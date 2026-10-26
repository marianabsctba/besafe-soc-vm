<!-- descricao: Navegar, ler e filtrar arquivos no terminal: a base de toda investigação. -->
# Módulo 1: Terminal Linux

<p class="sub">O terminal assusta no começo. Depois de uma semana, você não vai querer outra coisa.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - o que é o terminal e por que analistas o usam tanto;
    - andar pelas pastas do sistema e entender caminhos;
    - ler arquivos grandes sem se perder;
    - procurar texto com `grep`;
    - encadear comandos com `|` (o "superpoder" do analista);
    - contar e ranquear ocorrências: *quais são os valores mais comuns neste log?*;
    - entender quando e por que usar `sudo`.

## 1. Por que terminal, se existe interface gráfica?

Porque **logs são texto**, e muito texto. Um servidor movimentado gera milhões de linhas por dia. Nenhuma planilha abre isso confortavelmente, mas o terminal filtra, conta e ordena milhões de linhas em segundos. Além disso:

- muitos servidores **não têm** interface gráfica;
- comandos podem ser repetidos, guardados no caderno e compartilhados com a equipe;
- quase toda ferramenta de segurança séria tem uma versão de linha de comando.

## 2. Anatomia de um comando

```
ls  -l  /var/log
│    │       └── argumento: sobre o que o comando age
│    └── opção: muda o comportamento (começa com - ou --)
└── comando: o programa que vai rodar
```

Para saber o que um comando faz, use o manual: `man ls` (saia com a tecla `q`). Ou a ajuda curta: `ls --help`.

!!! dica "Atalhos que salvam tempo"
    - `Tab` completa nomes de arquivos e pastas. Aperte duas vezes para ver as opções.
    - `↑` e `↓` navegam pelos comandos que você já digitou.
    - `Ctrl` + `C` interrompe um comando que está demorando ou travado.
    - `Ctrl` + `L` limpa a tela.
    - `history` mostra tudo o que você digitou na sessão.

## 3. Onde estou? O sistema de arquivos

No Linux, tudo fica numa única árvore que começa em `/` (a "raiz"). Algumas pastas que você vai visitar muito:

| Pasta | O que tem lá |
|---|---|
| `/home/analista` | a sua pasta pessoal, também escrita como `~` |
| `/var/log` | os logs do sistema |
| `/etc` | arquivos de configuração |
| `/opt/besafe` | as ferramentas do treinamento |
| `/tmp` | arquivos temporários (somem ao reiniciar) |

Três comandos para se orientar:

```bash
pwd                 # mostra a pasta em que você está
ls                  # lista o conteúdo da pasta
cd /var/log         # entra na pasta /var/log
```

Teste agora: rode `pwd`, depois `cd /var/log`, depois `pwd` de novo, depois `ls`.

### Caminho absoluto e caminho relativo

- **Absoluto** começa em `/` e funciona de qualquer lugar: `/opt/besafe/chainsaw`.
- **Relativo** parte de onde você está: se você está em `/opt/besafe`, basta `cd chainsaw`.
- `..` significa "a pasta de cima" e `.` significa "a pasta atual". `cd ..` sobe um nível. `cd ~` (ou só `cd`) volta para casa.

### Nomes com espaço

Um nome como `Credential Access` tem um espaço. Para o terminal, espaço separa argumentos, então ele entenderia "Credential" e "Access" como duas coisas. Use aspas: `cd "Credential Access"`. Ou deixe o `Tab` completar, que ele resolve sozinho.

## 4. Listar com detalhes

```bash
ls -la /var/log
```

- `-l` mostra detalhes (permissões, dono, tamanho, data);
- `-a` mostra também os arquivos ocultos (os que começam com `.`).

Uma linha típica:

```
-rw-r----- 1 syslog adm 465339 Oct 26 08:52 syslog
```

| Parte | Significado |
|---|---|
| `-rw-r-----` | tipo e permissões (`-` arquivo, `d` pasta; depois leitura `r`, escrita `w`, execução `x` para dono, grupo e outros) |
| `syslog` | dono do arquivo |
| `adm` | grupo do arquivo |
| `465339` | tamanho em bytes (use `ls -lh` para ver em KB/MB) |
| `Oct 26 08:52` | última modificação |

Repare que "outros" não têm permissão nenhuma (`---`). Por isso você, que não é dono nem do grupo `adm`, não consegue ler esse arquivo sem `sudo`. Logs têm permissão restrita de propósito: eles contêm nomes de usuário, IPs e às vezes até dados sensíveis.

