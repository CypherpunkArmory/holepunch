import nomad
import consul
from app import Q, redis_client
from app.utils.dns import discover_service
from datetime import timedelta
import os

from app.models import Tunnel


@Q.job(func_or_queue="nomad", timeout=60000)
def cleanup_old_nomad_box(job_id):
    nomad_client = nomad.Nomad(discover_service("nomad").ip)

    try:
        del_tunnel_nomad(nomad_client, job_id)
    except nomad.api.exceptions.BaseNomadException:
        cleanup_old_nomad_box.schedule(timedelta(hours=2), job_id, timeout=60000)
        raise nomad.api.exceptions.BaseNomadException


def del_tunnel_nomad(nomad_client, job_id):
    nomad_client.job.deregister_job(job_id, purge=True)


@Q.job(func_or_queue="nomad", timeout=100000)
def check_all_boxes():
    nomad_client = nomad.Nomad(discover_service("nomad").ip)
    deployments = nomad_client.job.get_deployments("ssh-client")

    for deployment in deployments:
        tunnel_exist = Tunnel.query.filter_by(job_id=deployment).first()
        if not tunnel_exist:
            cleanup_old_nomad_box(deployment)


@Q.job(func_or_queue="nomad", timeout=100000)
def find_unused_boxes():
    consul_client = consul.Consul(host=discover_service("consul").ip)
    services = consul_client.catalog.services()
    user_services = {k: v for (k, v) in services[1].items() if "ssh-" in k}
    for service in user_services:
        health_checks = consul_client.health.service(service)[1][0]["Checks"]
        for health_check in health_checks:
            if health_check["Name"] == "Serf Health Status":
                continue

            if health_check["Status"] == "passing":
                continue

            subdomain = health_check["ServiceName"].split("-")[1]
            if subdomain == "TCP":
                subdomain = subdomain + "-" + health_check["ServiceName"].split("-")[2]

            exists = redis_client.sismember("unhealthy_tunnels", subdomain)
            if exists:
                redis_client.srem("unhealthy_tunnels", subdomain)
                cleanup_old_nomad_box("ssh-client-" + subdomain)
            else:
                redis_client.sadd("unhealthy_tunnels", subdomain)
