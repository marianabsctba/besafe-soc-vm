<!-- descricao: IP, portas, TCP, DNS e HTTP explicados do zero, capturando tráfego de verdade. -->
# Módulo 2: Redes para quem vai defender

<p class="sub">Quase todo ataque passa pela rede em algum momento. Se você entende a conversa, percebe quando ela está estranha.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - o que é um endereço IP, e a diferença entre IP privado e público;
    - o que são portas e quais as mais importantes para o SOC;
    - como o TCP abre uma conexão (o *handshake*) e como o UDP difere;
    - como o DNS transforma nomes em endereços, e por que atacantes adoram DNS;
    - ler uma requisição HTTP e entender o que o HTTPS esconde e o que ele **não** esconde;
    - capturar tráfego com `tshark` e analisar no Wireshark.

## 1. A ideia central: pacotes

Quando um computador fala com outro, a mensagem é quebrada em pedaços chamados **pacotes**. Cada pacote é como um envelope:

- **de quem** (IP de origem) e **para quem** (IP de destino);
- **para qual serviço** (porta de destino) e **de qual porta voltar** (porta de origem);
- **o conteúdo** (um pedaço da página, do e-mail, do arquivo).

O analista de SOC passa muito tempo olhando os envelopes, mesmo quando não consegue abrir o conteúdo. Só os envelopes já contam muita coisa: *quem falou com quem, quando, quanto, com que frequência*.

## 2. Endereço IP

Um **endereço IP** (versão 4) são quatro números de 0 a 255 separados por ponto, como `192.168.0.10`. Ele identifica um dispositivo numa rede.

### Privado ou público?

Algumas faixas são reservadas para **redes internas** e nunca aparecem na internet:

| Faixa privada | Onde costuma aparecer |
|---|---|
| `10.0.0.0` a `10.255.255.255` | redes corporativas |
| `172.16.0.0` a `172.31.255.255` | redes corporativas, Docker, WSL |
| `192.168.0.0` a `192.168.255.255` | redes domésticas e pequenos escritórios |
| `127.0.0.0` a `127.255.255.255` | *loopback*: a própria máquina (`127.0.0.1` é o `localhost`) |

Qualquer endereço fora dessas faixas (e de algumas outras especiais) é **público**: está na internet.

!!! atencao "Por que isso importa tanto no SOC"
    A primeira pergunta diante de um IP num alerta é: **é interno ou externo?** Uma estação falando com um servidor interno é rotina. A mesma estação falando às 3h da manhã com um IP público que nunca apareceu antes é outra conversa. Saber classificar um IP de olho é um reflexo que você precisa desenvolver.

!!! dica "IPs de documentação"
    Neste treinamento, os IPs "de fora" usados nos exemplos e nos e-mails falsos estão nas faixas `203.0.113.x`, `198.51.100.x` e `192.0.2.x`. Elas são reservadas **para documentação** e não pertencem a ninguém. É boa prática usá-las em material de treino, para não "acusar" um IP real por engano.

## 3. Portas: a porta certa do prédio

Se o IP é o endereço do prédio, a **porta** é o número do apartamento: diz **qual serviço** vai receber o pacote. Um mesmo servidor pode ter um site na porta 443 e um banco de dados na 5432.

Portas que você precisa reconhecer de cabeça:

| Porta | Serviço | Comentário de SOC |
|---|---|---|
| 22 | SSH | acesso remoto a Linux; alvo número um de força bruta |
| 25 / 587 | SMTP | envio de e-mail |
| 53 | DNS | tradução de nomes; usado também para esconder dados |
| 80 | HTTP | web sem criptografia |
| 443 | HTTPS | web com criptografia; a maior parte do tráfego hoje |
| 445 | SMB | compartilhamento de arquivos Windows; muito usado em movimento lateral |
| 3389 | RDP | área de trabalho remota do Windows; exposto na internet é um convite |
| 1514 / 1515 | Wazuh | por onde os agentes mandam eventos ao Wazuh |

## 4. TCP e UDP

Existem dois jeitos principais de mandar pacotes:

