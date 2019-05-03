#!/bin/sh
# ________________________________________________________________________
# CLSchafer updatecert.sh
# Uses certbot and vault to request certupdates and store them
# 

# Grab route53 capable AWS key from vault

check_errs()
{
  # Function. Parameter 1 is the return code
  # Para. 2 is text to display on failure.
  if [ "${1}" -ne "0" ]; then
    echo "ERROR # ${1} : ${2}"
    # as a bonus, make our script exit with the right error code.
    exit ${1}
  fi
}

if [[ -z $AWS_ACCESS_KEY_ID ]]; then
  check_errs $? "no AWS ACCESS KEY set"
fi

if [[ -z $AWS_SECRET_ACCESS_KEY]]; then 
  check_errs $? "no AWS SECRET KEY SET"
fi

if [[-z $ADMINEMAIL ]]; then
  check_errs $? "no ADMIN EMAIL SET"
fi
if [[ -z $DOMAIN ]]; then
  check_errs $? "no domain name set"

# Make cert request
certbot certonly \
    -n --agree-tos --email $ADMINEMAIL \
    --dns-route53 \
    -d $DOMAIN
check_errs $? "certbot cert update errored"


# Store result in vault

if [[ -z $CERTPATH]]; then
  vault kv put $CERTPATH key=@/etc/letsencrypt/live/orbtestenv.net/privkey.pem
  check_errs $? "vault put errored for private key"
else
  echo "CERTPATH not set"
  exit (1) 
fi

if [[ -z $CHAINPATH]]; then
  vault kv put $CHAINPATH key=@/etc/letsencrypt/live/orbtestenv.net/fullchain.pem
  check_errs $? "vault put errored for chain"
else
  echo "CHAINPATH not set"
  exit (1) 
fi


