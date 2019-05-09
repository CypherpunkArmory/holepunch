FROM certbot/dns-route53
MAINTAINER cypherpunkarmory


# Install Vault client
RUN apk add curl
RUN apk add unzip
RUN curl https://releases.hashicorp.com/vault/1.1.1/vault_1.1.1_linux_amd64.zip -o vault.zip -s
RUN unzip vault.zip -d /usr/bin

COPY ./updatecerts.sh /usr/bin/updatecerts.sh

# environment variables
# AWS_ACCESS_KEY_ID  (issued by vault for aws route 53 access)
# AWS_SECRET_ACCESS_KEY  (issued by vault for aws route 53 access)
# ADMINEMAIL Defined in Nomad job
# DOMAIN Defined in Nomad job
# VAULT_ADDR  Defined in Nomad job
# VAULT_TOKEN  (passed in by Nomad)


CMD /usr/bin/updatecerts.sh
