<!-- descricao: Processos, contas, logons e Event IDs do Windows, aprendidos lendo logs de ataques reais. -->
# Módulo 3: Windows por dentro (pelos logs)

<p class="sub">Você não precisa usar Windows para investigá-lo. Precisa entender o que ele anota sobre si mesmo.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - por que o SOC estuda Windows principalmente **pelos logs**;
    - o que são processos, processo pai e filho, e por que a "árvore de processos" é a melhor amiga do analista;
    - o que são contas, SIDs e grupos, e quais contas especiais existem;
    - os **tipos de logon** e o que cada um revela;
    - os **Event IDs** mais importantes do log de Segurança e do Sysmon;
    - por que o `lsass.exe` é o alvo preferido de quem rouba senhas;
    - ler eventos reais de ataques com o Chainsaw.

## 1. Por que pelos logs

Numa empresa como a Pantera Logística, há centenas de computadores e servidores Windows. O analista de SOC não entra em cada um. Cada máquina **anota o que acontece** nos seus logs de eventos (arquivos `.evtx`), e esses registros são enviados ao SIEM. Investigar Windows, no SOC, é **ler esses registros e reconstruir a história**.

Os registros que mais importam vêm de dois lugares:

| Log | O que registra |
|---|---|
| **Security** (Segurança) | logons, falhas de logon, criação de contas, mudanças de grupo, limpeza de log |
| **Sysmon** | uma ferramenta gratuita da Microsoft que registra em detalhe: cada processo criado (com a linha de comando), conexões de rede, acessos a outros processos, alterações de registro |

Sem Sysmon (ou algo equivalente), o SOC enxerga só uma fração do que acontece. Empresas maduras instalam o Sysmon em todas as máquinas.

## 2. Processos e a árvore de processos

Um **processo** é um programa em execução. Cada processo tem:

- um **PID** (número de identificação, que muda a cada execução);
- uma **imagem** (o arquivo executável, como `C:\Windows\System32\cmd.exe`);
- uma **linha de comando** (o programa mais os argumentos com que foi chamado);
- um **usuário** (em nome de quem ele roda);
- um **processo pai** (quem o criou).

Todo processo nasce de outro. Isso forma uma **árvore**. Uma árvore normal de um computador Windows se parece com isto:

```
wininit.exe
 └─ services.exe                (gerencia os serviços do Windows)
     ├─ svchost.exe -k netsvcs  (hospeda serviços do sistema)
     └─ svchost.exe -k LocalService
winlogon.exe
 └─ userinit.exe
     └─ explorer.exe            (a área de trabalho do usuário)
         ├─ chrome.exe
         └─ outlook.exe
```

!!! atacante "Como o atacante pensa"
    O atacante precisa executar comandos, e todo comando vira um processo **com um pai**. É aí que ele se denuncia. Combinações que fazem o SOC parar e olhar:

    | Pai | Filho | Por que é estranho |
    |---|---|---|
    | `winword.exe` / `excel.exe` | `powershell.exe` / `cmd.exe` | documento de Office não tem motivo para abrir um terminal: clássico de macro maliciosa |
    | `outlook.exe` | `powershell.exe` | anexo executando comandos |
    | `services.exe` | `cmd.exe` | um "serviço" que na verdade é um comando: técnica de PsExec e similares |
    | `svchost.exe` | `cmd.exe` | o hospedeiro de serviços abrindo um terminal |
    | `wmiprvse.exe` | qualquer coisa interativa | execução remota via WMI |

    E desconfie de linhas de comando com `-w hidden` (janela escondida), `-nop` (sem perfil), `-enc` (comando codificado em base64) ou textos enormes e ilegíveis.

## 3. Contas, SIDs e grupos

Toda ação no Windows é feita **em nome de uma conta**. Cada conta tem um **SID** (identificador de segurança), um código único como `S-1-5-21-3461203602-4096304019-2269080069-1001`. O final do SID (o "RID") diz muito:

| SID ou final | Quem é |
|---|---|
| `...-500` | a conta **Administrator** interna |
| `...-501` | a conta **Guest** (Convidado), que deveria estar sempre desativada |
| `...-1000` em diante | contas criadas por pessoas |
| `S-1-5-18` | **SYSTEM**: o próprio sistema operacional, mais poderoso que um administrador |
| `S-1-5-19` / `S-1-5-20` | LOCAL SERVICE / NETWORK SERVICE: contas de serviços com poucos privilégios |

Contas pertencem a **grupos**, e o grupo é que dá o poder. O mais importante: **Administrators** (Administradores). Quem entra nesse grupo manda na máquina.

Contas de computador terminam com `$` (por exemplo `WIN-77LTAPHIQ1R$`). Elas aparecem muito nos logs, porque os computadores de um domínio também se autenticam uns nos outros.

## 4. Tipos de logon

Toda vez que alguém (ou algo) se autentica, o Windows registra um **4624** (logon com sucesso) ou um **4625** (falha). O campo **LogonType** diz **como** foi o acesso:

| Tipo | Nome | Quando acontece | Olhar do SOC |
|---|---|---|---|
| 2 | Interactive | alguém digitou a senha no teclado da máquina | normal em estações; em servidor, quem está sentado lá? |
| 3 | Network | acesso pela rede: pasta compartilhada, WMI, PsExec | o mais comum e o mais usado em movimento lateral |
| 4 | Batch | tarefa agendada | tarefas novas podem ser persistência |
| 5 | Service | um serviço iniciou com uma conta | serviço novo com conta de usuário é suspeito |
| 7 | Unlock | desbloqueio de tela | rotina |
| 9 | NewCredentials | um programa usou **outras** credenciais (`runas /netonly`) | raro, e técnica clássica de *pass-the-hash* |
| 10 | RemoteInteractive | área de trabalho remota (RDP) | de onde veio? fora do horário? |
| 11 | CachedInteractive | logon com credencial guardada (notebook fora da rede) | rotina em notebooks |

Grave os tipos **2, 3 e 10**. Eles aparecem em quase toda investigação.

## 5. Event IDs que você precisa conhecer

### Log de Segurança

| ID | Evento |
|---|---|
| 4624 | logon com sucesso |
| 4625 | falha de logon |
| 4634 / 4647 | logoff |
| 4648 | logon com credenciais explícitas (alguém informou usuário e senha de outra conta) |
| 4672 | logon com privilégios especiais (acesso de administrador) |
| 4688 | processo criado (precisa estar habilitado) |
| 4697 / 7045 | serviço instalado |
| 4698 | tarefa agendada criada |
| 4720 | conta de usuário criada |
| 4728 / 4732 | membro adicionado a um grupo (global / local) |
| 1102 | **o log de segurança foi apagado** |

### Sysmon

| ID | Evento |
|---|---|
| 1 | processo criado, com linha de comando, pai, usuário e hash |
| 3 | conexão de rede feita por um processo |
| 7 | DLL carregada por um processo |
| 8 | um processo criou uma *thread* dentro de outro (injeção) |
| 10 | um processo **acessou a memória** de outro |
| 11 | arquivo criado |
| 12 / 13 | chave de registro criada / valor alterado |
| 22 | consulta DNS feita por um processo |

!!! erro "Erro comum de N1"
    Tratar o **1102** como "só um evento de manutenção". Apagar o log de segurança é uma das primeiras coisas que um atacante faz para sumir com os rastros. Um 1102 fora de uma janela de manutenção planejada é, por si só, motivo para escalar.

## 6. O LSASS: o cofre das senhas

O `lsass.exe` (*Local Security Authority Subsystem Service*) é o processo que verifica senhas e guarda, na memória, as credenciais de quem está logado. Por isso ele é o alvo preferido de ferramentas de roubo de credenciais, como o **Mimikatz**: quem lê a memória do LSASS pode sair de lá com senhas ou *hashes* de senha de todo mundo que usou aquela máquina, inclusive administradores.

No Sysmon, isso aparece como um **evento 10** (acesso a processo) com `TargetImage` = `lsass.exe`. Vários programas legítimos (antivírus, por exemplo) também acessam o LSASS. O que muda é **quem acessa** e **com qual permissão** (o campo `GrantedAccess`).

## 7. Lab: lendo ataques reais

