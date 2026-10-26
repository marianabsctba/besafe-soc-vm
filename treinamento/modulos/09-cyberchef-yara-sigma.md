<!-- descricao: Desmontar código ofuscado no CyberChef, achar arquivos com YARA e escrever sua primeira regra Sigma. -->
# Módulo 9: CyberChef, YARA e Sigma

<p class="sub">Três ferramentas que transformam o N1 de "quem lê alertas" em "quem entende o que o atacante escreveu".</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - por que atacantes **ofuscam** comandos e como desfazer isso camada por camada;
    - usar o **CyberChef** com receitas (From Base64, Gunzip, To Hex);
    - reconhecer os sinais de um **carregador em memória** sem precisar entender cada linha;
    - escrever regras **YARA** e entender `ascii`, `wide` e `nocase`;
    - escrever, validar e testar uma regra **Sigma** contra logs reais;
    - por que uma regra que "não achou nada" não está necessariamente certa.

## 1. Por que ofuscar

Um comando legível como `powershell -c "baixa_e_executa http://..."` é fácil de detectar: qualquer regra procura a palavra suspeita. Por isso atacantes **escondem** o conteúdo:

- **Base64**: transforma qualquer coisa em letras e números (`aGVsbG8=` é `hello`). Não é criptografia, é só uma "fantasia".
- **Compressão** (gzip, deflate): deixa o conteúdo binário e menor.
- **Nomes aleatórios** de funções e variáveis (`bmj90`, `qKXi`): atrapalham a leitura humana.
- **Camadas**: um código ofuscado que, ao rodar, desofusca outro, que desofusca outro.

O trabalho do analista é **descascar as camadas** até chegar a algo legível e então reconhecer **o que aquilo faz**.

!!! atencao "Regra de ouro"
    Você **decodifica**, nunca **executa**. Tudo neste módulo é análise de texto. Copiar um comando suspeito para um terminal "para ver o que acontece" é a forma mais rápida de transformar a sua estação no próximo incidente.

## 2. Lab 1: descascando o serviço "hello"

!!! cenario "Cenário"
    Lembra do caso 2 do módulo 3? O serviço **hello** executava um PowerShell escondido com um texto enorme dentro de `FromBase64String(...)`. O N2 pediu: "descubra o que aquilo faz antes de fecharmos o relatório".

### Passo 1: extraia o texto codificado

O conteúdo está dentro do evento de registro (Sysmon 13) do arquivo de log. Este comando extrai só o trecho em base64 e grava num arquivo:

```bash
mkdir -p ~/labs/09-apoio
chainsaw dump ~/labs/EVTX-ATTACK-SAMPLES/"Lateral Movement/LM_sysmon_psexec_smb_meterpreter.evtx" --json \
  | python3 -c "
import sys, json, re
for e in json.load(sys.stdin):
    texto = str((e['Event'].get('EventData') or {}).get('Details') or '')
    achou = re.search(r\"FromBase64String\('+([A-Za-z0-9+/=]{40,})\", texto)
    if achou:
        print(achou.group(1))
        break
" > ~/labs/09-apoio/camada1.txt
head -c 120 ~/labs/09-apoio/camada1.txt; echo
```

O Chainsaw mostra o seu banner e algumas mensagens na tela; é normal, elas não vão para o arquivo. Você vai ver algo começando com `H4sIA...`. Guarde essa dica: **base64 que começa com `H4sI` quase sempre é gzip**. É uma "impressão digital" que analistas reconhecem de longe.

### Passo 2: o CyberChef

Abra o **CyberChef** pelo ícone da área de trabalho. A tela tem quatro áreas:

| Área | Para quê |
|---|---|
| **Operations** (esquerda) | a lista de operações disponíveis (centenas) |
| **Recipe** (centro) | a sua receita: operações aplicadas em sequência, de cima para baixo |
| **Input** (direita, em cima) | o que entra |
| **Output** (direita, embaixo) | o resultado |

1. Abra o arquivo no editor (`mousepad ~/labs/09-apoio/camada1.txt &`), selecione tudo (`Ctrl` + `A`), copie e cole na área **Input** do CyberChef.
2. Na busca de operações, digite **From Base64** e arraste para a **Recipe**. O Output vira um monte de símbolos estranhos, começando por caracteres como `.‹`. É binário: a compressão.
3. Agora arraste **Gunzip** para baixo do From Base64. O Output vira **código PowerShell legível**.

