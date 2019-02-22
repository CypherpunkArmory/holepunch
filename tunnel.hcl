# This declares a job named "docs". There can be exactly one
# job declaration per job file.

job "user-box" {
  datacenters = ["dc1"]

  type = "batch"

  parameterized {
    meta_required = ["ssh_password", "box_name"]
  }

  group "boxen" {
    count = 1
    task "box" {
      driver = "docker"

      config {
        image = "stephenprater/ubuntu-sshd:18.04"

        network_mode = "dumont_default"

        labels {
          "com.userland.dumont" = "${NOMAD_META_BOX_NAME}"
        }

        port_map {
          ssh = 22
        }
      }

      env {
        "SSH_PASSWORD" = "${NOMAD_META_SSH_PASSWORD}"
      }

      service {
        name = "box-${NOMAD_META_BOX_NAME}"
        tags = ["urlprefix-${NOMAD_META_BOX_NAME}:2222 proto=tcp"]
        port = "ssh"

        check {
          name = "alive"
          type = "tcp"
          interval = "10s"
          timeout = "2s"
          address_mode = "driver"
        }
      }

      resources {
        cpu    = 500 # MHz
        memory = 128 # MB

        network {
          mbits = 100

          # This requests a dynamic port named "http". This will
          # be something like "46283", but we refer to it via the
          # label "http".
          port "ssh" {
            static = 2222
          }

          port "forward" {
            static = 8080
          }
        }
      }
    }
  }
}