!!! cenario "Cenário"
    O seu líder de turno separou quatro casos antigos da Pantera Logística, já encerrados, para você aprender a ler eventos de Windows. São logs reais gravados durante ataques de laboratório. Para cada um, você vai responder: **o que aconteceu, quem fez, em que máquina e por que é suspeito**.

Vamos usar o **Chainsaw**, que lê arquivos `.evtx` direto no Linux. Comece indo para o acervo:

```bash
cd /opt/besafe/chainsaw/EVTX-ATTACK-SAMPLES
```

Dois comandos do Chainsaw que você vai usar:

| Comando | O que faz |
|---|---|
| `chainsaw dump ARQUIVO` | mostra **todos** os eventos do arquivo |
| `chainsaw search -t 'Event.System.EventID: =N' ARQUIVO` | mostra só os eventos com o Event ID `N` |

A saída vem em blocos (um por evento) com duas partes: `System` (dados comuns: ID, horário, computador) e `EventData` (os detalhes daquele tipo de evento).

### Caso 1: quem mexeu no cofre?

```bash
chainsaw dump "Credential Access/sysmon_10_lsass_mimikatz_sekurlsa_logonpasswords.evtx"
```

O arquivo tem um único evento. Encontre e anote:

- o `EventID` e o `Channel`: que tipo de evento é este?
- o `Computer`;
- o `SourceImage` (quem acessou) e o `TargetImage` (quem foi acessado);
- o `GrantedAccess`;
- o caminho do `SourceImage`: onde estava o programa?

### Caso 2: um serviço que não era serviço

```bash
chainsaw dump "Lateral Movement/LM_sysmon_psexec_smb_meterpreter.evtx" | less
```

São dez eventos de Sysmon. Use `/EventID` dentro do `less` para pular de evento em evento. Concentre-se em:

1. os eventos **13** (alteração de registro) feitos por `services.exe` na chave `HKLM\System\CurrentControlSet\services\hello\...`: um serviço chamado **hello** está sendo criado. Qual o valor de `ImagePath` (o que esse serviço executa)?
2. os eventos **1** (processo criado): monte a árvore `ParentImage → Image` dos três processos, em ordem de horário.
3. os eventos **3** (conexão de rede): para qual IP e **porta** o `powershell.exe` se conectou?

!!! dica "Para enxergar a árvore de uma vez"
    Filtre só os campos que importam:

    ```bash
    chainsaw search -t 'Event.System.EventID: =1' "Lateral Movement/LM_sysmon_psexec_smb_meterpreter.evtx" | grep -E "UtcTime|ParentImage|^    Image|User:"
    ```

### Caso 3: logons pela rede

```bash
chainsaw search -t 'Event.System.EventID: =4624' "Lateral Movement/LM_WMI_4624_4688_TargetHost.evtx" | grep -E "SystemTime|LogonType|TargetUserName|IpAddress|AuthenticationPackageName"
```

Depois veja os processos criados na máquina:

```bash
chainsaw search -t 'Event.System.EventID: =4688' "Lateral Movement/LM_WMI_4624_4688_TargetHost.evtx" | grep -E "SystemTime|NewProcessName"
```

Responda: qual conta fez logon **tipo 3** vindo de qual IP, e que processos apareceram em seguida?

### Caso 4: alguém aumentou os próprios poderes

```bash
chainsaw dump "Persistence/Network_Service_Guest_added_to_admins_4732.evtx" | grep -E "EventID|SystemTime|MemberSid|TargetUserName|SubjectUserName"
```

Dois eventos **4732** (membro adicionado a grupo local). Olhe o **final** de cada `MemberSid` e use a tabela da seção 3.

### Bônus: o atacante apagando os rastros

```bash
chainsaw dump "Lateral Movement/LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx" | grep -E "EventID|LogonType|TargetUserName|NewProcessName"
```

Procure o tipo de logon do 4624 e um Event ID que, sozinho, já justifica escalar.

## Checagem

