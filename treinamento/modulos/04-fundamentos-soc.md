<!-- descricao: Como um SOC funciona e como um N1 pensa: triagem, falso positivo, severidade e escalonamento. -->
# Módulo 4: Fundamentos do SOC e do analista N1

<p class="sub">Ferramenta se aprende em uma semana. Julgamento se constrói por anos. Este módulo é sobre julgamento.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - o que é um SOC, como ele se organiza e o papel de cada nível;
    - o ciclo de vida de um alerta, do disparo ao encerramento;
    - um método de triagem que funciona para qualquer alerta;
    - a diferença entre verdadeiro positivo, falso positivo e os casos no meio do caminho;
    - severidade, criticidade do ativo e prioridade;
    - quando e como escalar;
    - o básico do MITRE ATT&CK para dar nome ao que o atacante está fazendo.

## 1. O que é um SOC

**SOC** (*Security Operations Center*, centro de operações de segurança) é a equipe que **monitora, detecta e responde** a ameaças contra uma organização, normalmente 24 horas por dia. A matéria-prima do SOC são **eventos** (tudo que os sistemas registram) e **alertas** (eventos que uma regra considerou suspeitos).

Uma empresa média gera **milhões de eventos por dia** e **centenas ou milhares de alertas**. A imensa maioria dos alertas não é ataque. O trabalho do SOC é encontrar, no meio desse volume, os poucos que importam, e agir rápido.

### Os níveis

| Nível | Papel | Pergunta que responde |
|---|---|---|
| **N1** (Tier 1) | monitora a fila, faz a **triagem**, documenta, resolve o simples e **escala** o resto | "Isso é real? É urgente? Quem precisa saber?" |
| **N2** (Tier 2) | investiga a fundo, correlaciona fontes, conduz a resposta | "O que exatamente aconteceu, até onde foi?" |
| **N3** (Tier 3) | caça ameaças, faz análise forense e de malware, cria detecções | "O que ainda não estamos vendo?" |
| **Engenharia de detecção** | cria e ajusta as regras que geram os alertas | "Por que esse alerta dispara tanto à toa?" |

O N1 é a **porta de entrada**. Se o N1 descarta um ataque real como "ruído", ninguém mais vê. Se o N1 escala tudo, o N2 se afoga. O valor do N1 está exatamente no meio: **filtrar bem e documentar bem**.

## 2. Ciclo de vida de um alerta

```
 Regra dispara ──▶ Alerta na fila ──▶ Triagem (N1) ──┬──▶ Falso positivo: documenta e fecha
                                                    ├──▶ Real e simples: resolve pelo playbook, documenta e fecha
                                                    └──▶ Real ou incerto: escala ao N2 com o caso documentado
```

Repare que **todos os caminhos passam por documentar**. Um alerta fechado sem explicação é um alerta que vai voltar e ninguém vai lembrar por que foi descartado.

## 3. O método de triagem: seis perguntas

Diante de qualquer alerta, antes de qualquer ferramenta, responda:

1. **O quê?** O que a regra diz que aconteceu? Leia o nome, a descrição e o evento original. Não confie só no título.
2. **Onde?** Em qual máquina? Ela é uma estação de usuário, um servidor de arquivos, o controlador de domínio, o servidor do site? (Isso é a **criticidade do ativo**.)
3. **Quem?** Qual conta? É uma pessoa, um serviço, um administrador? Ela costuma fazer isso?
4. **Quando?** Em horário comercial ou às 3h de domingo? Coincide com alguma manutenção planejada?
5. **De onde e para onde?** IPs internos ou externos? Destino conhecido ou novo?
6. **É normal aqui?** Essa é a pergunta mais importante, e a mais difícil. O mesmo evento pode ser rotina num lugar e ataque em outro. Você responde comparando com o histórico: essa máquina, essa conta, esse horário, isso já aconteceu antes?

!!! erro "Erro comum de N1"
    Fechar um alerta porque "esse sempre dá falso positivo". Atacantes **contam** com isso: se uma regra é famosa por gerar ruído, é ali que eles se escondem. Cada alerta merece as seis perguntas, mesmo que rápidas.

## 4. Positivos, negativos e o meio do caminho

