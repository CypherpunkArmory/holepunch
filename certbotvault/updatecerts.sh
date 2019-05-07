#!/bin/sh
# ________________________________________________________________________
# CLSchafer updatecert.sh
# Uses certbot and vault to request certupdates and store them
# 

# Grab route53 capable AWS key from vault

check_errs() {
  # Function. Parameter 1 is the return code
  # Para. 2 is text to display on failure.
  if [ "${1}" -ne "0" ]; then
    echo "ERROR # ${1} : ${2}"
    # as a bonus, make our script exit with the right error code.
    exit ${1}
  fi
}

if [ "${AWS_ACCESS_KEY_ID+1}" ]; then
  check_errs $? "no AWS ACCESS KEY set"
fi

if [ "${AWS_SECRET_ACCESS_KEY+1}" ]; then 
  check_errs $? "no AWS SECRET KEY SET"
fi

if [ "${ADMINEMAIL+1}" ]; then
  check_errs $? "no ADMIN EMAIL SET"
fi
if [ "${DOMAIN+1}" ]; then
  check_errs $? "no domain name set"
fi

# Make cert request uses AWS key passed in from vault during nomad job start.
certbot certonly \
    -n --agree-tos --email "${ADMINEMAIL}" \
    --dns-route53 \
    -d "${DOMAIN}"
check_errs $? "certbot cert update errored"


# Check vault envs are set....

# Store result in vault

if [ "${CERTPATH+1}" ]; then
  vault kv put ${CERTPATH} key=@/etc/letsencrypt/live/orbtestenv.net/privkey.pem
  check_errs $? "vault put errored for private key"
else
  echo "CERTPATH not set"
  exit 1 
fi

if [ "${CHAINPATH+1}" ]; then
  vault kv put ${CHAINPATH} key=@/etc/letsencrypt/live/orbtestenv.net/fullchain.pem
  check_errs $? "vault put errored for chain"
else
  echo "CHAINPATH not set"
  exit 1 
fi