## 5. Ler arquivos

| Comando | Quando usar |
|---|---|
| `cat arquivo` | arquivos pequenos: mostra tudo de uma vez |
| `less arquivo` | arquivos grandes: rola com as setas, `/palavra` busca, `q` sai |
| `head -n 20 arquivo` | as primeiras 20 linhas |
| `tail -n 20 arquivo` | as últimas 20 linhas |
| `tail -f arquivo` | acompanha o arquivo **ao vivo** enquanto ele cresce (`Ctrl` + `C` para parar) |
| `wc -l arquivo` | conta as linhas |

!!! erro "Erro comum de N1"
    Dar `cat` num log de 2 GB. O terminal trava despejando texto por minutos. Antes de abrir um arquivo, olhe o tamanho (`ls -lh`) e comece com `head`, `tail` ou `less`.

## 6. Procurar texto com grep

`grep` mostra só as linhas que contêm o que você procura.

```bash
grep "palavra" arquivo        # linhas com "palavra"
grep -i "palavra" arquivo     # ignorando maiúsculas e minúsculas
grep -c "palavra" arquivo     # só conta quantas linhas têm
grep -v "palavra" arquivo     # o contrário: linhas SEM a palavra
grep -r "palavra" pasta/      # procura em todos os arquivos da pasta
```

## 7. O pipe: o superpoder

O `|` (pipe) pega a saída de um comando e entrega como entrada para o próximo. Com ele você monta "linhas de produção" de dados:

```bash
comando1 | comando2 | comando3
```

A combinação mais importante da vida de um analista é esta:

```bash
... | sort | uniq -c | sort -nr | head
```

| Etapa | O que faz |
|---|---|
| `sort` | ordena as linhas, para que as iguais fiquem juntas |
| `uniq -c` | junta as linhas iguais vizinhas e conta quantas são |
| `sort -nr` | ordena pelo número (`-n`), do maior para o menor (`-r`) |
| `head` | mostra só as 10 primeiras |

Resultado: **um ranking**. Quais IPs mais tentaram logar? Quais usuários mais falharam? Quais regras mais dispararam? Essa pergunta aparece todo dia no SOC, e essa linha responde.

Para extrair uma coluna antes de ranquear, use `cut`: `cut -d, -f3` pega o terceiro campo de cada linha, usando a vírgula como separador.

## 8. Lab: explorando um acervo de ataques reais

!!! cenario "Cenário"
    O seu líder de turno pediu: "Antes de começar nos plantões, dá uma olhada no acervo de logs de ataque que a gente usa para treinar. Quero que você me diga quantos arquivos tem, quais táticas aparecem mais, e qual é o tipo de evento mais comum."

    O acervo é o EVTX-ATTACK-SAMPLES, que está na VM. Cada arquivo `.evtx` é um log de Windows gravado durante um ataque, e as pastas são organizadas por **tática** (o "objetivo" do atacante naquela etapa, segundo o MITRE ATT&CK, que você verá no módulo 5).

### Passo 1: chegue lá e olhe em volta

```bash
cd /opt/besafe/chainsaw/EVTX-ATTACK-SAMPLES
pwd
ls
```

Você vai ver pastas como `Credential Access`, `Lateral Movement`, `Persistence`, além de alguns arquivos soltos (um `README.md`, um `evtx_data.csv`, imagens).

### Passo 2: quantos arquivos de log existem?

`ls` não entra nas subpastas. Para procurar em todas, use `find`:

```bash
find . -name "*.evtx"
find . -name "*.evtx" | wc -l
```

O primeiro lista todos os arquivos `.evtx`. O segundo conta.

### Passo 3: quantos por tática?

Entre em uma pasta e conte:

```bash
ls "Credential Access" | wc -l
find "Credential Access" -name "*.evtx" | wc -l
```

Os dois números dão diferente! Investigue com `ls "Credential Access"` e descubra por quê.

### Passo 4: procure pelo nome

O `lsass.exe` é o processo do Windows que guarda as credenciais de quem está logado. Ele é o alvo preferido de quem quer roubar senhas (você vai entender isso no módulo 3). Quantos arquivos do acervo têm "lsass" no nome?

```bash
find . -iname "*lsass*"
find . -iname "*lsass*" | wc -l
```

O `-iname` ignora maiúsculas e minúsculas, ao contrário do `-name`.

### Passo 5: o catálogo em CSV

O arquivo `evtx_data.csv` descreve todos os eventos do acervo, um por linha, com colunas separadas por vírgula.

