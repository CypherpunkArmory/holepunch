job "web" {
  datacenters = ["city"]

  type = "service"

  group "holepunch" {
    count = 1
    task "flask" {
      driver = "docker"

      config = {
        image = "cypherpunkarmory/holepunch-production:0.0.18"

        port_map {
          http = 5000
        }
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
