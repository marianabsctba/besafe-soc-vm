# Build da VM Be Safe SOC Lab: Ubuntu 24.04 + XFCE + Wazuh.
# Uso (na raiz do repositorio):
#   packer init packer
#   packer build -only=qemu.besafe packer           # Linux com KVM (recomendado; veja scripts/empacotar.sh)
#   packer build -only=virtualbox-iso.besafe packer  # VirtualBox em host SEM Hyper-V
#
# VirtualBox sobre Hyper-V (Windows com WSL ou Docker) trava durante a instalacao;
# nesse caso use o QEMU dentro do WSL.

packer {
  required_plugins {
    virtualbox = {
      source  = "github.com/hashicorp/virtualbox"
      version = ">= 1.1.1"
    }
    qemu = {
      source  = "github.com/hashicorp/qemu"
      version = ">= 1.1.0"
    }
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = ">= 1.1.0"
    }
  }
}

variable "versao" {
  type    = string
  default = "0.2.0"
}

variable "iso_url" {
  type    = string
  default = "https://releases.ubuntu.com/24.04/ubuntu-24.04.5-live-server-amd64.iso"
}

variable "iso_checksum" {
  type    = string
  default = "file:https://releases.ubuntu.com/24.04/SHA256SUMS"
}

variable "memoria_mb" {
  type    = number
  default = 12288
}

variable "cpus" {
  type    = number
  default = 4
}

# onde a VM e montada e a OVA sai (o disco cresce ate disco_mb durante o build)
variable "saida" {
  type    = string
  default = "output-besafe"
}

variable "disco_mb" {
  type    = number
  default = 61440
}

# usuario temporario do build; removido no fim (o aluno usa "analista")
variable "build_usuario" {
  type    = string
  default = "build"
}

variable "build_senha" {
  type      = string
  default   = "tmp-build-2026"
  sensitive = true
}

locals {
  # o instalador le o autoinstall do servidor HTTP do proprio Packer
  http_content = {
    "/user-data" = templatefile("${abspath(path.root)}/http/user-data.pkrtpl", {
      usuario = var.build_usuario
      senha   = var.build_senha
    })
    "/meta-data" = ""
  }
  boot_command = [
    "c<wait>",
    "linux /casper/vmlinuz --- autoinstall ds='nocloud;s=http://{{ .HTTPIP }}:{{ .HTTPPort }}/'<enter><wait>",
    "initrd /casper/initrd<enter><wait>",
    "boot<enter>"
  ]
  desligar = "echo '${var.build_senha}' | sudo -S shutdown -P now"
}

source "qemu" "besafe" {
  vm_name          = "besafe-soc-lab-${var.versao}.qcow2"
  iso_url          = var.iso_url
  iso_checksum     = var.iso_checksum
  accelerator      = "kvm"
  memory           = var.memoria_mb
  cpus             = var.cpus
  disk_size        = "${var.disco_mb}M"
  disk_interface   = "virtio"
  net_device       = "virtio-net"
  format           = "qcow2"
  disk_compression = true
  headless         = true
  output_directory = "${var.saida}/qemu-besafe-soc-lab-${var.versao}"

  http_content = local.http_content
  boot_wait    = "5s"
  boot_command = local.boot_command

  ssh_username           = var.build_usuario
  ssh_password           = var.build_senha
  ssh_timeout            = "90m"
  ssh_handshake_attempts = 500
  shutdown_command       = local.desligar
}