```bash
ls -lh evtx_data.csv
head -n 3 evtx_data.csv
wc -l evtx_data.csv
```

A primeira linha é o cabeçalho com o nome das colunas. Olhe com atenção: a coluna 3 é `Channel` (de qual log do Windows o evento veio) e a coluna 7 é `EventID` (o tipo do evento).

### Passo 6: o ranking

Quais canais de log aparecem mais?

```bash
cut -d, -f3 evtx_data.csv | sort | uniq -c | sort -nr | head
```

E quais tipos de evento?

```bash
cut -d, -f7 evtx_data.csv | sort | uniq -c | sort -nr | head
```

!!! atencao "Tem coisa estranha no resultado"
    Você vai ver, misturadas com valores que fazem sentido, linhas em branco e textos como `%%4423`. Não é erro seu. Leia a seção seguinte antes de seguir.

### Passo 7: dados reais são sujos

O `wc -l` disse que o arquivo tem milhares de linhas. Mas o catálogo tem bem menos **eventos** do que linhas. Por quê?

Alguns campos do CSV contêm textos longos **com quebras de linha dentro**, protegidos por aspas. Para um leitor de CSV de verdade, aquilo é um campo só. Para o `cut`, que não conhece aspas, cada quebra de linha começa uma "linha nova", e ele pega o terceiro pedaço de um texto que nem é uma coluna. Daí o lixo.

Isso não é um detalhe acadêmico. No SOC você vai receber exportações de sistemas diferentes, e muitas vão ter esse tipo de armadilha. Duas lições:

1. **Desconfie de resultados que parecem bons demais ou estranhos demais.** Olhe o dado bruto (`head`, `less`) antes de confiar num número.
2. **Use a ferramenta certa para o formato.** Para CSV complexo, um leitor de CSV. Uma linha de Python resolve:

```bash
python3 -c "import csv,collections; r=csv.DictReader(open('evtx_data.csv')); print(collections.Counter(x['Channel'] for x in r).most_common(5))"
```

Compare com o resultado do `cut`. Os valores do topo batem, mas agora sem lixo.

### Passo 8: um log ao vivo, com você como protagonista

Os passos anteriores leram arquivos parados. Agora você vai ver um log crescendo em tempo real, e os eventos vão ser **as suas próprias ações**.

O `/var/log/auth.log` registra tudo que envolve autenticação na máquina: logins, uso de `sudo`, falhas de senha. Tente ler as últimas linhas:

```bash
ls -l /var/log/auth.log
tail -n 5 /var/log/auth.log
```

Você vai receber **`Permission denied`** (permissão negada). Olhe de novo a saída do `ls -l`: o arquivo pertence ao usuário `syslog` e ao grupo `adm`, e "outros" não têm permissão nenhuma. Você não é nenhum dos dois.

## 9. sudo: poder com responsabilidade

`sudo` executa um comando como **administrador** (o usuário `root`). Ele pede a sua senha (`analista`). Use `sudo` só quando precisar, e entenda o comando antes de rodar.

Agora sim, acompanhe o log ao vivo:

```bash
sudo tail -f /var/log/auth.log
```

Deixe rodando. Abra outra aba do terminal (`Ctrl` + `Shift` + `T`) e faça três coisas:

```bash
sudo -k            # "esquece" que você já digitou a senha
sudo ls /root      # quando pedir a senha, DIGITE ERRADO de propósito
sudo ls /root      # agora digite a senha certa
```

Volte para a primeira aba. Você vai ver aparecer, mais ou menos assim:

```
... sudo: pam_unix(sudo:auth): authentication failure; logname=analista uid=1000 euid=0 tty=/dev/pts/1 ruser=analista rhost=  user=analista
... sudo: analista : 1 incorrect password attempt ; TTY=pts/1 ; PWD=/home/analista ; USER=root ; COMMAND=/usr/bin/ls /root
... sudo: analista : TTY=pts/1 ; PWD=/home/analista ; USER=root ; COMMAND=/usr/bin/ls /root
... sudo: pam_unix(sudo:session): session opened for user root(uid=0) by analista(uid=1000)
... sudo: pam_unix(sudo:session): session closed for user root
```

Leia linha por linha:

| Linha | O que aconteceu |
|---|---|
| `authentication failure ... user=analista` | alguém, como `analista`, errou a senha do sudo |
| `1 incorrect password attempt ; ... COMMAND=/usr/bin/ls /root` | o resumo da tentativa que falhou, **incluindo o comando que a pessoa queria rodar** |
| `analista : TTY=pts/1 ; ... COMMAND=/usr/bin/ls /root` | agora deu certo, e o log registra exatamente qual comando rodou como root |
| `session opened` / `session closed` | a sessão de administrador abriu e fechou |