1. No caso 1, o que aconteceu e por que o caminho do `SourceImage` agrava a situação?
2. No caso 2, qual é a árvore de processos e por que cada elo é suspeito?
3. Ainda no caso 2, por que a porta de destino da conexão chama atenção?
4. No caso 3, qual conta acessou a máquina, de onde, com qual tipo de logon, e o que foi executado?
5. No caso 4, quem foi adicionado ao grupo Administrators e por que isso é grave?
6. No bônus, qual o tipo de logon e qual evento indica tentativa de esconder rastros?
7. Por que o mesmo evento "processo X acessou o lsass.exe" pode ser normal em uma situação e um incidente grave em outra?

<details markdown="1">
<summary>Ver respostas</summary>

1. É um **Sysmon 10**: o processo `mimikatz.exe` acessou a memória do `lsass.exe` (com `GrantedAccess` `0x1010`, uma combinação típica da ferramenta) na máquina `PC04.example.corp`. Ou seja: **tentativa de roubo de credenciais**. O caminho agrava porque o programa estava na **área de trabalho do usuário** (`C:\Users\IEUser\Desktop\mimikatz_trunk\...`), e não numa pasta de software instalado. Ferramenta trazida de fora e executada à mão. Isso se escala imediatamente, e todas as contas que usaram aquela máquina devem ser consideradas comprometidas.
2. `services.exe → cmd.exe → powershell.exe → powershell.exe`, tudo como `NT AUTHORITY\SYSTEM`. O `services.exe` criando `cmd.exe` mostra que o "serviço" **hello** era na verdade um comando (o `ImagePath` é `%%COMSPEC%% /b /c start /b /min powershell.exe -nop -w hidden ...`; `%COMSPEC%` é a variável do Windows que aponta para o `cmd.exe`, e aparece com `%%` duplicado porque o log "escapa" o caractere). O PowerShell roda **escondido** (`-w hidden`), sem perfil (`-nop`), e cria outro PowerShell que carrega código compactado na memória. É o padrão de ferramentas como o PsExec do Metasploit: o atacante, com credenciais de administrador, cria um serviço remoto para ganhar execução como SYSTEM.
3. O `powershell.exe` se conectou a `10.0.2.19` na porta **4444**, a porta padrão do Meterpreter (Metasploit). Atacantes descuidados não mudam o padrão. A conexão sai de dentro da rede para outra máquina, o que indica um **canal de comando** do atacante.
4. A conta **Administrator** do domínio `EXAMPLE` fez logons **tipo 3** (rede) vindos de `10.0.2.17`, com Kerberos e NTLM. Logo depois surgem `WmiPrvSE.exe` e `calc.exe`: alguém usou **WMI** remotamente para executar um programa. A calculadora é a "prova de conceito" clássica de laboratório; num ataque real seria um malware. É **movimento lateral**.
5. A conta de RID **501** (**Guest**, o Convidado) e a conta **S-1-5-20** (**NETWORK SERVICE**) foram colocadas no grupo **Administrators**, pelo usuário `IEUser`. É uma forma de **persistência e escalação**: contas que ninguém vigia ganham poder total. Guest deveria estar desativada; NETWORK SERVICE nunca deveria ser administradora.
6. Logon **tipo 9** (NewCredentials), característico de *pass-the-hash* com Mimikatz, e o evento **1102**: o log de segurança foi apagado.
7. Porque o contexto muda tudo: o antivírus corporativo, assinado e instalado em `C:\Program Files\`, acessa o LSASS o tempo todo. Um executável desconhecido, rodando da pasta `Downloads` ou da área de trabalho, às 2h da manhã, com permissões típicas de despejo de memória, é ataque. O N1 bom não decora "evento X é ruim": ele pergunta **quem, de onde, quando e se isso é normal aqui**.

</details>

!!! dica "Para ir além"
    - Leia a documentação do **Sysmon** no site da Microsoft (Sysinternals). A lista completa de eventos e campos é curta e muito útil.
    - Pesquise o projeto **SwiftOnSecurity sysmon-config**: uma configuração comentada que explica por que cada coisa é registrada.
    - Explore outros arquivos do acervo. Boas escolhas para começar: `Credential Access/sysmon_10_1_memdump_comsvcs_minidump.evtx` (despejo do LSASS com uma ferramenta do próprio Windows) e `Persistence/persistence_accessibility_features_osk_sysmon1.evtx` (a "porta dos fundos" do teclado virtual).