- **TCP** é como um telefonema: primeiro os dois lados combinam a conversa, depois falam, e cada pedaço é confirmado. Se algo se perde, é reenviado. Usado por web, e-mail, SSH, SMB.
- **UDP** é como mandar um cartão-postal: envia e pronto, sem confirmação. É mais rápido e simples. Usado por DNS, streaming, jogos.

### O handshake de três vias

Toda conexão TCP começa com três pacotes:

```
Cliente  ──── SYN ────────▶  Servidor     "quero conversar"
Cliente  ◀─── SYN, ACK ────  Servidor     "ok, eu também"
Cliente  ──── ACK ────────▶  Servidor     "combinado"
```

Só depois disso os dados começam a passar. No fim, a conexão é encerrada com pacotes **FIN** (ou cortada com **RST**).

!!! atacante "Como o atacante pensa"
    Antes de atacar, o atacante faz um **reconhecimento**: manda SYN para centenas de portas de um alvo para ver quais respondem com SYN-ACK (porta aberta) e quais respondem com RST (porta fechada). Isso é um **port scan**. No SOC, ele aparece como **um IP tocando muitas portas diferentes em pouco tempo**, quase sempre sem completar conexões. Agora você sabe por que esse padrão é suspeito.

## 5. DNS: a agenda de contatos da internet

Computadores falam em IPs; pessoas preferem nomes. O **DNS** traduz um nome como `pantera-logistica.com.br` no IP do servidor. O fluxo simplificado:

1. Você digita o nome no navegador.
2. O computador pergunta ao **resolvedor DNS** (via UDP, porta 53): "qual o IP de `pantera-logistica.com.br`?"
3. O resolvedor responde com o IP (ou com "não existe").
4. Só então o navegador abre a conexão TCP com aquele IP.

Tipos de registro que você vai ver:

| Tipo | Significado |
|---|---|
| `A` | nome → endereço IPv4 |
| `AAAA` | nome → endereço IPv6 |
| `MX` | qual servidor recebe e-mail do domínio |
| `TXT` | texto livre (usado para SPF, verificações e, às vezes, para esconder dados) |
| `CNAME` | apelido: este nome é outro nome |

!!! atacante "Como o atacante pensa"
    Quase toda rede deixa o DNS passar, porque sem ele nada funciona. Por isso atacantes usam DNS para:

    - **falar com o servidor de comando** (C2) escondendo ordens dentro de perguntas e respostas;
    - **vazar dados aos pedaços** em nomes enormes, como `a8f3c2e1d9...pantera-vaza.example`;
    - usar **domínios recém-registrados** ou com nomes aleatórios (`xk2jq9v.top`), criados aos montes por malware.

    No SOC, desconfie de: nomes muito longos ou aleatórios, volume anormal de perguntas para um mesmo domínio, muitas perguntas `TXT` e máquinas consultando um resolvedor DNS que não é o da empresa.

## 6. HTTP e HTTPS

### HTTP

O HTTP é a língua da web. O cliente faz um **pedido** e o servidor devolve uma **resposta**. Um pedido típico:

```
GET /rastreio?carga=12345 HTTP/1.1
Host: pantera-logistica.com.br
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...
```

| Parte | Significado |
|---|---|
| `GET` | o método: buscar algo (`POST` envia dados, como um formulário) |
| `/rastreio?carga=12345` | o caminho e os parâmetros |
| `Host` | o site pedido |
| `User-Agent` | o programa que fez o pedido, **segundo ele mesmo** |

A resposta começa com um **código de status**: `200` (ok), `301`/`302` (redirecionamento), `403` (proibido), `404` (não encontrado), `500` (erro no servidor).

!!! erro "Erro comum de N1"
    Confiar no `User-Agent`. Ele é **autodeclarado**: qualquer programa pode dizer que é o Chrome. Ferramentas de ataque às vezes esquecem de disfarçar (`python-requests/2.31`, `curl/8.5`, `sqlmap`), e aí o User-Agent ajuda. Mas um User-Agent "normal" não prova nada.

### HTTPS: o que fica escondido e o que não fica