| Termo | Significado | Exemplo |
|---|---|---|
| **Verdadeiro positivo (VP)** | a regra disparou e era mesmo malicioso | alerta de Mimikatz e era Mimikatz |
| **Falso positivo (FP)** | a regra disparou, mas não era malicioso | alerta de "força bruta" que era um serviço com a senha antiga configurada, tentando de novo |
| **Verdadeiro positivo benigno** | a regra acertou o comportamento, mas era autorizado | o time de segurança rodando um scanner de vulnerabilidades combinado |
| **Falso negativo (FN)** | era ataque e **nenhuma** regra disparou | o pior caso: você só descobre depois, se descobrir |

O falso negativo não aparece na fila, por definição. Por isso a **qualidade das regras** e a **atenção do analista** a detalhes estranhos (mesmo sem alerta) importam tanto.

!!! atencao "Falso positivo também é trabalho útil"
    Quando você identifica um falso positivo recorrente, anote **por que** é falso e sugira o ajuste à engenharia de detecção. Um N1 que reduz o ruído da fila melhora o SOC inteiro. Só não ajuste a regra por conta própria nem crie exceções amplas ("ignorar tudo do servidor X"): exceção mal feita é um ponto cego permanente.

## 5. Severidade, criticidade e prioridade

São três coisas diferentes:

- **Severidade** é o quão grave é o *comportamento* (definida pela regra). "Execução de ferramenta de roubo de credenciais" é alta; "falha de login isolada" é baixa.
- **Criticidade do ativo** é o quão importante é *a máquina ou conta* envolvida. O controlador de domínio, o servidor do ERP e a conta do diretor financeiro são críticos; um notebook de visitante, nem tanto.
- **Prioridade** é a combinação das duas, e é ela que diz **o que você olha primeiro**.

| | Ativo pouco crítico | Ativo crítico |
|---|---|---|
| **Severidade baixa** | prioridade baixa | média |
| **Severidade alta** | alta | **crítica: largue o resto** |

## 6. Quando escalar

Cada SOC tem os seus critérios, escritos num **playbook** ou procedimento. Na Pantera Logística, o N1 **escala imediatamente** quando:

- há sinal de **execução de código** malicioso confirmado ou provável;
- há indício de **roubo de credenciais** ou uso de conta privilegiada fora do normal;
- há **movimento lateral** (uma máquina atacando outra internamente);
- há sinal de **dados saindo** da empresa em volume ou para destino estranho;
- há **apagamento de logs** ou desativação de antivírus;
- o caso envolve **dados pessoais** de clientes ou colaboradores (o módulo 11 explica por quê);
- **você não tem certeza**. Na dúvida, escale: é mais barato o N2 olhar um falso positivo do que a empresa perder um ataque.

Escalar **não é passar o problema adiante**. É entregar o caso **pronto para o próximo agir**: o que você viu, onde, quando, o que já verificou e o que acha que é. O módulo 10 ensina a escrever isso.

## 7. MITRE ATT&CK: um vocabulário comum

O **MITRE ATT&CK** é uma base de conhecimento pública que cataloga **o que atacantes fazem**, observado em ataques reais. Ele se organiza em:

- **Táticas**: o *objetivo* do atacante naquela etapa (o "por quê");
- **Técnicas**: *como* ele atinge o objetivo (o "como"), cada uma com um código, como `T1003`.

As táticas, na ordem em que costumam aparecer num ataque:

| Tática | Objetivo do atacante | Exemplo que você já viu |
|---|---|---|
| Reconnaissance | conhecer o alvo | (fora da empresa) |
| Initial Access | entrar | e-mail de phishing |
| Execution | rodar código | macro abrindo PowerShell |
| Persistence | continuar lá depois de um reboot | serviço ou conta nova |
| Privilege Escalation | ganhar mais poder | Guest no grupo Administrators (módulo 3) |
| Defense Evasion | não ser visto | apagar o log (1102) |
| Credential Access | roubar senhas | Mimikatz no LSASS (`T1003.001`) |
| Discovery | entender a rede por dentro | listar usuários, port scan |
| Lateral Movement | pular para outras máquinas | WMI, PsExec (módulo 3) |
| Collection | juntar o que quer levar | compactar pastas do financeiro |
| Command and Control | falar com o atacante | conexão para a porta 4444 (módulo 3) |
| Exfiltration | levar os dados para fora | upload para nuvem desconhecida |
| Impact | causar dano | ransomware, apagar backups |

