docker-compose exec db createdb -U postgres holepunch_development
docker-compose exec db createdb -U postgres holepunch_test
docker-compose exec web flask db upgrade
docker-compose run nomad job run ssh.hcl
