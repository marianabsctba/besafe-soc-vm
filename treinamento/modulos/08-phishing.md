<!-- descricao: Cabeçalhos, SPF/DKIM/DMARC, links disfarçados, PDFs e macros: analisar e-mail suspeito sem abrir nada. -->
# Módulo 8: Analisando phishing

<p class="sub">A maioria dos ataques começa com uma mensagem. O N1 que lê bem um e-mail para o ataque antes de ele começar.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - reconhecer os tipos de phishing mais comuns no Brasil;
    - ler cabeçalhos de e-mail, incluindo a cadeia de `Received`;
    - entender SPF, DKIM e DMARC, e o que eles **não** garantem;
    - encontrar links disfarçados;
    - extrair e analisar anexos (PDF e macros) **sem abri-los**, com `pdfid`, `pdf-parser`, `exiftool` e `olevba`;
    - saber o que fazer depois da análise.

## 1. Os golpes que mais chegam

| Tipo | Como é | Exemplo na Pantera Logística |
|---|---|---|
| **Phishing em massa** | mesma mensagem para milhares de pessoas | "Sua caixa de e-mail está cheia, clique aqui" |
| **Spear phishing** | mensagem feita sob medida para uma pessoa ou setor | e-mail ao financeiro citando um fornecedor real |
| **Fraude de boleto / BEC** | troca de dados bancários de um fornecedor ou cobrança falsa | "o boleto de outubro mudou de banco, pague hoje" |
| **Roubo de credenciais** | página falsa de login | "sua senha expira hoje, confirme aqui" |
| **Anexo malicioso** | documento que executa código ao abrir | PDF com JavaScript, planilha com macro |
| **Smishing / WhatsApp** | o mesmo golpe por SMS ou mensageiro | "sou o novo número do diretor, preciso de um PIX" |

!!! atacante "Como o atacante pensa"
    Todo phishing tenta tirar a vítima do modo de pensar com calma. Os gatilhos se repetem: **urgência** ("pague hoje", "expira em 2 horas"), **autoridade** ("financeiro", "TI", "diretoria"), **medo** ("sua conta será bloqueada") e **quebra de processo** ("novos dados bancários", "não comente com ninguém"). Quando um e-mail tem dois desses, ele já merece desconfiança antes de qualquer análise técnica.

## 2. Anatomia de um e-mail

Um e-mail é texto. Abra um no terminal e você vê tudo que o programa de e-mail esconde:

```bash
cd ~/labs/08-phishing
less 03-rh.eml
```

A parte de cima são os **cabeçalhos**; depois de uma linha em branco vem o **corpo** (e os anexos, codificados em base64).

| Cabeçalho | O que diz | Cuidado |
|---|---|---|
| `From` | o remetente **mostrado** | é texto livre; o nome de exibição pode ser qualquer coisa |
| `Reply-To` | para onde vai a **resposta** | se for diferente do `From`, desconfie |
| `Return-Path` | o remetente "de envelope", usado na entrega | é o domínio que o SPF verifica |
| `Received` | cada servidor por onde a mensagem passou | lido **de baixo para cima**; o de baixo é o mais próximo da origem |
| `Authentication-Results` | o veredito do **seu** servidor sobre SPF, DKIM e DMARC | o campo mais valioso para o analista |
| `Message-ID` | identificador único | útil para achar a mesma mensagem em outras caixas |
| `X-Mailer` | o programa que gerou o e-mail | `PHPMailer` em cobrança "de banco" é estranho |

### SPF, DKIM e DMARC em uma frase cada

- **SPF**: o domínio publica a lista de servidores autorizados a enviar e-mails em seu nome. `spf=fail` = veio de um servidor que o domínio **não** autorizou.
- **DKIM**: o servidor de origem **assina** a mensagem; o destino confere a assinatura. `dkim=pass` = a mensagem não foi alterada e veio mesmo daquele domínio.
- **DMARC**: a política do domínio para quando SPF/DKIM falham, e a verificação de que o domínio do `From` bate com o que foi autenticado.

!!! erro "Erro comum de N1"
    Achar que `spf=pass dkim=pass dmarc=pass` significa "e-mail confiável". Esses testes provam que o e-mail veio **do domínio que diz ser**. Se o golpista registrou o próprio domínio parecido (`pantera-logistica-suporte.example`), ele configura SPF e DKIM perfeitos para ele. A autenticação diz **quem enviou**; não diz **se é do bem**.

## 3. Lab 1: três e-mails, três histórias

!!! cenario "Cenário"
    Três colaboradores encaminharam e-mails para o SOC pelo botão "reportar phishing". Eles estão em `~/labs/08-phishing/`. Sua tarefa: para cada um, decidir **legítimo** ou **malicioso** e dizer **por quê**, com base em evidências.

Veja os cabeçalhos principais de cada um:

```bash
for f in 0*.eml; do
  echo "=================== $f"
  grep -E -A2 "^(Return-Path|Received|Authentication-Results|From|Reply-To|Subject|X-Mailer):" "$f"
done | less
```

