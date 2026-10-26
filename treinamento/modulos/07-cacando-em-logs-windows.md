<!-- descricao: Hayabusa, Chainsaw e regras Sigma para caçar ataques em centenas de logs de uma vez. -->
# Módulo 7: Caçando em logs do Windows

<p class="sub">No módulo 3 você leu eventos um a um. Agora vai deixar as regras fazerem a primeira peneira, e aprender a não confiar cegamente nelas.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - o que é uma regra de detecção e o formato **Sigma**;
    - rodar o **Hayabusa** e o **Chainsaw** sobre um arquivo ou uma pasta inteira de logs;
    - ler uma linha do tempo de detecções e priorizar pelo nível;
    - **ir da detecção ao evento bruto** para confirmar o que aconteceu;
    - ler uma regra Sigma e entender exatamente o que ela procura;
    - reconhecer quando uma regra acertou a técnica mas o contexto muda a conclusão.

## 1. Regras de detecção e o Sigma

Uma **regra de detecção** descreve um padrão suspeito: "se aparecer um processo `rundll32.exe` com `comsvcs` e `MiniDump` na linha de comando, avise". O SIEM aplica milhares de regras a cada evento que chega.

O problema histórico: cada SIEM tinha sua própria linguagem de regras. O **Sigma** resolveu isso: é um formato **aberto e neutro** (em YAML) para escrever regras uma vez e convertê-las para qualquer ferramenta. Existe uma comunidade enorme publicando regras Sigma de graça.

O Hayabusa e o Chainsaw usam regras Sigma para caçar direto em arquivos `.evtx`, sem precisar de SIEM. É o que um analista faz quando recebe os logs de uma máquina para investigar.

## 2. As duas ferramentas

| | Hayabusa | Chainsaw |
|---|---|---|
| Autor | Yamato Security (Japão) | WithSecure (Finlândia) |
| Ponto forte | linha do tempo completa, muito rápido, resumos (logons, métricas) | caça com Sigma e regras próprias, separa resultados por categoria |
| Comando principal | `hayabusa dfir-timeline` | `chainsaw hunt` |

Elas se complementam: se as duas apontam a mesma coisa, sua confiança aumenta.

### Níveis

As regras têm um nível que indica a gravidade estimada do que detectam:

| Nível | No Hayabusa | Leitura |
|---|---|---|
| informational | `info` | registro de contexto, não é alerta |
| low | `low` | pode ser normal; olhar se houver tempo |
| medium | `med` | suspeito; vale investigar |
| high | `high` | provável atividade maliciosa |
| critical | `crit` | quase certamente malicioso |

## 3. Lab 1: uma detecção, do alerta ao evento

!!! cenario "Cenário"
    A equipe de resposta recolheu os logs de uma estação (`MSEDGEWIN10`) depois que o antivírus reclamou de "algo com dump de memória". Seu trabalho é dizer o que aconteceu.

```bash
cd ~/labs/EVTX-ATTACK-SAMPLES
hayabusa dfir-timeline -f "Credential Access/sysmon_10_1_memdump_comsvcs_minidump.evtx" -o ~/labs/comsvcs.csv -w -q -C
```

| Opção | Significado |
|---|---|
| `-f` | um arquivo `.evtx` (use `-d` para uma pasta inteira) |
| `-o` | salvar a linha do tempo em CSV |
| `-w` | não fazer perguntas (sem o "assistente") |
| `-q` | sem o banner de abertura |
| `-C` | sobrescrever o arquivo de saída se já existir |

Veja o resultado:

```bash
column -s, -t < ~/labs/comsvcs.csv | cut -c1-140 | less -S
```

Você vai encontrar linhas `info` (registros de contexto), `low`, uma `med` e duas **`high`**. Uma delas é genérica (**Proc Access (Sysmon Alert)**, veja o quadro "Detecções genéricas" no lab 2). A outra é específica e conta o que aconteceu: **Process Memory Dump Via Comsvcs.DLL**.

!!! atencao "Horários"
    O Hayabusa mostra os horários no fuso da VM (`-03:00`, horário de Brasília). O Chainsaw e os eventos brutos usam **UTC** (três horas a mais). Num incidente, misturar fusos é uma fonte clássica de confusão na linha do tempo. Use `-U` no Hayabusa se quiser tudo em UTC.

Agora vá ao **evento bruto** que gerou a detecção. A regra é sobre criação de processo, então:

```bash
chainsaw search -t 'Event.System.EventID: =1' "Credential Access/sysmon_10_1_memdump_comsvcs_minidump.evtx" | grep -E "UtcTime|^    Image|CommandLine|ParentImage|^    User"
```