!!! dica "A varinha mágica"
    Se você não sabe qual é a codificação, experimente a operação **Magic**: ela tenta adivinhar a receita sozinha. É um bom começo, mas confira sempre o que ela sugeriu.

### Passo 3: o mesmo no terminal

O CyberChef é ótimo para explorar. No terminal, a mesma receita é uma linha (e pode ir para o seu caderno):

```bash
base64 -d ~/labs/09-apoio/camada1.txt | gunzip > ~/labs/09-apoio/carregador.ps1
less ~/labs/09-apoio/carregador.ps1
```

### Passo 4: o que esse código faz?

Você **não** precisa entender cada linha. Precisa reconhecer padrões. Procure no código:

```bash
grep -oE "GetProcAddress|VirtualAlloc|GetDelegateForFunctionPointer|DefineDynamicAssembly|FromBase64String" ~/labs/09-apoio/carregador.ps1 | sort | uniq -c
```

| Indicador | O que significa |
|---|---|
| funções com nomes aleatórios (`bmj90`, `qKXi`) | código gerado por ferramenta para dificultar a leitura |
| `GetProcAddress` | pegar o endereço de uma função interna do Windows |
| `VirtualAlloc` | reservar um pedaço de memória (normalmente para colocar código lá) |
| `GetDelegateForFunctionPointer` | transformar um endereço de memória em algo que se pode **executar** |
| `DefineDynamicAssembly` | montar código .NET na memória, sem arquivo em disco |
| outro `FromBase64String(...)` | **mais uma camada** escondida |

Juntos, esses sinais formam um padrão clássico: um **carregador em memória** (*in-memory loader*). Ele reserva memória, coloca código de máquina lá dentro e executa, **sem gravar nada em disco**, o que dribla antivírus que só olham arquivos.

### Passo 5: a segunda camada

Procure o segundo base64:

```bash
grep -oE 'FromBase64String\("[^"]{0,40}' ~/labs/09-apoio/carregador.ps1
```

Ele começa com `/OiCAAAA...`. Copie esse trecho (só o começo já basta) para o CyberChef com a receita **From Base64** seguida de **To Hex**. O resultado começa com:

```
fc e8 82 00 00 00 60 89 e5 ...
```

Isso não é texto: é **código de máquina** (o *shellcode*). E esses primeiros bytes (`fc e8 82 00 00 00`) são o início característico do shellcode gerado pelo Metasploit. Analistas experientes reconhecem esse começo como reconhecem o `H4sI` do gzip.

A análise do shellcode em si é trabalho de N3 (engenharia reversa). O seu trabalho como N1 terminou muito bem: você provou que o serviço **hello** carregava shellcode do Metasploit na memória, e isso se conecta com a conexão para a porta **4444** que você viu no módulo 3. O caso está fechado com evidência.

## 3. YARA: encontrar arquivos pelo conteúdo

**YARA** é uma linguagem para descrever "como um arquivo malicioso se parece". Uma regra tem **strings** (o que procurar) e uma **condição** (quando considerar que achou):

```
rule carregador_powershell_memoria
{
    meta:
        descricao = "PowerShell que reserva memoria e executa codigo nela"
        autor = "Treinamento Be Safe"

    strings:
        $a = "GetProcAddress"
        $b = "VirtualAlloc"
        $c = "GetDelegateForFunctionPointer"
        $d = "FromBase64String"

    condition:
        3 of them
}
```

A condição `3 of them` exige pelo menos três das quatro strings. Exigir **combinações** em vez de uma única palavra reduz falsos positivos: `FromBase64String` sozinho aparece em muito script legítimo.

### Lab 2: sua primeira regra

Crie o arquivo:

```bash
mousepad ~/labs/09-apoio/carregador.yar &
```

Cole a regra acima, salve e rode:

```bash
yara ~/labs/09-apoio/carregador.yar ~/labs/09-apoio/
```