O HTTPS é o HTTP dentro de um túnel criptografado (TLS). Para quem observa a rede:

| Fica **escondido** | Continua **visível** |
|---|---|
| o caminho (`/rastreio?carga=...`) | os IPs de origem e destino |
| os cabeçalhos e o conteúdo | as portas |
| senhas e formulários | **o nome do site** (no campo SNI do início da conexão) |
| | o horário, o tamanho e o ritmo das conexões |

Ou seja: mesmo sem abrir o conteúdo, o SOC sabe que a máquina X conversou com o site Y, por quanto tempo e com que frequência. Isso basta para pegar muito malware, que costuma "ligar para casa" em intervalos regulares (o chamado *beacon*).

## 7. Lab: espionando a sua própria rede

!!! cenario "Cenário"
    O time de infraestrutura da Pantera Logística vai subir um novo serviço interno de rastreamento. Antes de liberar, o seu líder quer que você entenda como esse tráfego aparece "no fio", para saber reconhecer depois. Você vai montar um mini-site na sua VM, acessar e capturar tudo.

### Passo 1: quem sou eu na rede?

```bash
ip -br addr
ip route
```

O primeiro mostra as interfaces de rede e seus IPs. Você vai ver `lo` (loopback, `127.0.0.1`) e a placa de rede (algo como `ens33` ou `enp0s3`) com um IP privado. O segundo mostra a **rota padrão** (`default via ...`): o endereço do roteador, por onde sai tudo que não é da rede local.

### Passo 2: quais portas estão abertas nesta máquina?

```bash
sudo ss -tlnp
```

| Opção | Significado |
|---|---|
| `-t` | só TCP |
| `-l` | só portas **escutando** (esperando conexões) |
| `-n` | mostra números em vez de nomes |
| `-p` | mostra qual programa está escutando |

Procure na lista as portas do Wazuh (`443`, `9200`, `55000`, `1514`, `1515`). Repare na coluna de endereço local: `127.0.0.1:443` só aceita conexões **da própria máquina**, enquanto `0.0.0.0:1514` aceita **de qualquer lugar**. Essa diferença é a primeira coisa que um atacante (e um auditor) olha.

### Passo 3: suba um site

```bash
cd ~/labs/02-redes/site
python3 -m http.server 8000
```

Esse terminal fica ocupado servindo o site. Abra uma **segunda aba** (`Ctrl` + `Shift` + `T`) para os próximos passos.

### Passo 4: capture o handshake

Na segunda aba, comece a captura (ela vai esperar pacotes):

```bash
sudo tshark -i lo -f "tcp port 8000"
```

Abra uma **terceira aba** e acesse o site:

```bash
curl http://127.0.0.1:8000/
```

!!! atencao "Espere o tshark começar"
    O `tshark` leva alguns segundos para começar a capturar. Espere aparecer a linha `Capturing on 'Loopback: lo'` antes de mandar o `curl`. Se você for rápido demais, os pacotes passam antes de ele estar ouvindo.

Volte à aba do `tshark`. Você vai ver algo assim (os números de porta e tempo mudam):

```
 1 0.000000  127.0.0.1 → 127.0.0.1  TCP  74 39052 → 8000 [SYN] Seq=0 ...
 2 0.000014  127.0.0.1 → 127.0.0.1  TCP  74 8000 → 39052 [SYN, ACK] Seq=0 Ack=1 ...
 3 0.000023  127.0.0.1 → 127.0.0.1  TCP  66 39052 → 8000 [ACK] Seq=1 Ack=1 ...
 4 0.000083  127.0.0.1 → 127.0.0.1  HTTP 143 GET / HTTP/1.1
 5 0.000086  127.0.0.1 → 127.0.0.1  TCP  66 8000 → 39052 [ACK] ...
 6 0.003336  127.0.0.1 → 127.0.0.1  TCP  251 HTTP/1.0 200 OK  [TCP segment of a reassembled PDU]
 7 0.003372  127.0.0.1 → 127.0.0.1  TCP  66 39052 → 8000 [ACK] ...
 8 0.003397  127.0.0.1 → 127.0.0.1  HTTP 83 HTTP/1.0 200 OK  (text/html)
 9 0.003399  127.0.0.1 → 127.0.0.1  TCP  66 39052 → 8000 [ACK] ...
10 0.003430  127.0.0.1 → 127.0.0.1  TCP  66 8000 → 39052 [FIN, ACK] ...
11 0.003441  127.0.0.1 → 127.0.0.1  TCP  66 39052 → 8000 [FIN, ACK] ...
12 0.003447  127.0.0.1 → 127.0.0.1  TCP  66 8000 → 39052 [ACK] ...
13 0.003451  127.0.0.1 → 127.0.0.1  TCP  66 39052 → 8000 [ACK] ...
```

