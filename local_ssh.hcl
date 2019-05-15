job "ssh-client" {
  datacenters = ["city"]

  type = "batch"

  parameterized {
    meta_required = ["ssh_key", "box_name", "base_url", "bandwidth"]
  }

  group "holepunch" {
    count = 1
    task "sshd" {
      driver = "docker"

      config {
        image = "cypherpunkarmory/sshd:develop"
        network_mode = "holepunch_default"

        labels {
          "io.holepunch.sshd" = "${NOMAD_META_BOX_NAME}"
        }

        port_map {
          ssh = 22
          http = 3000
          https = 3001
        }
      }

      env {
        "SSH_KEY" = "${NOMAD_META_SSH_KEY}"
        "BANDWIDTH" = "${NOMAD_META_BANDWIDTH}"
      }

      service {
        name = "box-${NOMAD_META_BOX_NAME}-ssh"

        port = "ssh"

        check {
          name = "ssh-${NOMAD_META_BOX_NAME}-up"
          address_mode = "driver"
          port = "ssh"
          type = "tcp"
          interval = "10s"
          timeout = "2s"
        }
      }

      service {
        name = "box-${NOMAD_META_BOX_NAME}-http"

        tags = [
          "urlprefix-${NOMAD_META_BOX_NAME}.${NOMAD_META_BASE_URL}/ proto=http",
        ]

        port = "http"

        check {
          name = "http-$${NOMAD_META_BOX_NAME}-up"
          address_mode = "driver"
          port = "http"
          type = "tcp"
          interval = "10s"
          timeout = "2s"
        }
      }

      service {
        name = "box-${NOMAD_META_BOX_NAME}-https"

        tags = [
          "urlprefix-${NOMAD_META_BOX_NAME}.${NOMAD_META_BASE_URL}/ proto=tcp+sni"
        ]

        port = "https"

        check {
          name = "https-${NOMAD_META_BOX_NAME}-up"
          address_mode = "driver"
          port = "https"
          type = "tcp"
          interval = "10s"
          timeout = "2s"
        }
      }

      resources {
        cpu    = 100 # MHz
        memory = 2000 # MB

        network {
          mbits = 1

          # This requests a dynamic port named "http". This will
          # be something like "46283", but we refer to it via the
          # label "http".
          port "ssh" {}
          port "http" {}
          port "https" {}
        }
      }
    }
  }
}
