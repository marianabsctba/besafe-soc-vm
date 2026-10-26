<!-- descricao: Suricata e Wireshark: capturar, detectar, separar ruído de ataque e conferir no pacote. -->
# Módulo 6: Rede na prática com Suricata e Wireshark

<p class="sub">No módulo 2 você aprendeu a ler a conversa. Agora vai ver um sensor de verdade apontando o que há de suspeito nela, e vai descobrir o que ele deixa passar.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - o que é um IDS e como funciona uma assinatura do Suricata;
    - por que `HOME_NET` e `EXTERNAL_NET` mudam completamente o que o sensor enxerga;
    - analisar uma captura (PCAP) com o Suricata;
    - ler os alertas no `fast.log` e no `eve.json`;
    - separar alertas **informativos** de alertas de **ataque**;
    - reconhecer **falsos negativos**;
    - confirmar um alerta no Wireshark, pacote por pacote.

## 1. IDS, IPS e assinaturas

Um **IDS** (*Intrusion Detection System*) observa o tráfego e **avisa** quando reconhece um padrão de ataque. Um **IPS** faz o mesmo e **bloqueia**. O Suricata pode trabalhar dos dois jeitos; nesta VM ele é IDS.

O Suricata reconhece ataques por **assinaturas** (regras). Esta VM usa o conjunto gratuito **ET Open** (Emerging Threats), com dezenas de milhares de regras. Esta é (resumida) a regra que detecta o sqlmap:

```
alert http $EXTERNAL_NET any -> $HTTP_SERVERS any (msg:"ET SCAN Sqlmap SQL Injection Scan";
    flow:established,to_server; threshold: type limit, count 2, seconds 40, track by_src;
    http.user_agent; content:"sqlmap"; startswith; ... sid:2008538; ...)
```

| Parte | Significado |
|---|---|
| `alert` | a ação (registrar um alerta) |
| `http` | o protocolo |
| `$EXTERNAL_NET any -> $HTTP_SERVERS any` | **de onde** e **para onde** o tráfego precisa ir para a regra valer (`$HTTP_SERVERS` é, por padrão, o mesmo que `$HOME_NET`) |
| `msg` | o nome que aparece no alerta |
| `flow:established,to_server` | só em conexões já abertas, no sentido cliente → servidor |
| `threshold: type limit, count 2, seconds 40` | no máximo 2 alertas a cada 40 segundos por origem, para não inundar a fila |
| `http.user_agent; content:"sqlmap"; startswith` | **o que procurar**: User-Agent começando com "sqlmap" |
| `sid` | o número único da regra |

### HOME_NET e EXTERNAL_NET

`HOME_NET` é "a nossa rede"; `EXTERNAL_NET` é "o resto". Muitas regras só valem para tráfego **de fora para dentro**. Se o `HOME_NET` estiver mal configurado, o sensor fica **cego** para essas regras, sem dar erro nenhum. Veja a configuração desta VM:

```bash
grep -nE "^\s+(HOME_NET|EXTERNAL_NET|HTTP_PORTS):" /etc/suricata/suricata.yaml
```

Repare: o `HOME_NET` cobre as redes privadas, mas **não** o `127.0.0.0/8` (localhost). E o `HTTP_PORTS` é só a porta `80`. Guarde isso: vai explicar o resultado do lab.

## 2. Lab: um ataque contra o seu site

!!! cenario "Cenário"
    O site interno de rastreamento da Pantera Logística recebeu uma visita estranha. O time de infraestrutura gravou o tráfego. Você vai reproduzir a situação na sua VM, analisar a captura com o Suricata e confirmar cada alerta no Wireshark.

### Passo 1: suba o site

```bash
cd ~/labs/06-rede/site
ls
python3 -m http.server 8000
```

Repare no arquivo `id.txt`: ele imita a resposta de um servidor que foi invadido e devolveu a saída do comando `id` (que mostra que o processo roda como `root`). É um teste clássico de IDS.

### Passo 2: grave o tráfego

Numa **segunda aba**, comece a gravação:

```bash
tshark -i lo -f "tcp port 8000" -w ~/labs/06-rede/lab.pcap
```

Espere aparecer `Capturing on 'Loopback: lo'`. Você está no grupo `wireshark`, por isso não precisa de `sudo` para capturar.

### Passo 3: o "visitante"