Leia como uma história:

| Pacotes | O que aconteceu |
|---|---|
| 1 a 3 | o handshake: `SYN`, `SYN, ACK`, `ACK` |
| 4 | o cliente pede a página (`GET /`) |
| 5, 7, 9 | os `ACK` sozinhos são confirmações: "recebi" |
| 6 e 8 | o servidor responde `200 OK`, em dois pedaços (o tshark junta os pedaços e mostra o HTTP completo no 8) |
| 10 a 13 | o encerramento: cada lado manda `FIN` e confirma o `FIN` do outro |

Repare que a porta do cliente (`39052` no exemplo) é aleatória e alta, enquanto a do servidor é fixa (`8000`). E que **o servidor fechou primeiro** (pacote 10): servidores HTTP/1.0 encerram a conexão logo depois de responder. Pare a captura com `Ctrl` + `C`.

### Passo 5: o que o pedido revela

Capture de novo, agora mostrando os detalhes só dos pacotes HTTP:

```bash
sudo tshark -i lo -f "tcp port 8000" -Y http.request -V
```

Na outra aba, faça dois pedidos:

```bash
curl http://127.0.0.1:8000/rastreio.html
curl -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0" http://127.0.0.1:8000/rastreio.html
```

Na saída do `tshark`, procure a linha `User-Agent` de cada pedido. No primeiro aparece `curl/...`. No segundo, o mesmo `curl` se diz **Chrome no Windows**, porque o `-A` troca o User-Agent. Você acabou de comprovar por que User-Agent não é prova de nada.

Olhe também a aba do servidor (`python3 -m http.server`): ele registrou cada acesso com IP, horário, caminho e código de status. Esse é o formato clássico de **log de acesso web**, que você verá muito no SOC.

### Passo 6: DNS ao vivo

A VM é offline, mas ainda tem um resolvedor DNS local (o `systemd-resolved`, em `127.0.0.53`). Capture as perguntas:

```bash
sudo tshark -i lo -f "udp port 53"
```

Na outra aba:

```bash
dig pantera-logistica.test
dig -t TXT pantera-logistica.test
```

No `tshark` aparecem a **pergunta** (`Standard query ... A pantera-logistica.test`) e a **resposta**. Como a VM não tem internet, a resposta vai indicar falha (`SERVFAIL` ou `No such name`). Isso também é informação: no SOC, um volume grande de respostas de "nome não existe" saindo de uma máquina é sinal clássico de malware procurando servidores de comando com nomes gerados por algoritmo.

Note também o `dig` em si: a seção `ANSWER` vem vazia e o `status` mostra o erro. O `dig` é a ferramenta do analista para perguntar ao DNS diretamente.

### Passo 7: HTTPS por fora

Capture o início de uma conexão HTTPS com o Wazuh:

```bash
sudo tshark -i lo -f "tcp port 443" -Y tls.handshake.type==1 -V | grep -E "Server Name:|Version"
```

Na outra aba:

```bash
curl -sk https://localhost/ > /dev/null
```

Você vai ver o **Server Name: localhost**: o nome do site trafega visível no início da conexão (é o SNI), mesmo com tudo criptografado depois. Pare com `Ctrl` + `C`.

### Passo 8: salve e abra no Wireshark

O `tshark` é ótimo para filtrar rápido; o **Wireshark** é melhor para explorar com calma. Grave uma captura em arquivo:

```bash
sudo tshark -i lo -f "tcp port 8000" -w /tmp/site.pcap
```