Monte a história com o que aparecer: quem rodou, o que rodou, a partir de qual processo pai, e **qual processo teve a memória despejada** (o número depois de `MiniDump` é o PID do alvo).

## 4. Lendo a regra Sigma

Uma detecção só é útil se você sabe **o que ela realmente verifica**. Encontre a regra:

```bash
grep -rl "title: Process Memory Dump Via Comsvcs.DLL" /opt/besafe/hayabusa/rules
```

Aparecem **dois** arquivos com o mesmo nome: um em `builtin/` (adaptado para o evento 4688 do log de Segurança) e outro em `sysmon/` (para o evento 1 do Sysmon). É a mesma regra Sigma convertida para as duas fontes de log. A nossa detecção veio do Sysmon, então abra essa versão:

```bash
less /opt/besafe/hayabusa/rules/sigma/sysmon/process_creation/proc_creation_win_rundll32_process_dump_via_comsvcs.yml
```

As partes que importam:

| Campo | O que diz |
|---|---|
| `title` / `description` | o que a regra detecta, em uma frase |
| `tags` | táticas e técnicas do MITRE ATT&CK (aqui, `attack.t1003.001`: roubo de credenciais da memória do LSASS) |
| `logsource` | que tipo de log a regra examina (`process_creation`) |
| `detection` | **o coração**: as condições. Aqui, um processo `rundll32` cuja linha de comando contém `comsvcs`, `full` e algo como `MiniDump` ou `#24` |
| `condition` | como as seleções se combinam (`and`, `or`, `1 of ...`) |
| `falsepositives` | quando a regra pode disparar à toa (aqui: "Unlikely", improvável) |
| `level` | o nível (`high`) |

!!! erro "Erro comum de N1"
    Ler só o título da regra e concluir. O título diz "dump de memória"; o evento bruto diz **de qual processo**. Antes de escrever no ticket "roubo de credenciais", confirme se o alvo foi o `lsass.exe`. Se não foi, a técnica continua grave (alguém testando ou preparando o ataque), mas a conclusão e o impacto mudam.

## 5. Lab 2: uma pasta inteira

Agora em escala: todas as amostras de roubo de credenciais, só nível alto ou crítico.

```bash
hayabusa dfir-timeline -d "Credential Access" -o ~/labs/credenciais.csv -w -q -C -m high
```

O `-m high` carrega só as regras de nível `high` para cima. Conte e ranqueie (lembre-se do módulo 1: CSV de verdade pede um leitor de CSV):

```bash
python3 -c "
import csv, collections
linhas = list(csv.DictReader(open('/home/analista/labs/credenciais.csv')))
print(len(linhas), 'deteccoes')
print(collections.Counter(l['Level'] for l in linhas))
for titulo, n in collections.Counter(l['RuleTitle'] for l in linhas).most_common(10):
    print(f'{n:4}  {titulo}')
"
```

E as críticas, com a máquina:

```bash
python3 -c "
import csv
for l in csv.DictReader(open('/home/analista/labs/credenciais.csv')):
    if l['Level'] == 'crit':
        print(l['Timestamp'][:19], '|', l['Computer'], '|', l['RuleTitle'])
"
```

!!! atencao "Detecções genéricas"
    Você vai ver no ranking regras como **Proc Exec (Sysmon Alert)** ou **Proc Access (Sysmon Alert)**. Elas não descrevem uma técnica: só avisam que a própria configuração do Sysmon marcou o evento como interessante. São úteis como contexto, mas **não** são, sozinhas, a explicação do que aconteceu.

## 6. Lab 3: o Chainsaw separando por assunto

```bash
cd /opt/besafe/chainsaw
chainsaw hunt "EVTX-ATTACK-SAMPLES/Lateral Movement" -s sigma/ --mapping mappings/sigma-event-logs-all.yml -r rules/ --csv --output ~/labs/movimento-lateral
ls ~/labs/movimento-lateral
```

| Opção | Significado |
|---|---|
| `-s sigma/` | usar as regras Sigma |
| `--mapping` | como traduzir os campos do Sigma para os campos dos eventos do Windows |
| `-r rules/` | usar também as regras próprias do Chainsaw |
| `--csv --output` | gravar os resultados em CSVs separados por categoria |

O Chainsaw cria arquivos como `lateral_movement.csv`, `log_tampering.csv` e `sigma.csv`. Abra o de **adulteração de logs**:

```bash
column -s, -t < ~/labs/movimento-lateral/log_tampering.csv | less -S
```