Numa **terceira aba**, faça as visitas abaixo. Cada linha imita um tipo de ferramenta ou de tentativa:

```bash
curl -s http://127.0.0.1:8000/id.txt
curl -s -A "sqlmap/1.8.4#stable (https://sqlmap.org)" "http://127.0.0.1:8000/index.html?id=1"
curl -s -A "Mozilla/5.00 (Nikto/2.5.0) (Evasions:None) (Test:000001)" http://127.0.0.1:8000/
curl -s "http://127.0.0.1:8000/index.html?q=1%27%20UNION%20SELECT%20NULL,NULL--"
curl -s --path-as-is "http://127.0.0.1:8000/../../etc/passwd"
curl -s -A "Wget/1.21" http://127.0.0.1:8000/index.html
```

| Linha | O que imita |
|---|---|
| 1 | o servidor devolvendo a saída do comando `id` |
| 2 | o **sqlmap**, ferramenta de injeção de SQL |
| 3 | o **Nikto**, scanner de vulnerabilidades web |
| 4 | uma tentativa de **injeção de SQL** (`UNION SELECT`) |
| 5 | uma tentativa de **path traversal** (subir pastas até `/etc/passwd`) |
| 6 | um download com `wget` |

Nenhuma dessas visitas causa dano: o site de teste não tem banco de dados nem arquivos sensíveis. Volte à aba do `tshark`, pare com `Ctrl` + `C`, e pare o site na primeira aba.

### Passo 4: o Suricata analisa a captura

O Suricata não precisa estar "ouvindo ao vivo": ele analisa um arquivo PCAP com `-r`. Primeiro, com a configuração **padrão**:

```bash
mkdir -p ~/labs/06-rede/saida-padrao
sudo suricata -r ~/labs/06-rede/lab.pcap -l ~/labs/06-rede/saida-padrao -k none
cat ~/labs/06-rede/saida-padrao/fast.log
```

Quantos alertas? Agora rode de novo, dizendo ao Suricata que, **neste lab**, a "nossa rede" é o localhost e que a porta 8000 também é web:

```bash
mkdir -p ~/labs/06-rede/saida-lab
sudo suricata -r ~/labs/06-rede/lab.pcap -l ~/labs/06-rede/saida-lab -k none \
  --set vars.address-groups.HOME_NET="[127.0.0.0/8]" \
  --set vars.address-groups.EXTERNAL_NET=any \
  --set vars.port-groups.HTTP_PORTS="[80,8000]"
sudo chown -R analista: ~/labs/06-rede/
```

| Opção | Significado |
|---|---|
| `-r` | ler um PCAP em vez de capturar ao vivo |
| `-l` | onde gravar os resultados |
| `-k none` | não descartar pacotes por *checksum* (comum em capturas de localhost) |
| `--set` | mudar uma variável da configuração só nesta execução |

### Passo 5: o ranking dos alertas

```bash
cut -d"]" -f3- ~/labs/06-rede/saida-lab/fast.log | sed "s/{TCP}.*//" | sort | uniq -c | sort -nr
```

Você vai ver alertas de prefixos diferentes. O prefixo diz muito:

| Prefixo | Leitura |
|---|---|
| `ET INFO` | informação, raramente malicioso sozinho |
| `ET HUNTING` | algo incomum que **vale olhar** se aparecer junto com outras coisas |
| `ET POLICY` | violação de política (uso de algo não permitido) |
| `ET SCAN` | reconhecimento / varredura |
| `ET WEB_SERVER`, `ET WEB_SPECIFIC_APPS` | ataque a aplicações web |
| `ET ATTACK_RESPONSE` | **resposta** que indica sucesso do ataque: muito grave |
| `ET MALWARE`, `ET TROJAN` | comunicação de malware conhecido |

### Passo 6: o alerta por dentro

O `fast.log` é o resumo. O `eve.json` tem os detalhes:

```bash
jq -c 'select(.event_type=="alert") | {sig: .alert.signature, src: .src_ip, dst: .dest_ip, porta: .dest_port, url: .http.url, ua: .http.http_user_agent}' ~/labs/06-rede/saida-lab/eve.json
```

E a regra exata que gerou um alerta (troque o número pelo `sid` que você quiser):

```bash
grep "sid:2100498;" /var/lib/suricata/rules/suricata.rules
```

### Passo 7: confirme no Wireshark

