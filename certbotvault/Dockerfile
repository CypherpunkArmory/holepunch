FROM certbot/dns-route53
MAINTAINER cypherpunkarmory


# Install Vault client
RUN apk add curl
RUN apk add unzip
RUN curl https://releases.hashicorp.com/vault/1.1.1/vault_1.1.1_linux_amd64.zip -o vault.zip -s
RUN unzip vault.zip -d /usr/bin

COPY ./updatecerts.sh /usr/bin/updatecerts.sh

#Expects the following ENVs
# VAULT_ADDR="http://vault:8200"
# ADMINEMAIL="someone@somedomain.tech"
# DOMAIN="awsroute53updateabledoamin.com"
# CERTPATH="pathInVaultToStoreCert"
# CHAINPATH="pathInVaultToStoreCert"




CMD /usr/bin/updatecerts.sh

#certbot certonly \
#  -n --agree-tos --email andrew@userland.tech \
#  --dns-route53 \
#  -d orbtestenv.net

#  sudo certbot certonly --standalone -d example.com -d www.example.com