Cada linha é um **1102** (log de segurança apagado). Anote em quais arquivos, máquinas e por quais usuários.

Agora, para ver um resultado formatado na tela, rode o Chainsaw em um único arquivo, sem `--csv`:

```bash
chainsaw hunt "EVTX-ATTACK-SAMPLES/Lateral Movement/LM_sysmon_psexec_smb_meterpreter.evtx" -s sigma/ --mapping mappings/sigma-event-logs-all.yml -r rules/
```

É o caso 2 do módulo 3 (o serviço "hello"). Repare nos nomes das regras que dispararam e compare com a sua própria análise daquele módulo.

## 7. Lab 4: quem entrou onde

O Hayabusa resume os logons de um conjunto de logs, o que responde rápido à pergunta "quem acessou esta máquina, de onde?":

```bash
cd ~/labs/EVTX-ATTACK-SAMPLES
hayabusa logon-summary -f "Lateral Movement/LM_WMI_4624_4688_TargetHost.evtx" -q
```

Compare a tabela com o que você encontrou à mão no caso 3 do módulo 3.

## Checagem

1. No lab 1, qual processo rodou o `comsvcs.dll`, qual era o processo pai e qual processo teve a memória despejada?
2. Isso foi roubo de credenciais? Justifique com o evento bruto.
3. Na regra Sigma, quais palavras precisam estar na linha de comando para ela disparar pela `selection_cli_1`?
4. No lab 2, quantas detecções de nível alto ou crítico existem, e qual a regra mais frequente?
5. Cite duas detecções críticas do lab 2 e as máquinas.
6. No lab 3, quantas vezes o log de segurança foi apagado no acervo de movimento lateral, e por quais contas?
7. Por que uma regra com `falsepositives: Unlikely` ainda pode levar a uma conclusão errada?

<details markdown="1">
<summary>Ver respostas</summary>

1. O `rundll32.exe` rodou `C:\windows\system32\comsvcs.dll, MiniDump 4868 C:\Windows\System32\notepad.bin full`. O processo pai foi o `WmiPrvSE.exe` (ou seja, foi disparado via **WMI**), e antes disso um `cscript` executou `c:\ProgramData\memdump.vbs notepad.exe`. A memória despejada foi a do processo **4868**, que o próprio script indica ser o **notepad.exe**, gravada como `notepad.bin`.
2. **Não exatamente**: a técnica é a mesma usada para roubar credenciais (despejar a memória do LSASS com uma DLL do próprio Windows), mas o alvo foi o Bloco de Notas, então não houve credencial exposta. É uma demonstração da técnica. No mundo real, você registraria como "**técnica de despejo de memória executada via WMI e script em `ProgramData`; alvo não foi o LSASS**" e escalaria do mesmo jeito: alguém está testando a técnica naquela máquina, provavelmente preparando o ataque de verdade.
3. `comsvcs` **e** `full`, **e** pelo menos uma de: `#-`, `#+`, `#24`, `24 `, `MiniDump` ou `#65560`. (Além disso, o processo precisa ser o `rundll32`.)
4. **84** detecções (76 `high` e 8 `crit`). A mais frequente é **Microsoft IIS Service Account Password Dumped** (18).
5. Por exemplo: **HackTool - Dumpert Process Dumper Default File** em `alice.insecurebank.local`; **HackTool - Mimikatz Kirbi File Creation** em `MSEDGEWIN10`; **Potential Credential Dumping Via LSASS Process Clone** em `DESKTOP-PIU87N6`.
6. **5 vezes**: por `IEUser` (PC04), `user01` (duas vezes, PC01), `administrator` (WIN-77LTAPHIQ1R) e `a-jbrown`. Repare que apagar logs aparece em vários ataques diferentes: é um hábito do atacante, não de um ataque específico.
7. Porque a regra verifica um **padrão técnico**, não a intenção nem o contexto. Ela pode acertar a técnica e o evento ser um teste autorizado, uma demonstração (como no lab 1) ou um administrador fazendo algo legítimo de um jeito incomum. A conclusão vem da sua análise do evento bruto e do contexto, não do título da regra.

</details>

!!! dica "Para ir além"
    - Rode o Hayabusa na pasta inteira do acervo (`-d .`) e use o `-T` para ver o gráfico de frequência no terminal.
    - Explore `hayabusa eid-metrics` (contagem por Event ID) e `hayabusa search -k mimikatz` (busca por palavra-chave).
    - Leia o repositório **SigmaHQ/sigma** quando tiver internet: ele é a principal fonte de regras Sigma públicas, e ler regras bem escritas ensina muito sobre técnicas de ataque.