source "virtualbox-iso" "besafe" {
  vm_name              = "besafe-soc-lab-${var.versao}"
  guest_os_type        = "Ubuntu_64"
  iso_url              = var.iso_url
  iso_checksum         = var.iso_checksum
  memory               = var.memoria_mb
  cpus                 = var.cpus
  disk_size            = var.disco_mb
  hard_drive_interface = "sata"
  gfx_controller       = "vmsvga"
  gfx_vram_size        = 64
  # BIOS e nao EFI: o VMware ignora a marcacao de EFI que o VirtualBox grava na OVA
  firmware = "bios"
  headless = true
  # os pacotes de guest do Ubuntu ja vem pela role base; a ISO so incharia a imagem
  guest_additions_mode = "disable"
  format               = "ova"
  output_directory     = "${var.saida}/besafe-soc-lab-${var.versao}"

  http_content = local.http_content
  boot_wait    = "5s"
  boot_command = local.boot_command

  ssh_username = var.build_usuario
  ssh_password = var.build_senha
  ssh_timeout  = "90m"
  # o instalador do Ubuntu tambem abre SSH e recusa a senha; o Packer nao pode desistir
  ssh_handshake_attempts = 500
  shutdown_command       = local.desligar

  vboxmanage = [
    # disco primeiro: depois de instalar, a VM nao pode ligar pela ISO de novo
    ["modifyvm", "{{ .Name }}", "--boot1", "disk", "--boot2", "dvd", "--boot3", "none", "--boot4", "none"],
    ["modifyvm", "{{ .Name }}", "--audio-enabled", "off"],
    # VirtualBox sobre Hyper-V (comum com WSL/Docker) trava o kernel no teste de AVX do raid6;
    # sem AVX o boot passa e o custo para o lab e desprezivel
    ["setextradata", "{{ .Name }}", "VBoxInternal/CPUM/IsaExts/AVX", "0"],
    ["setextradata", "{{ .Name }}", "VBoxInternal/CPUM/IsaExts/AVX2", "0"],
    ["modifyvm", "{{ .Name }}", "--clipboard-mode", "bidirectional"],
  ]
  export_opts = [
    "--manifest",
    "--vsys", "0",
    "--product", "Be Safe SOC Lab",
    "--vendor", "Be Safe",
    "--version", var.versao,
    "--description", "VM de treinamento para analistas de SOC N1. Powered By Mariana BS",
  ]
}

build {
  sources = ["source.qemu.besafe", "source.virtualbox-iso.besafe"]

  # Ansible roda dentro da VM (ansible-local): o host nao precisa ter Ansible
  provisioner "shell" {
    execute_command = "echo '${var.build_senha}' | {{ .Vars }} sudo -S -E bash '{{ .Path }}'"
    inline = [
      # destino das artes precisa existir e ser do usuario do build (o upload e por scp)
      "install -d -o ${var.build_usuario} -g ${var.build_usuario} /tmp/besafe-branding /tmp/besafe-treinamento /tmp/besafe-console",
      "apt-get update",
      # o pacote "ansible" ja traz community.general e ansible.posix; ansible-galaxy aqui
      # rodaria como root e deixaria ~/.ansible do usuario do build sem permissao
      "DEBIAN_FRONTEND=noninteractive apt-get install -y ansible python3-pil rsync",
    ]
  }

  # o diretorio branding fica fora do playbook_dir; sobe separado antes do ansible
  provisioner "file" {
    # barra no fim: sobe o conteudo da pasta, nao a pasta dentro do destino
    source      = "${path.root}/../branding/"
    destination = "/tmp/besafe-branding"
    direction   = "upload"
  }

  provisioner "file" {
    source      = "${path.root}/../treinamento/"
    destination = "/tmp/besafe-treinamento"
    direction   = "upload"
  }

  provisioner "file" {
    source      = "${path.root}/../console/"
    destination = "/tmp/besafe-console"
    direction   = "upload"
  }

  provisioner "ansible-local" {
    playbook_file   = "${path.root}/../ansible/site.yml"
    playbook_dir    = "${path.root}/../ansible"
    extra_arguments = ["--extra-vars", "'besafe_versao=${var.versao} branding_src=/tmp/besafe-branding'"]
  }

  # limpeza: trava o usuario do build (o primeiro boot apaga), logs e espaco livre
  provisioner "shell" {
    execute_command  = "echo '${var.build_senha}' | {{ .Vars }} sudo -S -E bash '{{ .Path }}'"
    environment_vars = ["BUILD_USUARIO=${var.build_usuario}"]
    script           = "${path.root}/scripts/limpeza.sh"
  }
}