Isso explica as pastas do acervo EVTX-ATTACK-SAMPLES: cada uma é uma tática. E o Wazuh marca muitos alertas com a técnica do ATT&CK correspondente, como você vai ver no próximo módulo.

!!! atacante "Como o atacante pensa"
    Um ataque é uma **sequência**. Raramente um único alerta conta a história inteira: o phishing gera um alerta pequeno, a execução gera outro, o roubo de credenciais um terceiro. O N1 que pensa em sequência pergunta: *"se isto é a etapa de Execution, o que eu deveria procurar logo antes (como ele entrou?) e logo depois (o que ele fez em seguida?)"*. É assim que um alerta de severidade média vira a descoberta de um incidente.

## 8. Postura profissional

- **Sigilo**: você vai ver e-mails, nomes, IPs, às vezes dados pessoais. Nada disso sai do SOC. Nem para o colega de outra área, nem "só para comentar".
- **Necessidade de saber**: investigue o que o alerta pede. Bisbilhotar a caixa de e-mail de alguém "porque dá" é falta grave, e pode ser ilegal.
- **Registro de tudo**: horário, o que você viu, o que fez, com quem falou. Num incidente sério, o seu registro pode virar prova.
- **Calma**: um incidente real é estressante. Siga o playbook, documente, escale. Pressa sem método destrói evidências.

## 9. Lab: a fila da manhã

!!! cenario "Cenário"
    Segunda-feira, 8h. Você assume o turno e encontra estes dez alertas na fila. Para cada um, decida: **provável falso positivo**, **verdadeiro positivo benigno**, **precisa investigar** ou **escalar já**, e dê a **prioridade** (baixa, média, alta, crítica). Justifique em uma frase usando as seis perguntas.

    Informação útil sobre o ambiente: o time de TI faz manutenção aos domingos das 22h às 2h. A estação `PL-FIN-07` é do financeiro. O `SRV-DC01` é o controlador de domínio. O time de segurança roda um scanner de vulnerabilidades a partir de `10.10.1.50` toda terça-feira.

| # | Alerta | Detalhes |
|---|---|---|
| 1 | Falha de logon (4625) | 3 falhas da conta `joana.lima` na própria estação, às 8h02, seguidas de um logon com sucesso às 8h03 |
| 2 | Port scan interno | `10.10.1.50` tocou 1.200 portas em 40 máquinas, domingo às 23h |
| 3 | Office abrindo PowerShell | `excel.exe` → `powershell.exe -nop -w hidden -enc JABjAD0A...` em `PL-FIN-07`, às 7h48 |
| 4 | Log de segurança apagado (1102) | em `SRV-DC01`, sábado às 3h17, pela conta `adm.ricardo` |
| 5 | Muitas consultas DNS | estação `PL-LOG-22` fez 4.000 consultas para subdomínios aleatórios de `xk2jq9v.top` desde as 6h |
| 6 | Novo serviço instalado | serviço `GoogleUpdaterService` instalado em 60 estações, domingo às 23h30, pela conta de deploy da TI |
| 7 | Acesso ao LSASS | `MsMpEng.exe` (Microsoft Defender) acessou `lsass.exe` em `PL-RH-03` |
| 8 | Logon RDP de fora | logon tipo 10 da conta `suporte.terceiro` em `SRV-ERP01`, vindo de `203.0.113.40`, sábado às 2h |
| 9 | Usuário adicionado a grupo | conta `estagiario.ti` adicionada ao grupo `Domain Admins`, segunda às 7h55 |
| 10 | Antivírus detectou e removeu | arquivo `boleto_outubro.pdf.exe` em `Downloads` da `PL-FIN-02`, removido automaticamente às 7h30 |

<details markdown="1">
<summary>Ver uma resolução comentada</summary>

