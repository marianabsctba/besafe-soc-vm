#!/bin/bash
# Limpeza final do build antes de exportar a OVA
set -euo pipefail

# o usuario do build nao pode ser apagado enquanto o Packer esta conectado nele:
# trava a senha agora e o servico de primeiro boot remove a conta
passwd -l "$BUILD_USUARIO"
rm -f /etc/sudoers.d/90-build
echo "$BUILD_USUARIO" > /var/lib/besafe/usuario-build

apt-get -y autoremove --purge
apt-get clean
rm -rf /tmp/* /var/tmp/* /var/log/*.gz /var/log/*.[0-9]
find /var/log -type f -exec truncate -s 0 {} \;
truncate -s 0 /etc/machine-id
rm -f /var/lib/dbus/machine-id
rm -f /etc/ssh/ssh_host_*
# o aluno nao precisa de SSH; so o build usava
systemctl disable ssh.service ssh.socket 2>/dev/null || true
ufw delete allow 22/tcp || true

# zera o espaco livre para a OVA comprimir melhor
dd if=/dev/zero of=/zero bs=1M status=none || true
rm -f /zero
sync
