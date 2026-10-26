# Arquitetura

Decisões já tomadas e pontos em aberto. Este documento vem antes do código: o que estiver em "Em aberto" precisa ser fechado antes de implementar a parte correspondente.

## Decisões

| Tema | Decisão |
|---|---|
| Distribuição | gratuita, OVA para VirtualBox e VMware |
| Conectividade | 100% offline |
| Base | Debian 12 + XFCE, build reproduzível com Packer + Ansible |
| SIEM | Wazuh (manager, indexer, dashboard) |
| IA | modelo local pequeno (3B a 4B, Q4) em CPU, carregado sob demanda; licença Apache 2.0 ou MIT |
| Nota | determinística, calculada pela semente do aluno; a IA nunca dá nota nem resposta |
| Identidade | preto e rosa, pantera Be Safe, "Powered By Mariana BS" |

## Componentes

### Ferramentas de mercado
Wazuh, Suricata, Wireshark/tshark, Zeek (sob demanda), Hayabusa, Chainsaw, Sigma, oletools, pdfid, exiftool, YARA, CyberChef offline.

Fora de propósito: Security Onion (pesado), TheHive e MISP (pesados, licenciamento mudou), Velociraptor (fica para a trilha "Promoção a N2").

### Console Be Safe (local)
Plantão, fila de tickets, nota e progressão, mais os serviços simulados da empresa:
- Be Safe Intel (reputação de IP, domínio e hash, com resultados ambíguos)
- caixa de phishing reportado (.eml reais)
- diretório de usuários (cargo, gestor, férias)
- inventário de ativos (criticidade, ambiente)
- relatórios de sandbox pré-gerados

### Motor de cenários
Injeta eventos no horário certo a partir da semente do aluno. Eventos Windows vêm de datasets EVTX públicos reescritos com a semente (não redistribuímos Windows).

### IA local
O conhecimento fica no cenário, não no modelo. Cada cenário traz a verdade do autor e uma escada de dicas; o modelo só conversa em cima disso:
- mentor N2 socrático (pedir ajuda custa pontos)
- revisor de ticket (checklist determinístico, modelo escreve o texto)
- pessoas simuladas: usuária, gestor, N2
- lab de prompt injection contra o copiloto do SOC

Modo turbo opcional: o modelo roda no host com GPU e a VM aponta para ele.

## Orçamento de RAM (VM)

| Componente | RAM |
|---|---|
| Debian + motor + console | 1 GB |
| Wazuh | 5 a 6 GB |
| Modelo 3B Q4 | 2,5 a 3 GB |
| Total | 10 a 12 GB (host com 16 GB) |

## Em aberto

- Público alvo: iniciantes, transição de carreira ou equipes de clientes
- Requisito de hardware: confirmar host com 16 GB ou criar perfil leve para 8 GB
- Escolha do modelo local: teste comparativo de 3 ou 4 candidatos em PT-BR
- Licença de cada dataset EVTX usado
- Certificado com verificação pública e o tratamento LGPD da captação