Para cada e-mail, anote:

1. O domínio do `From` e o do `Reply-To` (se houver). São iguais?
2. O IP e o servidor no `Received`. É interno (faixa privada, módulo 2) ou externo?
3. O resultado de SPF, DKIM e DMARC.
4. O domínio do remetente é **exatamente** o da empresa ou do fornecedor, ou só parecido?
5. Quais gatilhos de engenharia social aparecem no assunto e no texto?

Para ler o corpo:

```bash
python3 -c "
import email, sys
from email import policy
for f in ['01-boleto.eml', '02-senha.eml', '03-rh.eml']:
    m = email.message_from_bytes(open(f, 'rb').read(), policy=policy.default)
    print('=====', f, '|', m['Subject'])
    print(m.get_body(preferencelist=('plain',)).get_content())
"
```

## 4. Lab 2: o link que mente

No e-mail `02-senha.eml`, o texto do link parece o portal da empresa. Mas, num e-mail em HTML, o **texto mostrado** e o **destino real** são coisas independentes:

```bash
python3 -c "
import email, re
from email import policy
m = email.message_from_bytes(open('02-senha.eml', 'rb').read(), policy=policy.default)
html = m.get_body(preferencelist=('html',)).get_content()
for destino, texto in re.findall(r\"<a href='([^']+)'>([^<]+)</a>\", html):
    print('texto mostrado:', texto)
    print('destino real  :', destino)
"
```

Compare os dois. Olhe com atenção o **domínio** do destino real, lendo **da direita para a esquerda**: o domínio que manda é o que vem logo antes do sufixo (`.example`, `.com.br`). Tudo à esquerda dele é decoração que o dono do domínio escolhe.

## 5. Lab 3: o anexo PDF

**Nunca** abra o anexo para "ver o que é". Extraia e analise como arquivo:

```bash
python3 -c "
import email
from email import policy
m = email.message_from_bytes(open('01-boleto.eml', 'rb').read(), policy=policy.default)
for parte in m.iter_attachments():
    nome = parte.get_filename()
    open(nome, 'wb').write(parte.get_content())
    print('anexo salvo:', nome)
"
file boleto_outubro.pdf
sha256sum boleto_outubro.pdf
```

O `file` confirma o tipo **real** pelo conteúdo (um `.pdf` pode ser um executável renomeado). O `sha256sum` dá a "impressão digital", que vai para o ticket e serve para procurar o mesmo arquivo em outros lugares.

### pdfid: o raio-x

```bash
pdfid boleto_outubro.pdf
```

O `pdfid` conta palavras-chave perigosas dentro do PDF. Um boleto de verdade não precisa de nenhuma destas:

| Palavra-chave | Significado |
|---|---|
| `/JS` e `/JavaScript` | o PDF contém JavaScript |
| `/OpenAction` e `/AA` | algo é executado **automaticamente** ao abrir ou ao interagir |
| `/Launch` | o PDF tenta executar um programa |
| `/EmbeddedFile` | há um arquivo escondido dentro do PDF |
| `/URI` | links |

### pdf-parser: o que exatamente ele faz

```bash
pdf-parser --search javascript boleto_outubro.pdf
```

Você vai ver o objeto que contém o JavaScript e o código em si. Neste arquivo de treino, o código só mostra um aviso (`app.alert(...)`). Num ataque real, aqui estaria o código que explora uma falha do leitor de PDF ou que redireciona para um download.

### exiftool: os metadados

```bash
exiftool boleto_outubro.pdf
```

Título, autor, programa que criou e **data de criação**. Às vezes os metadados entregam o golpista: um "boleto do banco" criado por um programa estranho, ou com data **anterior** à suposta emissão.

## 6. Lab 4: a macro

O time de resposta extraiu a macro de um documento `pedido_frete_outubro.docm` que chegou a outro setor. O código está em `macro_pedido_frete.vba`. O `olevba` analisa macros (dentro de documentos do Office ou como texto):

```bash
olevba macro_pedido_frete.vba
```

No fim da saída, a tabela classifica o que encontrou:

| Tipo | Significado |
|---|---|
| `AutoExec` | a macro roda **sozinha** ao abrir o documento (`AutoOpen`, `Document_Open`) |
| `Suspicious` | comandos perigosos (`Shell`, `vbHide`, `CreateObject`) |
| `Base64 Strings` | texto codificado escondido |
| `IOC` | URLs, IPs ou executáveis encontrados no código |

Repare em dois truques no código:

1. `"pow" & "ershell"`: a palavra `powershell` foi **quebrada em pedaços** e colada na hora. Uma busca simples por "powershell" no arquivo não acharia nada.
2. `-enc` seguido de base64: o comando real está codificado.

Decodifique. O PowerShell usa base64 de texto **UTF-16** (dois bytes por letra, a mesma armadilha do `wide` da YARA no módulo 9). No CyberChef: **From Base64** seguido de **Decode text** com **UTF-16LE (1200)**. Ou no terminal:

```bash
grep -oE '"[A-Za-z0-9+/=]{40,}"' macro_pedido_frete.vba | tr -d '"' | base64 -d | iconv -f UTF-16LE -t UTF-8; echo
```

Neste arquivo de treino, o comando só escreve uma mensagem. Mas o **padrão** (macro automática + Shell escondido + PowerShell sem perfil, oculto e codificado) é idêntico ao de um ataque real. É exatamente o alerta "Excel abrindo PowerShell" que você viu no módulo 4.

## 7. Depois da análise

Concluiu que é malicioso? A resposta não para no "é phishing":

1. **Quem mais recebeu?** O mesmo `Message-ID`, remetente ou assunto em outras caixas. (Num SOC real, isso é uma busca no gateway de e-mail.)
2. **Alguém clicou, respondeu ou abriu o anexo?** Procure acessos ao domínio do link no proxy ou DNS, e execuções na estação de quem abriu.
3. **Alguém digitou a senha?** Se sim: troca de senha imediata e verificação de logons daquela conta.
4. **Bloqueio**: remetente, domínio e link (defanged no ticket, módulo 10).
5. **Fraude de boleto**: alguém pagou? O financeiro deve confirmar dados bancários com o fornecedor **por um telefone já conhecido**, nunca pelo telefone que veio no e-mail.
6. **Dados pessoais** envolvidos (credenciais, dados de clientes)? Módulo 11.
7. **Avisar quem reportou**: o colaborador que usou o botão "reportar" merece retorno. Isso ensina a empresa inteira a reportar.

## Checagem

1. Qual dos três e-mails é legítimo? Cite três evidências.
2. No `01-boleto.eml`, qual o resultado do SPF e por que ele falhou? Para onde iriam as respostas?
3. O `02-senha.eml` passou em SPF, DKIM e DMARC. Por que ainda assim é malicioso?
4. No link do lab 2, qual é o domínio que realmente manda no destino?
5. Quais palavras-chave do `pdfid` indicaram perigo no boleto, e o que significam juntas?
6. Que truque a macro usa para esconder a palavra "powershell"? Por que isso importa para quem escreve regras?
7. Um colaborador do financeiro já pagou o boleto do `01-boleto.eml`. O que muda na resposta?

<details markdown="1">
<summary>Ver respostas</summary>

1. O **`03-rh.eml`**. Evidências: veio de um servidor **interno** (`exch01`, IP `10.10.2.15`, faixa privada); SPF, DKIM e DMARC passam **para o domínio da própria empresa** (`pantera-logistica.example`); não há `Reply-To` diferente; o conteúdo é informativo, sem link, anexo, urgência ou pedido de dados.
2. `spf=fail`: o domínio `transportes-andorinha.example` **não autoriza** o IP `203.0.113.66` a enviar em seu nome. O golpista forjou o domínio do fornecedor. As respostas iriam para `financeiro.andorinha@correio-rapido.example` (o `Reply-To`), uma caixa controlada pelo golpista. Somam-se: `dkim=none`, `dmarc=fail`, `X-Mailer: PHPMailer`, urgência e "novos dados bancários".
3. Porque o golpista registrou e configurou **o próprio domínio**, `pantera-logistica-suporte.example`, que só **parece** o da empresa. A autenticação prova que o e-mail veio desse domínio, e esse domínio é do golpista. Somam-se: urgência ("expira hoje", "bloqueada em 2 horas") e o link disfarçado.
4. **`login-seguro.example`**. O endereço `pantera-logistica.login-seguro.example` é um subdomínio de `login-seguro.example`; o "pantera-logistica" à esquerda é decoração escolhida pelo golpista.
5. `/JS` e `/JavaScript` (há código) e `/OpenAction` (algo roda **automaticamente** ao abrir). Juntas: um PDF que executa JavaScript assim que é aberto. Um boleto não tem motivo nenhum para isso.
6. Concatenação de texto: `"pow" & "ershell"`. Regras que procuram a palavra inteira no **arquivo** não a encontram; é preciso detectar o **comportamento** (o processo `powershell.exe` sendo criado pelo Office, módulo 3) ou procurar padrões mais robustos.
7. Vira um incidente de **fraude financeira** em andamento: acionar imediatamente o financeiro e o banco para tentar bloquear ou recuperar a transferência, preservar o e-mail e os comprovantes, verificar se a caixa de e-mail do fornecedor (ou a nossa) foi comprometida, e escalar com prioridade crítica.

</details>

!!! dica "Para ir além"
    - Abra qualquer e-mail da sua caixa pessoal no modo "mostrar original" e leia a cadeia de `Received` e o `Authentication-Results`. Fica fácil depois de três ou quatro.
    - Leia sobre **typosquatting** e **IDN homograph**: domínios que trocam letras parecidas (`rn` por `m`, letras de outros alfabetos).
    - Explore o `oleid` e o `mraptor`, outras ferramentas do oletools.