Faça dois ou três `curl` na outra aba, pare a captura e copie o arquivo para você:

```bash
sudo cp /tmp/site.pcap ~/labs/02-redes/ && sudo chown analista: ~/labs/02-redes/site.pcap
wireshark ~/labs/02-redes/site.pcap &
```

No Wireshark:

1. Clique num pacote `GET` e explore o painel do meio: cada camada (Ethernet/Loopback, IP, TCP, HTTP) aparece separada, do envelope ao conteúdo.
2. Clique com o botão direito no pacote e escolha **Seguir** > **Fluxo TCP** (*Follow TCP Stream*). A conversa inteira aparece como texto: pedido em uma cor, resposta em outra. É a ferramenta mais usada do Wireshark numa investigação.
3. Abra **Estatísticas** > **Conversações**: a lista de quem falou com quem e quanto. Em capturas grandes, é o primeiro lugar para olhar.

Volte à primeira aba e pare o servidor com `Ctrl` + `C`.

## Checagem

1. Classifique como privado, público ou loopback: `10.20.30.40`, `172.20.1.5`, `172.40.1.5`, `8.8.8.8`, `127.0.0.1`, `192.168.100.7`.
2. Quais são os três pacotes do handshake TCP, em ordem?
3. Um alerta mostra o IP `10.10.8.14` fazendo conexões para 900 portas diferentes de `10.10.5.21` em 20 segundos. O que é isso, provavelmente?
4. Por que o DNS é tão atraente para quem quer esconder comunicação maliciosa?
5. Num tráfego HTTPS, o SOC consegue ver a senha que o usuário digitou? E o site que ele acessou?
6. No passo 5, o que o experimento com `curl -A` provou?
7. No passo 2, qual a diferença prática entre um serviço escutando em `127.0.0.1` e em `0.0.0.0`?

<details markdown="1">
<summary>Ver respostas</summary>

1. `10.20.30.40` privado; `172.20.1.5` privado (está entre 172.16 e 172.31); `172.40.1.5` **público** (fora da faixa, uma pegadinha clássica); `8.8.8.8` público (é o DNS do Google); `127.0.0.1` loopback; `192.168.100.7` privado.
2. `SYN`, `SYN-ACK`, `ACK`.
3. Um **port scan** interno: uma máquina mapeando os serviços de outra. Se `10.10.8.14` é uma estação de usuário, é bem suspeito, porque pode ser um atacante já dentro da rede fazendo reconhecimento antes de se mover. Se for a máquina de um scanner de vulnerabilidades autorizado, é rotina. A investigação começa por **saber quem é a máquina de origem**.
4. Porque quase todo ambiente permite DNS (sem ele nada funciona), o volume é alto (fácil se misturar) e muitas empresas não inspecionam o conteúdo das consultas.
5. A senha **não** (ela vai dentro do túnel criptografado). O site, **sim**: o nome aparece no SNI, e os IPs e o ritmo das conexões também ficam visíveis.
6. Que o User-Agent é escolhido por quem faz o pedido. O mesmo programa se apresentou como `curl` e como Chrome no Windows.
7. Em `127.0.0.1` o serviço só aceita conexões da própria máquina; em `0.0.0.0` aceita de qualquer rede que alcance a máquina. Um serviço sensível (um banco de dados, um painel de administração) escutando em `0.0.0.0` sem necessidade é uma exposição desnecessária.

</details>

!!! dica "Para ir além"
    - Leia sobre o modelo **OSI** e o modelo **TCP/IP**. Você já usou quatro camadas neste módulo sem perceber (enlace, rede, transporte, aplicação).
    - Explore os filtros de exibição do Wireshark: `ip.addr == 127.0.0.1`, `tcp.flags.syn == 1 && tcp.flags.ack == 0` (só os "primeiros SYN"), `http.request.method == "POST"`, `dns.flags.rcode != 0` (respostas DNS com erro).
    - Quando tiver internet, os desafios do site **Malware-Traffic-Analysis.net** são o melhor treino de PCAP que existe. Leia os termos de uso do site antes.
