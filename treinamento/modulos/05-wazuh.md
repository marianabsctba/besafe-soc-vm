<!-- descricao: O SIEM na prática: gere eventos de verdade, encontre os alertas e leia cada campo. -->
# Módulo 5: Wazuh na prática

<p class="sub">Você vai atacar a sua própria VM (com segurança) e ver, do outro lado, o SIEM percebendo.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - o que o Wazuh faz e de onde vêm os alertas;
    - navegar no painel: Threat Hunting, MITRE ATT&CK e Rules;
    - filtrar alertas por regra, nível e campo;
    - ler um alerta inteiro, campo por campo;
    - entender o que é uma **regra de correlação** (vários eventos viram um alerta mais grave);
    - diferenciar alerta de **ataque** de alerta de **configuração**.

## 1. Como o Wazuh funciona

```
 logs da máquina ──▶ DECODIFICADOR ──▶ REGRAS ──▶ alerta (com nível) ──▶ INDEXER ──▶ painel
 (auth, journald,     "que tipo de       "isso é     de 0 a 15             (guarda      (onde você
  Suricata...)         linha é essa?"     suspeito?"                        e indexa)    investiga)
```

1. **Coleta**: o Wazuh lê logs (nesta VM: o journald do sistema, o log do dpkg, o `eve.json` do Suricata).
2. **Decodificação**: cada linha passa por um *decoder* que reconhece o formato e extrai campos (usuário, IP de origem, programa).
3. **Regras**: milhares de regras avaliam os campos. Cada regra tem um **ID**, uma **descrição**, um **nível** (0 a 15) e, muitas vezes, a técnica do **MITRE ATT&CK**.
4. **Alerta**: se uma regra casa, nasce um alerta, guardado no indexer e mostrado no painel.

### Os níveis

| Nível | Leitura prática |
|---|---|
| 0 a 3 | informativo; registros de rotina |
| 4 a 7 | atenção: erros, falhas isoladas, mudanças de sistema |
| 8 a 11 | importante: ações sensíveis, padrões de ataque |
| 12 a 15 | grave: alta probabilidade de ataque ou impacto |

## 2. Tour pelo painel

Abra o Wazuh (`https://localhost`, usuário `admin`, senha em `~/.besafe/wazuh.txt` ou no arquivo **CREDENCIAIS** da área de trabalho). No menu principal (o ícone ☰ no canto superior esquerdo):

| Caminho | Para quê |
|---|---|
| **Threat intelligence > Threat Hunting** | o lugar principal do analista: a aba de painel resume os alertas; a aba **Events** lista cada alerta, com busca e filtros |
| **Threat intelligence > MITRE ATT&CK** | os alertas organizados por tática e técnica |
| **Endpoint security > Configuration Assessment** | verificação de configuração segura (CIS); gera alertas de conformidade |
| **Server management > Rules** | todas as regras: pesquise pelo ID para ver o que cada uma verifica |

!!! atencao "Interfaces mudam"
    O Wazuh atualiza a interface de tempos em tempos. Se algum nome de menu estiver um pouco diferente na sua tela, procure pela função (alertas, eventos, regras). Os conceitos e os campos do alerta não mudam.

### Buscando e filtrando

Na aba **Events** do Threat Hunting existe uma barra de busca. Ela aceita consultas no formato `campo:valor`:

| Consulta | O que mostra |
|---|---|
| `rule.id:5712` | só os alertas da regra 5712 |
| `rule.level >= 10` | alertas de nível 10 para cima |
| `rule.groups:authentication_failures` | todas as falhas de autenticação |
| `data.srcip:127.0.0.1` | alertas com esse IP de origem |
| `rule.mitre.id:T1110` | alertas mapeados para a técnica Brute Force |

Ajuste também o **intervalo de tempo** (no canto superior direito). Um erro clássico é procurar um alerta de hoje com o filtro em "últimos 15 minutos".

