job "holepunch" {
  datacenters = ["city"]

  type = "service"

  group "services" {
    vault {
      policies = ["holepunch-policy"]

      change_mode   = "restart"
    }

    count = 1
    task "web" {
      driver = "docker"

      config = {
        image = "cypherpunkarmory/holepunch-production:0.0.22"

        port_map {
          http = 5000
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
        destination = ".env.production"
        env         = true
        change_mode = "restart"
      }


      env {
        FLASK_ENV = "production"
        FLASK_SKIP_DOTENV = 1
      }

      service = {
        name = "web-holepunch-http"
        tags = [
          "urlprefix-api.holepunch.io/ proto=http"
        ]

        port = "http"

        check {
          name = "web-holepunch-http-up"
          port = "http"
          type = "http"
          path = "/health_check"
          interval = "10s"
          timeout = "2s"
        }
      }



      resources {
        cpu = 250
        memory = 500
        network {
          mbits = 1
          port "http" {}
        }
      }
    }
  }
}