Alerta de IDS é indício; o pacote é a prova.

```bash
wireshark ~/labs/06-rede/lab.pcap &
```

1. Na barra de filtro, digite `http.user_agent contains "sqlmap"` e aperte Enter. Fica só o pedido do sqlmap.
2. Troque o filtro para `http.request.uri contains "passwd"`. Veja o caminho com `../../`.
3. Troque para `http.response` e ache a resposta do `id.txt`. Clique com o botão direito > **Seguir** > **Fluxo HTTP** e veja o `uid=0(root)` que o servidor devolveu.
4. Abra **Estatísticas** > **HTTP** > **Contador de pacotes** e **Requisições**: um resumo de todos os pedidos.

## 3. O que o sensor não viu

Compare as seis visitas do passo 3 com os alertas do passo 5. Pelo menos **duas** não geraram alerta nenhum. Quais?

!!! erro "Erro comum de N1"
    Concluir que "não houve ataque porque o IDS não alertou". Um IDS reconhece o que tem assinatura; o resto passa em silêncio. Esses são os **falsos negativos** do módulo 4, e é por isso que um SOC combina várias fontes (IDS, logs do servidor web, EDR) e não confia em uma só.

!!! atacante "Como o atacante pensa"
    Se a assinatura procura "sqlmap" no User-Agent, o atacante muda o User-Agent (você fez isso no módulo 2 com `curl -A`). Se procura `UNION SELECT`, ele escreve `UnIoN/**/SeLeCt`. Assinaturas pegam muito ataque automatizado e descuidado; atacantes cuidadosos estudam justamente as assinaturas para desviar delas.

## Checagem

1. Quantos alertas a configuração **padrão** gerou, e quantos a configuração **de lab**? Por que a diferença?
2. Quais tipos de alerta são ruído neste lab, e por quê?
3. Qual alerta é o mais grave e por quê?
4. Quais visitas **não** geraram alerta?
5. Qual o papel do Wireshark depois que o Suricata já alertou?
6. Num servidor real da empresa, o `HOME_NET` não inclui a rede da filial de Joinville. Que problema isso causa?

<details markdown="1">
<summary>Ver respostas</summary>

1. A configuração padrão gera **1** alerta (`GPL ATTACK_RESPONSE id check returned root`, uma regra que vale para qualquer origem e destino). A de lab gera **13**. Com o padrão, `127.0.0.1` não fazia parte do `HOME_NET` e a porta 8000 não era considerada web, então as regras "de fora para dentro" e as de HTTP não se aplicavam. Mesma captura, mesmo tráfego, resultados completamente diferentes: a configuração do sensor define o que ele enxerga.
2. `ET INFO Python SimpleHTTP ServerBanner` (6 vezes): só informa que o servidor é o servidor de teste do Python. `ET HUNTING curl User-Agent to Dotted Quad` (3 vezes): o `curl` acessando um IP direto, sem nome, o que é incomum mas, aqui, fomos nós mesmos. Ambos são **contexto**, não ataque.
3. `ET ATTACK_RESPONSE Output of id command from HTTP server` e o `GPL ATTACK_RESPONSE id check returned root`: eles mostram uma **resposta** do servidor que indica que um comando foi executado **como root**. Num caso real, é sinal de que o ataque **funcionou**. Os alertas de `SCAN` e de `/etc/passwd` mostram **tentativas**.
4. A do **Nikto** (linha 3), a do **UNION SELECT** (linha 4) e a do **wget** (linha 6, que é legítima). As duas primeiras são falsos negativos.
5. Confirmar o que realmente trafegou: ver o pedido e a resposta completos, verificar se o ataque teve sucesso e coletar as evidências exatas para o ticket.
6. Ataques vindos de Joinville seriam tratados como "externos", e ataques **contra** máquinas de Joinville não casariam com regras que exigem destino no `HOME_NET`. Parte do tráfego interno ficaria fora da vigilância, sem ninguém perceber.

</details>

!!! dica "Para ir além"
    - Leia algumas regras inteiras no `/var/lib/suricata/rules/suricata.rules` (procure por `sid:2008538;`) e tente entender cada palavra-chave na documentação do Suricata.
    - Escreva uma regra local que alerte qualquer User-Agent contendo `Nikto`, coloque num arquivo `local.rules` e rode o Suricata com `-S local.rules` sobre a mesma captura.
