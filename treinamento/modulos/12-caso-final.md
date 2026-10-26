<!-- descricao: Investigação completa de uma estação comprometida, do primeiro alerta ao relatório e à comunicação. -->
# Módulo 12: Caso final, a estação PC04

<p class="sub">Tudo que você aprendeu, numa investigação só. Sem passo a passo desta vez: só o cenário, as perguntas e os entregáveis.</p>

!!! objetivo "O que você vai entregar"
    1. uma **linha do tempo** com fuso horário;
    2. o **mapeamento** de cada etapa para uma tática do MITRE ATT&CK;
    3. a lista de **indicadores** (defanged);
    4. o **ticket** completo para o N2 (módulo 10);
    5. a **avaliação de dados pessoais** para a encarregada (módulo 11);
    6. a **mensagem** para a gerente de RH, que não é técnica.

## O cenário

!!! cenario "Segunda-feira, 9h"
    O antivírus da estação **PC04**, do setor de **RH** da Pantera Logística, gerou um alerta genérico de "ferramenta de despejo de memória" no domingo à noite e ninguém olhou. Hoje de manhã, a equipe de infraestrutura percebeu que **o tráfego da porta 80 da PC04 está estranho** e pediu ajuda ao SOC.

    A equipe de resposta coletou os logs da estação e de mais um evento que "parecia relacionado". Eles estão em:

    ```
    ~/labs/12-caso-final/PC04-logs/
    ```

    Na PC04 trabalha a analista de RH que usa a conta **IEUser**. Pelo servidor de arquivos, a PC04 tem acesso às pastas do RH (fichas de admissão, folha de pagamento e atestados).

    O seu líder disse apenas: *"Quero saber o que aconteceu, em que ordem, o que o atacante conseguiu, e o que precisa ser feito. E veja se tem LGPD nisso."*

## As ferramentas que você já conhece

Você pode usar o que quiser. Algumas sugestões:

- `hayabusa dfir-timeline -d PASTA -o saida.csv -w -q -C -U` para a visão geral (o `-U` deixa tudo em UTC, para combinar com os eventos brutos);
- `chainsaw hunt` com as regras Sigma, para a separação por categoria;
- `chainsaw dump` e `chainsaw search` para conferir cada evento bruto;
- `python3` com `csv` para ordenar, filtrar e contar;
- o CyberChef para defang.

!!! atencao "Lembretes dos módulos anteriores"
    - Título de regra não é conclusão: confira o evento bruto.
    - Fato e hipótese, separados.
    - Fuso horário em toda linha do tempo.
    - Nem tudo que "parece relacionado" é do mesmo incidente.

## Perguntas que guiam a investigação

1. Qual foi a **primeira** atividade maliciosa registrada, quando e com qual ferramenta?
2. O atacante tentou roubar credenciais **mais de uma vez**? Com quais ferramentas, e onde os resultados foram gravados?
3. Houve tentativa de **apagar rastros**? Quando, e por qual conta?
4. O que o atacante fez com o **compartilhamento de arquivos**?
5. Que ferramenta foi instalada para **acesso remoto**, e que alterações ela fez no sistema (registro, firewall, permissões)?
6. Por que a porta do RDP foi alterada para **80**? Como isso se conecta com o que a infraestrutura percebeu?
7. Que outro programa malicioso aparece no fim do dia, e o que ele faz?
8. Todos os arquivos coletados pertencem ao **mesmo incidente**? Justifique.
9. Mapeie cada etapa para uma tática do MITRE ATT&CK.
10. Há dados pessoais em risco? Quais critérios de relevância do módulo 11 parecem presentes?

## Entregáveis

Escreva tudo no seu caderno (`~/caderno/`), num arquivo `caso-final-PC04.md`. Use a estrutura de ticket do módulo 10. Para a mensagem à gerente de RH, use as cinco perguntas da seção 7 do módulo 10.

<details markdown="1">
<summary>Ver a resolução completa (só depois de terminar)</summary>

### Linha do tempo (UTC, 17/03/2019)

