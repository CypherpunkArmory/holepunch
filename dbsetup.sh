docker-compose exec db createdb -U postgres holepunch_development
docker-compose exec db createdb -U postgres holepunch_test
docker-compose run web flask db upgrade
