# Glossário

<p class="sub">Os termos que você vai ouvir no primeiro dia de SOC, em ordem alfabética.</p>

| Termo | Significado |
|---|---|
| **Alerta** | evento que uma regra considerou suspeito e colocou na fila do SOC |
| **Ativo** | qualquer coisa que a empresa quer proteger: máquina, servidor, conta, sistema, dado |
| **Beacon** | conexão periódica de um malware para o seu servidor de comando ("ligar para casa") |
| **C2 (Command and Control)** | infraestrutura que o atacante usa para mandar ordens a máquinas comprometidas |
| **Criticidade** | o quão importante é um ativo para o negócio |
| **CVE** | identificador público de uma vulnerabilidade conhecida, como `CVE-2020-1472` |
| **DPO / Encarregado** | pessoa responsável pela proteção de dados pessoais na empresa (LGPD); recebe os casos com dados pessoais |
| **EDR** | ferramenta instalada nas máquinas que registra e bloqueia comportamento malicioso |
| **Escalar** | passar o caso ao nível seguinte (N2), já documentado |
| **Evento** | qualquer registro de algo que aconteceu num sistema |
| **EVTX** | formato dos arquivos de log de eventos do Windows |
| **Exfiltração** | retirada de dados da empresa pelo atacante |
| **Falso negativo** | ataque real que nenhuma regra detectou |
| **Falso positivo** | alerta disparado por algo que não era malicioso |
| **FIM** | monitoramento de integridade de arquivos: avisa quando arquivos importantes mudam |
| **Hash** | "impressão digital" de um arquivo (MD5, SHA-1, SHA-256): qualquer alteração muda o hash |
| **IDS / IPS** | sistema que detecta (IDS) ou detecta e bloqueia (IPS) ataques no tráfego de rede |
| **IOC** | indicador de comprometimento: IP, domínio, hash, nome de arquivo ligados a um ataque |
| **Lateral (movimento)** | o atacante pulando de uma máquina para outra dentro da rede |
| **LSASS** | processo do Windows que guarda credenciais na memória; alvo de roubo de senhas |
| **MITRE ATT&CK** | catálogo público de táticas e técnicas de atacantes |
| **Persistência** | o que o atacante faz para continuar no sistema depois de um reboot |
| **Phishing** | golpe por mensagem (e-mail, SMS, WhatsApp) para roubar dados ou instalar malware |
| **Playbook** | procedimento escrito: o que fazer, passo a passo, diante de um tipo de alerta |
| **Prioridade** | ordem de atendimento: severidade combinada com criticidade do ativo |
| **Ransomware** | malware que criptografa arquivos e pede resgate |
| **Severidade** | o quão grave é o comportamento detectado |
| **SIEM** | sistema que centraliza logs, aplica regras e gera alertas (aqui: Wazuh) |
| **SID** | identificador único de uma conta no Windows |
| **SLA** | prazo combinado para atender ou resolver um tipo de caso |
| **SNI** | campo do início de uma conexão HTTPS que mostra o nome do site |
| **SOC** | centro de operações de segurança: a equipe que monitora e responde |
| **Sysmon** | ferramenta da Microsoft que registra em detalhe a atividade do Windows |
| **TTP** | táticas, técnicas e procedimentos: o "jeito de agir" de um atacante |
| **Triagem** | primeira análise de um alerta: é real? é urgente? quem precisa saber? |
| **Verdadeiro positivo** | alerta que de fato era malicioso |
| **Verdadeiro positivo benigno** | alerta correto sobre algo que era autorizado |
| **YARA** | linguagem para descrever padrões que identificam arquivos maliciosos |
