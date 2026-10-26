#!/bin/bash
# Limpeza final do build antes de exportar a OVA
set -euo pipefail

# o usuario do build nao pode ser apagado enquanto o Packer esta conectado nele:
# trava a senha agora e o servico de primeiro boot remove a conta e o sudoers dela.
# O sudo sem senha fica ate la porque o Packer ainda usa para desligar a VM.
passwd -l "$BUILD_USUARIO"
echo "$BUILD_USUARIO" > /var/lib/besafe/usuario-build

# rede generica: o instalador amarra a config ao nome da placa do VirtualBox (enp0s3),
# mas no VMware ela vira ens33/ens160 e a VM ficaria sem rede
rm -f /etc/netplan/*.yaml
cat > /etc/netplan/01-besafe.yaml <<'NETPLAN'
network:
  version: 2
  ethernets:
    cabeadas:
      match:
        name: "e*"
      dhcp4: true
      optional: true
NETPLAN
chmod 600 /etc/netplan/01-besafe.yaml

# cloud-init so servia para o autoinstall; em hardware novo ele rodaria de novo
# e atrasaria o boot procurando metadados de nuvem
touch /etc/cloud/cloud-init.disabled

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
