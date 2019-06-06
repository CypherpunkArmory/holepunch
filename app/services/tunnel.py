from typing import Tuple, cast

import nomad
from dpath.util import values

from app import db
from app.jobs.nomad_cleanup import cleanup_old_nomad_box
from app.models import Subdomain, Tunnel, User
from app.services.subdomain import SubdomainCreationService
from app.utils.errors import (
    AccessDenied,
    TunnelError,
    SubdomainInUse,
    TunnelLimitReached,
)
from app.utils.json import dig

from app.utils.dns import discover_service

from typing import Optional

from flask import current_app


class TunnelCreationService:
    def __init__(
        self,
        current_user: User,
        subdomain_id: Optional[int],
        port_type: list,
        ssh_key: str,
    ):

        self.port_type = port_type
        self.ssh_key = ssh_key
        self.current_user = current_user

        if subdomain_id:
            self.subdomain = Subdomain.query.get(subdomain_id)
        else:
            self.subdomain = SubdomainCreationService(
                self.current_user
            ).get_unused_subdomain()

        # We need to do this each time so each if a nomad service goes down
        # it doesnt affect web api
        self.nomad_client = nomad.Nomad(discover_service("nomad").ip)

    def create(self) -> Tunnel:
        self.check_subdomain_permissions()
        job_id = None
        if self.over_tunnel_limit():
            raise TunnelLimitReached("Maximum number of opened tunnels reached")
        try:
            job_id, result = self.create_tunnel_nomad()
            ssh_port, ip_address = self.get_tunnel_details(result, job_id)
        except TunnelError:
            # if nomad fails to even start the job then there will be no job_id
            if job_id:
                cleanup_old_nomad_box.queue(job_id, timeout=60000)
            raise TunnelError("Failed to create tunnel")
        except nomad.api.exceptions.BaseNomadException:
            raise TunnelError("Failed to create tunnel")

        self.subdomain.in_use = True

        tunnel = Tunnel(
            subdomain_id=self.subdomain.id,
            port=self.port_type,
            job_id=job_id,
            ssh_port=ssh_port,
            ip_address=ip_address,
        )

        tunnel.subdomain = self.subdomain

        db.session.add(tunnel)
        db.session.add(self.subdomain)
        db.session.flush()

        return tunnel

    def check_subdomain_permissions(self) -> None:
        if self.subdomain.user != self.current_user:
            raise AccessDenied("You do not own this subdomain")
        elif self.subdomain.in_use:
            raise SubdomainInUse("Subdomain is in use")
        elif self.subdomain.user == self.current_user:
            pass

    def over_tunnel_limit(self) -> bool:
        num_tunnels = self.current_user.tunnels.count()
        if num_tunnels >= self.current_user.limits().tunnel_count:
            return True
        return False

    def create_tunnel_nomad(self) -> Tuple[str, dict]:
        """Create a tunnel by scheduling an SSH container into the Nomad cluster"""

        meta = {
            "ssh_key": self.ssh_key,
            "box_name": self.subdomain.name,
            "base_url": current_app.config["BASE_SERVICE_URL"],
            "bandwidth": str(self.current_user.limits().bandwidth),
        }

        result = self.nomad_client.job.dispatch_job("ssh-client", meta=meta)
        return (cast(str, result["DispatchedJobID"]), result)

    def get_tunnel_details(self, result: dict, job_id: str) -> Tuple[str, str]:
        """Get details of ssh container"""
        # FIXME: nasty blocking loops should be asynced or something
        # Add error handling to this
        status = None
        trys = 0
        while status != "running":
            trys += 1
            status = self.nomad_client.job[result["DispatchedJobID"]]["Status"]
            if trys > 1000:
                raise TunnelError(detail="The tunnel failed to start.")

        job_info = self.nomad_client.job.get_allocations(job_id)

        allocation_info = self.nomad_client.allocation.get_allocation(
            dig(job_info, "0/ID")
        )

        allocation_node = values(allocation_info, "NodeID")
        nodes = self.nomad_client.nodes.get_nodes()

        ip_address = next(x["Address"] for x in nodes if x["ID"] in allocation_node)
        allocated_ports = values(allocation_info, "Resources/Networks/0/DynamicPorts/*")
        ssh_port = next(x for x in allocated_ports if x["Label"] == "ssh")["Value"]

        if current_app.config["ENV"] == "development":
            ip_address = current_app.config["SEA_HOST"]

        return (ssh_port, ip_address)


class TunnelDeletionService:
    def __init__(self, current_user: User, tunnel: Optional[Tunnel], job_id=None):
        self.current_user = current_user
        self.tunnel = tunnel
        if job_id:
            self.job_id = job_id
        if tunnel:
            self.subdomain = tunnel.subdomain
            self.job_id = tunnel.job_id

        self.nomad_client = nomad.Nomad(discover_service("nomad").ip)

    def delete(self):
        if self.subdomain.reserved:
            self.subdomain.in_use = False
            db.session.add(self.subdomain)
            db.session.delete(self.tunnel)
            db.session.flush()
        else:
            db.session.delete(self.tunnel)
            db.session.delete(self.subdomain)
            db.session.flush()
        cleanup_old_nomad_box.queue(self.job_id, timeout=60000)
