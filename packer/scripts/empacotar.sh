#!/bin/bash
# Converte o disco do build QEMU numa VM do VMware (.vmx + .vmdk).
# A OVA final sai do ovftool da VMware a partir desse .vmx (abre no VMware e no VirtualBox).
#
# Uso: empacotar.sh <disco.qcow2> <pasta-de-saida> <versao> [memoria_mb] [cpus]
set -euo pipefail

DISCO=$1
SAIDA=$2
VERSAO=$3
MEMORIA=${4:-12288}
CPUS=${5:-4}
NOME="besafe-soc-lab-${VERSAO}"

mkdir -p "$SAIDA"
# monolithicSparse: formato que o VMware Workstation/Player abre direto e o ovftool le
qemu-img convert -p -O vmdk -o adapter_type=lsilogic,subformat=monolithicSparse \
  "$DISCO" "$SAIDA/$NOME.vmdk"

cat > "$SAIDA/$NOME.vmx" <<VMX
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "19"
displayName = "Be Safe SOC Lab $VERSAO"
annotation = "VM de treinamento para analistas de SOC N1.|0AUsuario: analista / Senha: analista|0APowered By Mariana BS"
guestOS = "ubuntu-64"
firmware = "bios"
memsize = "$MEMORIA"
numvcpus = "$CPUS"
cpuid.coresPerSocket = "$CPUS"
sata0.present = "TRUE"
sata0:0.present = "TRUE"
sata0:0.fileName = "$NOME.vmdk"
ethernet0.present = "TRUE"
ethernet0.connectionType = "nat"
ethernet0.virtualDev = "e1000e"
ethernet0.addressType = "generated"
usb.present = "TRUE"
ehci.present = "TRUE"
sound.present = "FALSE"
svga.vramSize = "134217728"
mks.enable3d = "FALSE"
tools.syncTime = "TRUE"
VMX

echo "VM do VMware em $SAIDA/$NOME.vmx"
