# Be Safe SOC Lab

VM gratuita da Be Safe para formar analistas de SOC nível 1. Em vez de uma lista de labs com flags, o aluno entra como N1 recém contratado de uma empresa fictícia e trabalha em plantões: alertas gerados ao vivo, muito ruído, tickets, passagem de turno e escalonamento.

![Desktop](docs/preview-desktop.png)

## Diferenciais

- **Telemetria única por aluno:** cada instalação tem uma semente própria (IPs, usuários, hashes, horários), então a resposta de um aluno não vale para outro.
- **Ruído realista:** a maior parte dos alertas é falso positivo. A nota mede julgamento de triagem, não caça a flag.
- **Ticket como entrega:** evidência, linha do tempo, severidade e escalonamento.
- **Contexto brasileiro e LGPD:** golpes de PIX, phishing gov.br, malware de boleto e cenários que terminam em "precisa comunicar à ANPD?".
- **IA local e offline:** mentor N2 socrático, pessoas simuladas (usuária, gestor, N2) e um lab de prompt injection contra o copiloto do SOC.

Detalhes em [docs/arquitetura.md](docs/arquitetura.md).

## Estrutura

```
branding/            identidade visual (pantera, paleta, fontes OFL)
  build_assets.py    gera papel de parede, login, GRUB, Plymouth e ícones em branding/out
  preview.py         gera as prévias em docs/
packer/              template da VM (Ubuntu 24.04, VirtualBox, saída OVA)
ansible/
  site.yml           playbook principal
  roles/base         usuário do aluno, XFCE, guest tools, firewall
  roles/branding     identidade no boot, login, XFCE, terminal e Wazuh
  roles/wazuh        Wazuh all-in-one enxuto para lab
  roles/primeiro_boot senhas únicas por cópia da VM
docs/                arquitetura e prévias
```

## Gerar as artes

```bash
pip install pillow
python branding/build_assets.py
python branding/preview.py
```

## Construir a VM

Requisitos no host: [Packer](https://developer.hashicorp.com/packer) e VirtualBox. O Ansible roda dentro da VM, então não precisa estar instalado no host.

```bash
packer init packer
packer build packer
```

A OVA sai em `output-besafe-<versao>/`. O build leva de 30 a 60 minutos.

## Usar a VM

- Requisito: host com 16 GB de RAM (a VM usa 12 GB) e 4 núcleos.
- Login: usuário `analista`, senha `analista`.
- A senha do Wazuh dashboard é única por cópia e fica em `~/.besafe/wazuh.txt`.

## Identidade visual

Preto `#050407` e rosa `#FC13B4`, com a pantera da Be Safe no boot (GRUB e Plymouth), na tela de login, no papel de parede, no terminal e no Wazuh dashboard.

![Boot](docs/preview-boot.png)

Fontes: [Orbitron](https://fonts.google.com/specimen/Orbitron) e [Rajdhani](https://fonts.google.com/specimen/Rajdhani), ambas sob SIL Open Font License (licenças em `branding/fonts`).

---

Powered By Mariana BS
