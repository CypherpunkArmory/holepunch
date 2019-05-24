FROM rastasheep/ubuntu-sshd:18.04

RUN apt update

RUN sed -i 's/PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config

RUN echo "GatewayPorts yes" >> /etc/ssh/sshd_config && \
  echo "AllowTcpForwarding yes" >> /etc/ssh/sshd_config && \
  echo "AllowStreamLocalForwarding yes" >> /etc/ssh/sshd_config && \
  echo "PermitTunnel yes" >> /etc/ssh/sshd_config

# Allow SSH Access, but no shell for the punch user
RUN useradd -m -s /usr/sbin/nologin punch && \
  mkdir /home/punch/.ssh && \
  chown punch:punch /home/punch/.ssh && \
  chmod 0700 /home/punch/.ssh && \
  touch /home/punch/.ssh/authorized_keys && \
  chown punch:punch /home/punch/.ssh/authorized_keys && \
  chmod 0600 /home/punch/.ssh/authorized_keys && \
  echo "punch:*" | chpasswd -e

RUN apt -y install trickle

RUN echo '#!/bin/sh\n\
echo $SSH_KEY > /home/punch/.ssh/authorized_keys\n\
exec trickle -s -u $BANDWIDTH -d $BANDWIDTH /usr/sbin/sshd -D'\
>> /run_with_trickle.sh

RUN chmod +x /run_with_trickle.sh
ENTRYPOINT ["/run_with_trickle.sh"]
