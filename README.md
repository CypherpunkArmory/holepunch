[![Codacy Badge](https://api.codacy.com/project/badge/Grade/62df8afdbbe64aeb92e32be409932f6e)](https://www.codacy.com/app/CypherpunkArmory/holepunch?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CypherpunkArmory/holepunch&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/62df8afdbbe64aeb92e32be409932f6e)](https://www.codacy.com/app/CypherpunkArmory/holepunch?utm_source=github.com&utm_medium=referral&utm_content=CypherpunkArmory/holepunch&utm_campaign=Badge_Coverage)
[![CircleCI](https://circleci.com/gh/CypherpunkArmory/holepunch.svg?style=svg)](https://circleci.com/gh/CypherpunkArmory/holepunch)
# Holepunch

This is the code used to run [api.holepunch.io](https://api.holepunch.io) <br/>
Visit [holepunch.io](https://holepunch.io) to find out more

# Setting Up

The holepunch nomad cluster requires a loopback alias in order to communicate
with containers running on the MacOS version of docker.

If you are running on a Mac, you can create this loopback alias at
172.16.123.1 by running `task setup_net`

If you are running locally, you will need to set the sshendpoint in your `.punch.toml`
file to this address as well.

This step is not necessary for running on Linux - but you will probably need
to change the `SEA_HOST` environment variable to your local IP.

1. You will need a dockerhub account to run the app.
2. Create a virtualenv (using pyenv) called "holepunch" based on Python 3.7.0
3. Install go-task via homebrew
4. Run `task setup_db setup_net`
5. Run the tests  `docker-compose run web pytest`

# Common Commands

## Run Flask Shell

`docker-compose run -e "FLASK_APP=app:create_app('development')" web python -m flask shell`

## Exec into a container

Most of the containers do not have bash so you'll need to use regular old sh.

`docker ps` -> note the _container id_
`docker exec -it <container_id> /bin/sh`


# Deploying Holepunch

Contributors and Holepunch Developers

1. Spin up a pushbutton environment using Grid.
2. Login to the Pushbutton VPN
3. Cd into the deploy directory and create a holepunch workspace with the _same
   name_ as your Pusbutton
4. Push a release to Docker Hub - for development it will deploy a tag with
   your branch name.  If you're on master, it will create a tag release.
5. task deploy WORKSPACE=<your workspace name>
  - If you are on master it will create new tags incremented by 0.0.1 and
    release those
  - You can specify a version using the VER variable.