## 3. Lab: ataque a si mesmo

!!! cenario "Cenário"
    O seu líder quer ter certeza de que você sabe encontrar e interpretar alertas antes de assumir a fila. Você vai gerar três tipos de evento na sua própria VM e encontrar cada um no Wazuh.

!!! atencao "Isto é seguro?"
    Sim. Tudo acontece dentro da sua VM, contra ela mesma, e no final você desfaz o que criou. É exatamente assim que equipes de detecção testam se as regras funcionam.

### Evento 1: senha errada no sudo

No terminal:

```bash
sudo -k
sudo ls /root    # digite a senha ERRADA
sudo -k
sudo ls /root    # ERRADA de novo
sudo ls /root    # agora a certa
```

No Wazuh (Threat Hunting > Events), procure:

```
rule.id:5401
```

Você deve encontrar **Failed attempt to run sudo**, regra **5401**, nível **5**, com a técnica **T1548.003** (Sudo and Sudo Caching). Abra o alerta (clique na seta ao lado da linha) e encontre o usuário e a linha original do log (`full_log`).

### Evento 2: um usuário novo

```bash
sudo useradd -m lab-temp
```

Procure:

```
rule.id:5902
```

**New user added to the system**, regra **5902**, nível **8**, técnica **T1136** (Create Account). Por que o nível é maior que o do sudo errado? Porque criar conta é uma das formas clássicas de **persistência**: o atacante garante uma porta de volta.

### Evento 3: força bruta no SSH

O SSH vem desligado nesta VM (ninguém de fora precisa acessá-la). Ligue só para o lab:

```bash
sudo systemctl start ssh
```

Agora simule um atacante testando nomes de usuário que não existem:

```bash
for i in $(seq 1 10); do
  ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=3 hacker$i@127.0.0.1 true
done
```

Cada tentativa vai falhar (é o esperado). Aguarde uns 30 segundos e procure no Wazuh:

```
rule.id:5710 or rule.id:5712
```

Você vai ver:

- vários **sshd: Attempt to login using a non-existent user** (regra **5710**, nível **5**), um por tentativa;
- **um** alerta **sshd: brute force trying to get access to the system. Non existent user.** (regra **5712**, nível **10**).

### O que aconteceu: correlação

A regra 5712 não olha um evento: ela olha **vários**. Em **Server management > Rules**, procure a regra 5712 e veja a definição: ela dispara quando a regra 5710 acontece **8 vezes** (`frequency`) **do mesmo IP** num intervalo curto (`timeframe`). Muitos eventos pequenos, de nível 5, viram **um** alerta de nível 10.

Isso é **correlação**, e é o que transforma ruído em sinal. Uma tentativa de login com usuário inexistente pode ser um erro de digitação. Oito em um minuto, do mesmo IP, é um robô tentando nomes.

Desligue o SSH e remova o usuário de teste:

```bash
sudo systemctl stop ssh ssh.socket
sudo userdel -r lab-temp
```

## 4. Lendo um alerta inteiro

Abra o alerta da regra 5712 e veja os campos. Ou, no terminal, veja o último alerta de nível 10 ou mais em formato bruto:

```bash
sudo tail -n 500 /var/ossec/logs/alerts/alerts.json | jq -c 'select(.rule.level >= 10)' | tail -n 1 | jq .
```

Campos que você precisa saber ler:

| Campo | Exemplo | Significado |
|---|---|---|
| `rule.id` / `rule.description` | `5712` / brute force... | qual regra disparou |
| `rule.level` | `10` | gravidade estimada |
| `rule.groups` | `sshd`, `authentication_failures` | categorias (ótimas para filtrar) |
| `rule.mitre.tactic` / `technique` | Credential Access / Brute Force | o "porquê" e o "como" do ATT&CK |
| `rule.frequency` | `8` | quantos eventos a correlação exigiu |
| `data.srcip` / `data.srcuser` | `127.0.0.1` / `hacker8` | de onde veio e qual usuário foi tentado |
| `full_log` | `sshd[...]: Invalid user hacker8 from 127.0.0.1 port ...` | **a linha original**: sempre confira |
| `location` | `journald` | de qual log o evento veio |
| `decoder.name` | `sshd` | qual decodificador interpretou a linha |
| `rule.pci_dss`, `gdpr`, `hipaa`... | | normas de conformidade relacionadas |