!!! atencao "TTY e PWD"
    `TTY=pts/1` diz de qual terminal veio o comando (um terminal gráfico ou uma sessão SSH; cada um ganha um número). `PWD` é a pasta em que a pessoa estava. Num incidente real, esses detalhes ajudam a separar o que foi feito numa sessão do que foi feito em outra.

Pare o `tail` com `Ctrl` + `C`.

Repare no que você acabou de fazer: gerou um evento, encontrou-o no log e interpretou cada campo. É o ciclo inteiro de uma investigação, em miniatura.

!!! atacante "Como o atacante pensa"
    Para um atacante que invadiu uma conta comum, conseguir rodar comandos como `root` é a "chave mestra" do servidor. Essa etapa se chama **escalação de privilégio**. Por isso tentativas de `sudo` negadas, usuários novos no grupo `sudo` e alterações em `/etc/sudoers` são eventos que o SOC monitora de perto.

## Checagem

1. Qual o total de arquivos `.evtx` no acervo?
2. No passo 3, por que `ls | wc -l` e `find -name "*.evtx" | wc -l` deram números diferentes em `Credential Access`?
3. Quantos arquivos têm "lsass" no nome?
4. Qual canal de log aparece mais no catálogo? E qual o segundo?
5. Qual o Event ID mais comum? (Dica: ignore as linhas que não são números.)
6. Por que o `cut` mostrou linhas estranhas no passo 6?
7. Para que serve o `-f` em `tail -f`, e por que ele é útil no SOC?
8. No passo 8, por que você não conseguiu ler o `auth.log` sem `sudo`?
9. Imagine que, num servidor, o `auth.log` mostre dez `authentication failure` de sudo seguidos para o usuário `estagiario`, e depois um `COMMAND=/bin/bash`. O que isso sugere?

<details markdown="1">
<summary>Ver respostas</summary>

1. **278** arquivos `.evtx`.
2. Porque a pasta tem um arquivo que não é `.evtx` (um `.etl`, outro formato de log do Windows). O `ls` conta tudo, o `find -name "*.evtx"` conta só os `.evtx`. Moral: sempre se pergunte **o que exatamente** o seu comando está contando.
3. **8** arquivos.
4. `Microsoft-Windows-Sysmon/Operational` (2401 eventos), seguido de `Security` (1496). O Sysmon é uma ferramenta da Microsoft que registra em detalhe o que os processos fazem. Você vai conhecê-lo no módulo 3.
5. O **5145** (950 ocorrências): acesso a um arquivo compartilhado na rede. Faz sentido: a tática com mais eventos no acervo é Lateral Movement, e o atacante se movendo entre máquinas acessa muitos compartilhamentos.
6. Porque alguns campos do CSV têm quebras de linha dentro de aspas. O `cut` não entende aspas e trata cada quebra como uma linha nova.
7. O `-f` ("follow") mantém o arquivo aberto e mostra as linhas novas assim que elas são escritas. No SOC serve para acompanhar ao vivo o que acontece enquanto você reproduz ou investiga algo.
8. Porque o arquivo pertence a `syslog`/`adm` e não dá permissão nenhuma a "outros". Logs de autenticação contêm nomes de usuário, IPs e horários de acesso: informação que um atacante adoraria ter, então o acesso é restrito.
9. Alguém (ou algo) tentou várias senhas no sudo até acertar e então abriu um **shell de root** (`/bin/bash` como administrador). Pode ser o próprio estagiário que esqueceu a senha, mas também pode ser uma conta comprometida tentando escalar privilégio. O que muda a análise: o estagiário costuma usar sudo? Estava trabalhando nesse horário? De onde veio o login dele? Esse é o tipo de caso que você **registra com todos os horários e escala**, em vez de concluir sozinho.

</details>

!!! dica "Para ir além"
    - Faça o desafio de terminal **OverTheWire Bandit** (níveis 0 a 15) quando tiver acesso à internet. É gratuito e ensina exatamente o que um analista precisa.
    - Aprenda `awk` para extrair colunas por espaço: `awk '{print $1}' arquivo` imprime a primeira palavra de cada linha.
    - Experimente o desafio extra do Suricata: quantas regras existem em `/var/lib/suricata/rules/suricata.rules`? E quais categorias (`classtype`) são as mais comuns? Monte o ranking com `grep -o 'classtype:[^;]*'` e a linha de produção do item 7.
