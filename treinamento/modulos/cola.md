# Cola de comandos

<p class="sub">Para deixar aberta durante o plantão. Todos funcionam nesta VM.</p>

## Terminal

| Tarefa | Comando |
|---|---|
| onde estou | `pwd` |
| listar com detalhes e ocultos | `ls -lah` |
| ler arquivo grande | `less arquivo` (busca com `/`, sai com `q`) |
| começo / fim | `head -n 20 arquivo` / `tail -n 20 arquivo` |
| acompanhar ao vivo | `tail -f arquivo` |
| procurar texto | `grep -i "texto" arquivo` |
| contar linhas com texto | `grep -c "texto" arquivo` |
| procurar arquivos por nome | `find /caminho -iname "*parte*"` |
| ranking de valores | `... \| sort \| uniq -c \| sort -nr \| head` |
| uma coluna (separador vírgula) | `cut -d, -f3 arquivo` |
| primeira palavra de cada linha | `awk '{print $1}' arquivo` |
| hash de um arquivo | `sha256sum arquivo` |
| tipo real de um arquivo | `file arquivo` |

## Rede

| Tarefa | Comando |
|---|---|
| meus IPs | `ip -br addr` |
| rota padrão | `ip route` |
| portas escutando | `sudo ss -tlnp` |
| consulta DNS | `dig nome` / `dig -t TXT nome` |
| capturar ao vivo | `sudo tshark -i lo -f "tcp port 8000"` |
| gravar captura | `sudo tshark -i INTERFACE -w arquivo.pcap` |
| ler PCAP com filtro | `tshark -r arquivo.pcap -Y "http.request"` |
| abrir no Wireshark | `wireshark arquivo.pcap &` |

## Logs do Windows (EVTX)

| Tarefa | Comando |
|---|---|
| todos os eventos | `chainsaw dump arquivo.evtx` |
| só um Event ID | `chainsaw search -t 'Event.System.EventID: =4624' arquivo.evtx` |
| caçar com regras Sigma | `hayabusa dfir-timeline -f arquivo.evtx -o saida.csv -w` |
| linha do tempo de uma pasta | `hayabusa dfir-timeline -d pasta/ -o saida.csv -w` |

## Event IDs essenciais

| ID | Significado |
|---|---|
| 4624 / 4625 | logon com sucesso / falha |
| 4672 | logon com privilégio de administrador |
| 4688 | processo criado |
| 4697 / 7045 | serviço instalado |
| 4698 | tarefa agendada criada |
| 4720 | conta criada |
| 4728 / 4732 | adicionado a grupo |
| 1102 | log de segurança apagado |
| Sysmon 1 | processo criado (com linha de comando e pai) |
| Sysmon 3 | conexão de rede |
| Sysmon 10 | acesso à memória de outro processo |
| Sysmon 11 | arquivo criado |
| Sysmon 13 | valor de registro alterado |
| Sysmon 22 | consulta DNS |

## Tipos de logon

| Tipo | Significado |
|---|---|
| 2 | no teclado da máquina |
| 3 | pela rede |
| 4 | tarefa agendada |
| 5 | serviço |
| 9 | com outras credenciais (`runas /netonly`) |
| 10 | área de trabalho remota (RDP) |

## Serviços da VM

| Tarefa | Comando |
|---|---|
| estado do Wazuh | `systemctl status wazuh-manager wazuh-indexer wazuh-dashboard` |
| reiniciar o dashboard | `sudo systemctl restart wazuh-dashboard` |
| senha do Wazuh | `cat ~/.besafe/wazuh.txt` |
| alertas do Wazuh em texto | `sudo tail -f /var/ossec/logs/alerts/alerts.log` |
| eventos do Suricata | `tail -f /var/log/suricata/eve.json` |
