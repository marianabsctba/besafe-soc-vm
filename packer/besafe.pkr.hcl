# Build da VM Be Safe SOC Lab: Ubuntu 24.04 + XFCE + Wazuh, exportada como OVA.
# Uso (na raiz do repositorio):
#   packer init packer
#   packer build packer

packer {
  required_plugins {
    virtualbox = {
      source  = "github.com/hashicorp/virtualbox"
      version = ">= 1.1.1"
    }
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = ">= 1.1.0"
    }
  }
}

variable "versao" {
  type    = string
  default = "0.1.0"
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
  default   = "besafe-build"
  sensitive = true
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
  firmware             = "efi"
  headless             = true
  format               = "ova"
  output_directory     = "output-besafe-${var.versao}"

  # o instalador le o autoinstall do servidor HTTP do proprio Packer
  http_content = {
    "/user-data" = templatefile("${abspath(path.root)}/http/user-data.pkrtpl", {
      usuario = var.build_usuario
      senha   = var.build_senha
    })
    "/meta-data" = ""
  }
  boot_wait = "5s"
  boot_command = [
    "c<wait>",
    "linux /casper/vmlinuz --- autoinstall ds='nocloud-net;s=http://{{ .HTTPIP }}:{{ .HTTPPort }}/'<enter><wait>",
    "initrd /casper/initrd<enter><wait>",
    "boot<enter>"
  ]

  ssh_username     = var.build_usuario
  ssh_password     = var.build_senha
  ssh_timeout      = "60m"
  shutdown_command = "echo '${var.build_senha}' | sudo -S shutdown -P now"

  vboxmanage = [
    ["modifyvm", "{{ .Name }}", "--nat-localhostreqs1", "on"],
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
  sources = ["source.virtualbox-iso.besafe"]

  # Ansible roda dentro da VM (ansible-local): o host nao precisa ter Ansible
  provisioner "shell" {
    execute_command = "echo '${var.build_senha}' | {{ .Vars }} sudo -S -E bash '{{ .Path }}'"
    inline = [
      "apt-get update",
      "DEBIAN_FRONTEND=noninteractive apt-get install -y ansible-core python3-pil rsync",
      "ansible-galaxy collection install ansible.posix community.general",
    ]
  }

  # o diretorio branding fica fora do playbook_dir; sobe separado antes do ansible
  provisioner "file" {
    source      = "${path.root}/../branding"
    destination = "/tmp/besafe-branding"
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