!!! erro "Erro comum de N1"
    Confiar só na descrição e no nível. O `full_log` é a evidência; o resto é a interpretação da regra. Em todo alerta que você for escalar, copie o `full_log` para o ticket.

## 5. Alerta de ataque ou de configuração?

Volte ao Threat Hunting e olhe **todos** os alertas da última hora (sem filtro). Além dos que você gerou, provavelmente vai ver vários **CIS Ubuntu Linux 24.04 LTS Benchmark...** com nível 9, e talvez alertas de pacote instalado.

Eles vêm do **Configuration Assessment** (SCA): o Wazuh compara a configuração da máquina com um padrão de segurança (o CIS Benchmark) e avisa quando algo muda. Quando você ligou o SSH, ele passou a verificar a configuração do SSH, e vários itens "falharam".

Isso **não** é um ataque: é um alerta de **postura** (a configuração poderia ser mais segura). Mas repare que o nível 9 é **mais alto** que o do sudo errado. Num SOC real, se você ordenar a fila só por nível, vai passar a manhã olhando conformidade enquanto uma tentativa de acesso espera. Por isso:

- separe mentalmente (e com filtros) **alertas de detecção** de **alertas de conformidade**;
- use `rule.groups` e `rule.mitre` para focar no que é comportamento de atacante;
- conformidade importa, mas costuma ir para outra fila (a equipe de infraestrutura ou de GRC).

## Checagem

1. Quais são as quatro etapas do caminho de um log até virar alerta no Wazuh?
2. Qual regra e nível apareceram para o sudo com senha errada? E para o usuário novo? Por que níveis diferentes?
3. O que é uma regra de correlação? Explique com a 5712.
4. Qual campo do alerta é a evidência original?
5. Os alertas CIS de nível 9 indicam um ataque? Como você os trataria?
6. Você procura um alerta que gerou há 2 horas e não encontra. Qual a primeira coisa a verificar?

<details markdown="1">
<summary>Ver respostas</summary>

1. Coleta do log, decodificação (extração de campos), avaliação pelas regras e geração do alerta (guardado no indexer e exibido no painel).
2. Sudo errado: regra **5401**, nível **5**. Usuário novo: regra **5902**, nível **8**. Criar conta é uma técnica de persistência (o atacante garante acesso futuro), mais grave que uma senha errada isolada.
3. Uma regra que dispara a partir de **vários** eventos de outra regra. A 5712 dispara quando a 5710 (login com usuário inexistente) acontece 8 vezes do mesmo IP num curto intervalo, gerando um alerta de nível 10.
4. O `full_log`, a linha original do log.
5. Não. São alertas de conformidade (a configuração do SSH não segue o CIS Benchmark). Devem ser registrados e encaminhados à equipe responsável pela configuração, separados da fila de detecção de ataques.
6. O **intervalo de tempo** do painel. Depois, se o filtro está correto (campo e valor) e se o evento realmente gerou um alerta (veja o `alerts.json` no terminal).

</details>

!!! dica "Para ir além"
    - Em **Server management > Ruleset Test**, cole uma linha de log (por exemplo, um `Invalid user` do `auth.log`) e veja qual decodificador e qual regra o Wazuh aplicaria. É o melhor jeito de entender por que um alerta disparou ou não.
    - Explore o painel **MITRE ATT&CK** depois dos labs: as técnicas T1110, T1136 e T1548 devem aparecer.