A YARA vai apontar **dois** arquivos: o `carregador.ps1`, como esperado, e o próprio `carregador.yar`. A regra casou consigo mesma, porque o arquivo da regra contém as palavras que ela procura! É um clássico: guarde regras YARA longe das pastas que você varre, ou o resultado fica poluído.

Agora teste a regra contra algo que **não** deveria disparar:

```bash
yara -r ~/labs/09-apoio/carregador.yar /usr/share/doc/ | head
```

Nenhum resultado é o esperado: a documentação do sistema não tem esse padrão.

### Lab 3: a armadilha do `wide`

Logs do Windows (`.evtx`) guardam texto em **UTF-16**: cada letra ocupa dois bytes (`m\0i\0m\0i\0...`). Uma regra que procura `"mimikatz"` em texto comum (ASCII) **não enxerga** esse formato.

```bash
cat > ~/labs/09-apoio/mimikatz-ascii.yar <<'EOF'
rule mimikatz_ascii { strings: $a = "mimikatz" nocase condition: $a }
EOF
cat > ~/labs/09-apoio/mimikatz-wide.yar <<'EOF'
rule mimikatz_ascii_wide { strings: $a = "mimikatz" nocase ascii wide condition: $a }
EOF
yara -r ~/labs/09-apoio/mimikatz-ascii.yar ~/labs/EVTX-ATTACK-SAMPLES/ | wc -l
yara -r ~/labs/09-apoio/mimikatz-wide.yar ~/labs/EVTX-ATTACK-SAMPLES/ | wc -l
```

| Modificador | Efeito |
|---|---|
| `nocase` | ignora maiúsculas e minúsculas |
| `ascii` | procura em texto comum (é o padrão) |
| `wide` | procura em UTF-16 (dois bytes por letra) |

Compare os dois números. Depois veja **quais** arquivos a regra `wide` encontrou:

```bash
yara -r ~/labs/09-apoio/mimikatz-wide.yar ~/labs/EVTX-ATTACK-SAMPLES/
```

Repare que nem todos são logs: aparecem também um arquivo de índice do `.git`, um notebook e o CSV do catálogo. A YARA faz exatamente o que você pediu, inclusive nos lugares em que você não queria procurar. Delimite a busca:

```bash
find ~/labs/EVTX-ATTACK-SAMPLES/ -name "*.evtx" -exec yara ~/labs/09-apoio/mimikatz-wide.yar {} \;
```

## 4. Sigma: a sua primeira regra de detecção

No módulo 7 você **leu** uma regra Sigma. Agora vai **escrever** uma, validar e testar contra logs reais. É o ciclo da engenharia de detecção em miniatura.

### Lab 4: PowerShell escondido

```bash
mkdir -p ~/labs/09-apoio/regras
mousepad ~/labs/09-apoio/regras/powershell_oculto.yml &
```

Cole:

```yaml
title: PowerShell oculto e sem perfil
id: 6f1c2a64-3b0e-4f63-9a52-0d6c1e5a7b10
status: experimental
description: PowerShell iniciado com janela oculta e sem perfil, padrao comum de execucao maliciosa
author: Treinamento Be Safe
date: 2026-10-26
tags:
    - attack.execution
    - attack.t1059.001
logsource:
    category: process_creation
    product: windows
detection:
    selecao:
        Image|endswith: '\powershell.exe'
        CommandLine|contains|all:
            - '-w hidden'
            - '-nop'
    condition: selecao
falsepositives:
    - Scripts administrativos legitimos que escondem a janela
level: high
```

!!! atencao "YAML é sensível a espaços"
    A indentação (os espaços no começo das linhas) faz parte da sintaxe. Use espaços, nunca Tab, e mantenha os níveis alinhados como no exemplo.

Valide a sintaxe:

```bash
sigma check ~/labs/09-apoio/regras/
```

O resultado esperado é `Found 0 errors`. Agora teste contra o caso do serviço **hello**:

```bash
cd /opt/besafe/chainsaw
chainsaw hunt "EVTX-ATTACK-SAMPLES/Lateral Movement/LM_sysmon_psexec_smb_meterpreter.evtx" -s ~/labs/09-apoio/regras/ --mapping mappings/sigma-event-logs-all.yml
```

A sua regra deve encontrar os dois PowerShell escondidos daquele ataque. E no acervo inteiro?

