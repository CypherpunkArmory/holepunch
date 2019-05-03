#!/bin/bash

set -e

if [ -z "${SSH_KEY}" ]; then
        echo "=> Please pass your public key in the SSH_KEY env variable"
        exit 1
fi

echo "punch:*" | chpasswd -e
echo $SSH_KEY > /home/punch/.ssh/authorized_keys
exec trickle -s -u $BANDWIDTH -d $BANDWIDTH /usr/sbin/sshd -D
