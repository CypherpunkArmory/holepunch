job "holepunch" {
  datacenters = ["city"]

  vault {
    policies = ["holepunch-policy"]

    change_mode   = "restart"
  }

  type = "service"

  group "workers"{
    count = 1

    task "job-dashboard"{
      driver = "docker"

      config = {
        image = "cypherpunkarmory/holepunch-production:0.0.28"
        entrypoint = ["/bin/bash" , "-l", "-c"]
        command = "rq-dashboard -b 0.0.0.0"
        port_map {
          http = 9181
        }
        labels {
          usage = "job-dashboard"
        }
      }

      env {
        RQ_REDIS_URL = "redis://holepunch-redis.ldw3vp.ng.0001.usw2.cache.amazonaws.com:6379"
        RQ_DASHBOARD_REDIS_URL = "redis://holepunch-redis.ldw3vp.ng.0001.usw2.cache.amazonaws.com:6379"
      }

      service = {
        name = "jobs-dash"

        port = "http"

        check {
          name = "jobs-dash-up"
          port = "http"
          type = "http"
          path = "/"
          interval = "120s"
          timeout = "2s"
        }
      }

      resources {
        cpu = 100
        memory = 100
        network {
          mbits = 1
          port "http" {
            static = 9181
          }
        }
      }
    }

    task "jobs"{
      driver = "docker"

      config = {
        image = "cypherpunkarmory/holepunch-production:0.0.28"
        entrypoint = ["/bin/bash" , "-l", "-c"]
        command = "python -m flask rq worker"
        labels {
          usage = "jobs"
        }
      }

      template {
        data = <<EOH
# Empty lines are also ignored
{{with secret "secret/holepunch"}}
DATABASE_URL={{.Data.DATABASE_URL}}
JWT_SECRET_KEY={{.Data.JWT_SECRET_KEY}}
MAIL_PASSWORD={{.Data.MAIL_PASSWORD}}
MAIL_USERNAME={{.Data.MAIL_USERNAME}}
ROLLBAR_TOKEN={{.Data.ROLLBAR_TOKEN}}
{{end}}
EOH
        destination = ".secrets.production"
        env         = true
        change_mode = "restart"
      }

      env {
        FLASK_APP = "app:create_app('production')"
        FLASK_ENV = "production"
        CONSUL_HOST = "172.17.0.1"
        CLUSTER_HOST = "172.17.0.1"
        RQ_REDIS_URL = "redis://holepunch-redis.ldw3vp.ng.0001.usw2.cache.amazonaws.com:6379"
        SEA_HOST = "172.17.0.1"
        DD_AGENT_HOST = "172.17.0.1"
      }

      resources {
        cpu = 250
        memory = 250
        network {
          mbits = 1
        }
      }
    }
  }

  group "services" {
    count = 3

    task "web" {
      driver = "docker"
      config = {
        image = "cypherpunkarmory/holepunch-production:0.0.28"

        port_map {
          https = 5000
        }
        labels {
          usage = "web"
        }

        logging {
          type = "journald"
        }
      }

      template {
        data = <<EOH
# Empty lines are also ignored
{{with secret "secret/holepunch"}}
DATABASE_URL={{.Data.DATABASE_URL}}
JWT_SECRET_KEY={{.Data.JWT_SECRET_KEY}}
MAIL_PASSWORD={{.Data.MAIL_PASSWORD}}
MAIL_USERNAME={{.Data.MAIL_USERNAME}}
ROLLBAR_TOKEN={{.Data.ROLLBAR_TOKEN}}
{{end}}
EOH
        destination = "/secrets/production"
        env         = true
        change_mode = "restart"
      }

      template {
        data = <<EOH
{{ with secret "secret/fabio/certs/api.holepunch.io" }}
{{ .Data.cert }}
{{ end }}
EOH
        destination = "/secrets/cert.pem"
        change_mode = "restart"
      }

      template {
        data = <<EOH
{{ with secret "secret/fabio/certs/api.holepunch.io" }}
{{ .Data.key }}
{{ end }}
EOH
        destination = "/secrets/key.pem"
        change_mode = "restart"
      }

      env {
        FLASK_ENV = "production"
        FLASK_SKIP_DOTENV = 1
        RQ_REDIS_URL = "redis://holepunch-redis.ldw3vp.ng.0001.usw2.cache.amazonaws.com:6379"
      }

      service = {
        name = "web-holepunch-https"
        tags = [
          "urlprefix-api.holepunch.io/ proto=tcp+sni tlskipverify=true"
        ]

        port = "https"

        check {
          name = "web-holepunch-https-up"
          protocol = "https"
          port = "https"
          type = "http"
          path = "/health_check"
          interval = "10s"
          timeout = "2s"
          tls_skip_verify = true
        }
      }

      resources {
        cpu = 250
        memory = 250
        network {
          mbits = 1
          port "https" {}
        }
      }
    }
  }
}
