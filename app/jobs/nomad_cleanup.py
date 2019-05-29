import nomad
from app import Q
from app.utils.dns import discover_service
from datetime import timedelta
import os

from app.models import Tunnel


@Q.job(func_or_queue="nomad", timeout=60000)
def cleanup_old_nomad_box(job_id):
    if os.getenv("FLASK_ENV") == "production":
        nomad_client = nomad.Nomad(discover_service("nomad").ip)
    else:
        nomad_client = nomad.Nomad(host=os.getenv("SEA_HOST", "0.0.0.0"))

    try:
        del_tunnel_nomad(nomad_client, job_id)
    except nomad.api.exceptions.BaseNomadException:
        cleanup_old_nomad_box.schedule(timedelta(hours=2), job_id, timeout=60000)
        raise nomad.api.exceptions.BaseNomadException


def del_tunnel_nomad(nomad_client, job_id):
    nomad_client.job.deregister_job(job_id)


@Q.job(func_or_queue="nomad", timeout=100000)
def check_all_boxes():
    if os.getenv("FLASK_ENV") == "production":
        nomad_client = nomad.Nomad(discover_service("nomad").ip)
    else:
        nomad_client = nomad.Nomad(host=os.getenv("SEA_HOST", "0.0.0.0"))
    deployments = nomad_client.job.get_deployments("ssh-client")

    for deployment in deployments:
        tunnel_exist = Tunnel.query.filter_by(job_id=deployment).first()
        if not tunnel_exist:
            cleanup_old_nomad_box(deployment)