```bash
chainsaw hunt EVTX-ATTACK-SAMPLES/ -s ~/labs/09-apoio/regras/ --mapping mappings/sigma-event-logs-all.yml
```

### A regra é boa?

Ela encontrou os mesmos dois eventos, e mais nenhum no acervo. Isso quer dizer que ela é boa? **Não necessariamente.** Pense como o atacante: o PowerShell aceita várias grafias para a mesma opção. `-w hidden`, `-W Hidden`, `-WindowStyle Hidden`, `-win hidden` e até `-w 1` fazem a mesma coisa. A sua regra só pega a primeira (o Sigma ignora maiúsculas no `contains`, então `-W Hidden` também passa, mas `-WindowStyle Hidden` não).

Uma versão mais robusta troca o "todos" por "qualquer um" e lista as variações:

```yaml
detection:
    selecao_imagem:
        Image|endswith: '\powershell.exe'
    selecao_oculto:
        CommandLine|contains:
            - '-w hidden'
            - '-w 1'
            - '-win hidden'
            - '-window hidden'
            - '-windowstyle hidden'
            - '-wi h'
    condition: selecao_imagem and selecao_oculto
```

Se você testar essa versão no acervo, ela também vai encontrar só os dois eventos. **O acervo não tem as outras grafias.** Essa é a lição final do módulo: testar uma regra exige **casos positivos conhecidos**. "Não achou nada" não prova que a regra é boa, só que não havia nada que ela soubesse reconhecer. Engenheiros de detecção mantêm coleções de exemplos de cada variação justamente por isso.

## Checagem

1. O que indica um texto em base64 que começa com `H4sI`?
2. Qual receita do CyberChef transformou a camada 1 em PowerShell legível?
3. Cite três indicadores que mostram que o código é um carregador em memória.
4. O que eram os bytes `fc e8 82 00 00 00`, e como isso se conecta com o módulo 3?
5. Por que a regra YARA usa `3 of them` em vez de procurar só `FromBase64String`?
6. Quantos arquivos a regra `ascii` encontrou, e quantos a `wide`? Por que a diferença?
7. Por que "minha regra Sigma não encontrou nada no acervo inteiro" não prova que ela está certa?

<details markdown="1">
<summary>Ver respostas</summary>

1. Que o conteúdo, depois de decodificado, é um arquivo **gzip** (os bytes iniciais do gzip, `1f 8b 08`, viram `H4sI` em base64).
2. **From Base64** seguido de **Gunzip**.
3. Quaisquer três entre: nomes de função aleatórios; `GetProcAddress`; `VirtualAlloc`; `GetDelegateForFunctionPointer`; `DefineDynamicAssembly`; uma segunda camada em base64.
4. São o início de um **shellcode** (código de máquina), com a assinatura típica do Metasploit. Ele se conecta à conexão do `powershell.exe` para a porta **4444** do módulo 3: o carregador colocou o shellcode na memória e o shellcode abriu o canal com o atacante.
5. Porque `FromBase64String` sozinho aparece em muitos scripts legítimos. Exigir a **combinação** de vários sinais reduz falsos positivos.
6. **3** com `ascii` e **8** com `ascii wide`. Os logs `.evtx` guardam texto em UTF-16, que só o `wide` enxerga. Dos 8, só **4** são arquivos `.evtx` (o `find` mostra); os outros são um `.etl`, o `.git/index`, o notebook e o CSV do catálogo.
7. Porque o acervo pode simplesmente não ter as variações que a regra deixaria escapar. Para avaliar uma regra, é preciso testá-la contra exemplos positivos conhecidos de cada variação, e contra dados normais para medir falsos positivos.

</details>

!!! dica "Para ir além"
    - Explore a operação **Defang URL** do CyberChef: ela transforma `http://site.com` em `hxxp://site[.]com`, o jeito seguro de colocar links maliciosos em tickets (ninguém clica sem querer).
    - Leia o repositório **Yara-Rules** e as regras do projeto **signature-base** (Florian Roth) quando tiver internet: são ótimos exemplos de regras bem escritas.
    - Experimente o `sigma list targets` e pesquise como o `sigma convert` transforma uma regra Sigma na linguagem de um SIEM específico.