| Horário | Evento | Fonte |
|---|---|---|
| 19:09:41 | `procdump.exe` (em `C:\Users\IEUser\Desktop\`) acessa o `lsass.exe` e grava `lsass.exe_190317_120941.dmp` na área de trabalho | Sysmon 10 e 11 |
| 19:10:03 | `taskmgr.exe` gera outro despejo do LSASS em `C:\Users\IEUser\AppData\Local\Temp\lsass (2).DMP` | Sysmon 10 e 11 |
| 19:26:42 | **log de segurança apagado** pela conta `IEUser` | Security 1102 |
| 19:30:30 | compartilhamento de rede criado apontando para `c:\windows\system32`, pela `IEUser` | Security 5142 |
| 19:37:11 | `mimikatz.exe` (na área de trabalho) acessa o `lsass.exe` | Sysmon 10 |
| 20:17:44 | arquivos do **RDP Wrapper** extraídos na área de trabalho | Sysmon 11 |
| 20:17:52 | `install.bat` executa `RDPWInst.exe -i -o` | Sysmon 1 |
| 20:18:05 | `ServiceDll` do serviço de Área de Trabalho Remota trocado para `rdpwrap.dll` | Sysmon 13 |
| 20:18:09 | RDP habilitado (`fDenyTSConnections = 0`), sessões simultâneas habilitadas e regra de firewall liberando a porta 3389 via `netsh` | Sysmon 13 e 1 |
| 20:20:17 | `takeown` e `icacls` tomam posse do `termsrv.dll` e dão controle total a todos (`S-1-1-0`) | Sysmon 1 |
| 20:22:59 | **porta do RDP alterada para 80** (`PortNumber = 0x50`) | Sysmon 13 |
| 20:42:51 | `keylogger_directx.exe` (área de trabalho) começa a registrar o teclado | Sysmon 13 |

### O arquivo que não pertence

O `wmighost_sysmon_20_21_1.evtx` registra a criação de uma **persistência via WMI** (um *ActiveScriptEventConsumer* chamado `ProbeScriptFint`, que busca comandos em `hxxp://kumardeep[.]sosblogs[.]com/...`) feita pelo `WMIGhost.exe`. Mas é de **03/04/2019**, mais de duas semanas depois, e na área de trabalho de **outro usuário** (`user01`). Não há ligação comprovada com a sequência de 17/03. Registre como **evento separado, a investigar em ticket próprio**, e não o inclua na linha do tempo deste incidente sem evidência. (Se ele fosse da PC04 e pós-incidente, indicaria que o atacante voltou, mas isso precisa ser comprovado, não suposto.)

### Mapeamento MITRE ATT&CK

| Etapa | Tática | Técnica (exemplo) |
|---|---|---|
| procdump, taskmgr, mimikatz no LSASS | Credential Access | T1003.001 (LSASS Memory) |
| log apagado | Defense Evasion | T1070.001 (Clear Windows Event Logs) |
| compartilhamento para `system32` | Lateral Movement / Collection (preparação) | T1021.002 (SMB/Admin Shares) |
| RDP Wrapper, ServiceDll, firewall, termsrv.dll | Persistence / Defense Evasion | T1133 (External Remote Services), T1562.004 (Disable or Modify System Firewall) |
| porta do RDP para 80 | Command and Control / Defense Evasion | T1571 (Non-Standard Port) |
| keylogger | Collection / Credential Access | T1056.001 (Keylogging) |

### Indicadores (defanged)

- `C:\Users\IEUser\Desktop\procdump.exe`
- `C:\Users\IEUser\Desktop\lsass.exe_190317_120941.dmp` e `C:\Users\IEUser\AppData\Local\Temp\lsass (2).DMP`
- `C:\Users\IEUser\Desktop\mimikatz_trunk\Win32\mimikatz.exe`
- `C:\Users\IEUser\Desktop\RDPWrap-v1.6.2\` e `%ProgramFiles%\RDP Wrapper\rdpwrap.dll`
- `C:\Users\IEUser\Desktop\keylogger_directx.exe`
- RDP escutando na porta **80/tcp**
- (evento separado) `hxxp://kumardeep[.]sosblogs[.]com/...` e `C:\Users\user01\Desktop\WMIGhost.exe`

### Avaliação

**Fatos:** na PC04, em pouco mais de 1h30, a conta `IEUser` foi usada para atacar a memória do LSASS três vezes (despejos em arquivo com o procdump e com o Gerenciador de Tarefas, e acesso direto com o Mimikatz), apagar o log de segurança, mexer em compartilhamentos, instalar um acesso remoto adulterado (RDP Wrapper) exposto na porta 80 e executar um keylogger. Todas as ferramentas estavam na área de trabalho do usuário.

**Hipóteses:** (1) alguém com controle da sessão de `IEUser` (remoto ou presencial) agiu à mão, com ferramentas trazidas de fora; (2) o RDP na porta 80 é a porta dos fundos que explica o "tráfego estranho" percebido pela infraestrutura; (3) as credenciais de todos que fizeram logon na PC04 recentemente (inclusive técnicos da TI, se algum logou lá) devem ser consideradas comprometidas.

### Ações recomendadas

Isolar a PC04 da rede; desabilitar e redefinir a senha de `IEUser` e de qualquer conta que tenha logado na PC04; verificar logons via RDP na porta 80 a partir de fora; procurar os mesmos indicadores em outras máquinas; verificar o que foi acessado nas pastas do RH a partir da PC04; preservar a máquina para análise forense (não formatar).

### LGPD

A PC04 acessa pastas com **dados pessoais de colaboradores**, incluindo **dados sensíveis** (atestados = saúde) e **financeiros** (folha). Houve roubo de **credenciais** (dado de autenticação) e um **keylogger** ativo. Ainda não se sabe se houve acesso ou cópia das pastas do RH. Critérios potencialmente presentes: dados sensíveis, financeiros e de autenticação. Encaminhar **imediatamente** à encarregada, registrando a data e a hora em que o SOC tomou conhecimento.

### Mensagem para a gerente de RH (exemplo)

> "Identificamos que o computador PC04, do seu setor, foi usado por alguém não autorizado no domingo à noite para tentar capturar senhas e instalar um acesso remoto. Desconectamos o computador da rede e bloqueamos a conta que estava em uso nele. Ainda estamos verificando se as pastas do RH foram acessadas, e a nossa encarregada de proteção de dados já foi informada. A colaboradora vai receber outro computador e uma senha nova ainda hoje. Pedimos que ninguém do RH use o PC04 nem tente ligá-lo. Próxima atualização às 14h."

</details>

## Parabéns

Se você chegou até aqui fazendo os labs, você já sabe mais do que muita gente que se candidata a vagas de N1: lê logs de Windows sem Windows, entende rede pacote por pacote, desmonta código ofuscado, escreve regras, separa fato de hipótese e sabe quando um incidente vira assunto de proteção de dados.

O próximo passo é **repetir**. Volte ao acervo EVTX-ATTACK-SAMPLES, escolha uma pasta e investigue sozinho. Cada arquivo é um caso novo.

!!! dica "Para continuar"
    - Mantenha o seu caderno vivo. Ele vira o seu manual pessoal.
    - Participe de comunidades de SOC e Blue Team e de CTFs defensivos (Blue Team Labs Online, CyberDefenders).
    - Estude para certificações de entrada, se fizer sentido para você.
    - E volte aqui: novas versões desta VM vão trazer novos casos.