1. **Provável falso positivo, prioridade baixa.** Alguém errando a senha ao chegar e acertando em seguida, na própria máquina, em horário normal. Registre e feche. (Se fossem 300 falhas, ou vindas de outra máquina, a história mudaria.)
2. **Verdadeiro positivo benigno?** Cuidado: o scanner autorizado roda **terça**, e isto foi **domingo**. A origem é a máquina certa, mas o dia não bate. **Precisa investigar, prioridade média**: confirmar com o time de segurança se houve execução extra. Se ninguém confirmar, escalar. Detalhes que "quase batem" são os mais perigosos.
3. **Escalar já, prioridade crítica.** Excel abrindo PowerShell escondido e codificado (`-enc`) na máquina do financeiro, que é alvo preferido de golpe. É o padrão de macro maliciosa (tática Execution). Isole a máquina se o playbook permitir e escale com os detalhes.
4. **Escalar já, prioridade crítica.** Log apagado no controlador de domínio, de madrugada, **fora** da janela de manutenção (que é domingo). Mesmo que a conta seja de um administrador real, ela pode estar comprometida. Não pergunte ao Ricardo por chat antes de escalar: se a conta dele foi tomada, o atacante pode estar lendo.
5. **Escalar, prioridade alta.** Milhares de consultas para subdomínios aleatórios de um domínio estranho é padrão de C2 ou de vazamento por DNS (módulo 2).
6. **Verdadeiro positivo benigno, prioridade baixa,** **se** confirmado: dentro da janela de manutenção, pela conta de deploy, em massa. Mas confirme com a TI que esse deploy estava planejado, e anote o número da mudança no ticket. Atacantes também dão nomes "inocentes" a serviços.
7. **Provável falso positivo, prioridade baixa.** O antivírus acessa o LSASS para proteger o sistema. Confirme que o executável é o legítimo (caminho em `C:\ProgramData\Microsoft\Windows Defender\` ou `C:\Program Files\Windows Defender\`) e feche. Se o "MsMpEng.exe" estivesse rodando de `C:\Users\Public\`, seria um disfarce.
8. **Escalar já, prioridade crítica.** Acesso remoto ao servidor do ERP, por conta de terceiro, vindo da internet, de madrugada no fim de semana. Mesmo que o fornecedor tenha permissão de acesso, o horário e a origem exigem confirmação imediata.
9. **Escalar já, prioridade crítica.** Um estagiário virando administrador do domínio inteiro não é um processo normal. Pode ser erro grave de alguém da TI, ou escalação de privilégio por um atacante. Em ambos os casos, precisa de ação agora.
10. **Precisa investigar, prioridade média.** O antivírus removeu, ótimo, mas o arquivo **chegou** até lá. `boleto_outubro.pdf.exe` é a extensão dupla clássica de phishing. Como chegou (e-mail? download?), outras pessoas receberam o mesmo? Ele chegou a ser executado antes de ser removido? "O antivírus pegou" encerra o arquivo, não a investigação.

</details>

## Checagem

1. Qual a diferença entre severidade e prioridade?
2. O que é um falso negativo, e por que ele é o mais perigoso?
3. Cite três situações em que o N1 deve escalar imediatamente.
4. No alerta 2 do lab, por que "a origem é o scanner autorizado" não bastou para fechar?
5. O que é uma tática e o que é uma técnica no MITRE ATT&CK?

<details markdown="1">
<summary>Ver respostas</summary>

1. Severidade é o quão grave é o comportamento detectado. Prioridade combina a severidade com a criticidade do ativo envolvido, e define a ordem de atendimento.
2. É um ataque real que nenhuma regra detectou. É o mais perigoso porque é invisível: não aparece na fila, e o atacante segue agindo sem ninguém saber.
3. Qualquer três entre: execução maliciosa, roubo de credenciais, movimento lateral, saída de dados, apagamento de logs, envolvimento de dados pessoais, ou dúvida real sobre a gravidade.
4. Porque o contexto (o dia) não batia com o comportamento autorizado (terça-feira). Um atacante dentro da rede pode usar justamente a máquina do scanner para se misturar. Confirmar com quem é dono da atividade é parte da triagem.
5. Tática é o objetivo do atacante naquela etapa (por exemplo, Credential Access). Técnica é o meio usado para atingir o objetivo (por exemplo, `T1003.001`, ler a memória do LSASS).

</details>

!!! dica "Para ir além"
    - Navegue pelo site do **MITRE ATT&CK** (attack.mitre.org) quando tiver internet. Escolha uma técnica de cada tática e leia os exemplos de detecção.
    - Leia sobre a **Pirâmide da Dor** (*Pyramid of Pain*), de David Bianco: por que bloquear um hash é fácil para o atacante contornar, e detectar um comportamento é difícil.
