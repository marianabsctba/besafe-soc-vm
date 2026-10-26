<!-- descricao: Escrever tickets que o N2 consegue usar, passar o turno sem perder nada e falar com quem não é técnico. -->
# Módulo 10: Ticket, plantão e comunicação

<p class="sub">Uma investigação brilhante que ninguém consegue entender vale quase nada. O ticket é o produto do seu trabalho.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - escrever um ticket completo, claro e verificável;
    - registrar evidências e indicadores de forma segura (*defang*);
    - separar **fato** de **hipótese**;
    - fazer uma passagem de turno que não deixa nada cair;
    - explicar um incidente para um gestor que não é técnico.

## 1. Para quem você escreve

O seu ticket vai ser lido por pessoas diferentes, em momentos diferentes:

| Leitor | O que ele precisa |
|---|---|
| o **N2**, daqui a 10 minutos | saber exatamente o que você viu e já verificou, para não refazer |
| o **colega do próximo turno** | entender o estado do caso sem te ligar às 3h |
| o **gestor** | saber o impacto e o que está sendo feito |
| a **auditoria**, daqui a um ano | reconstruir o que aconteceu e quem decidiu o quê |
| a **encarregada de dados (DPO)**, se houver dado pessoal | saber que dados, de quem, e desde quando |

Escreva pensando no pior caso: alguém que não estava lá, lendo com pressa.

## 2. A estrutura de um bom ticket

```
TÍTULO: [Severidade] O quê - Onde
  Ex.: [ALTA] PowerShell oculto iniciado pelo Excel - PL-FIN-07

RESUMO (2 a 3 linhas)
  O que aconteceu, em linguagem simples, e a sua avaliação.

LINHA DO TEMPO (sempre com fuso horário)
  2026-10-26 07:48:12 BRT  excel.exe (usuário joana.lima) inicia powershell.exe -w hidden -enc ...
  2026-10-26 07:48:15 BRT  powershell.exe conecta em 203.0.113[.]77:443
  2026-10-26 07:52:00 BRT  alerta recebido na fila do SOC

ATIVOS ENVOLVIDOS
  Máquina, IP, usuário, função da máquina e criticidade.

EVIDÊNCIAS
  Onde está cada dado: ID do alerta, consulta usada no SIEM, nome do arquivo de log,
  Event IDs e Record IDs. Quem ler deve conseguir encontrar a mesma coisa.

INDICADORES (IOCs), sempre "defanged"
  IP 203.0.113[.]77 | domínio atualiza-boleto[.]example | SHA-256 3f1a...

O QUE JÁ FOI VERIFICADO
  - Comando decodificado: baixa e executa um script (anexo: decodificado.txt)
  - Nenhuma outra máquina conectou no mesmo IP nas últimas 24h (consulta X)

AVALIAÇÃO
  Fato: ...
  Hipótese: ...

AÇÕES TOMADAS E RECOMENDADAS
  Tomadas: máquina isolada às 07:55 pelo playbook PB-03.
  Recomendadas: redefinir a senha de joana.lima; verificar caixa de e-mail.

ESCALADO PARA / QUANDO
  N2 (plantão: Carlos), 2026-10-26 07:58 BRT.
```

## 3. Fato e hipótese

O erro mais comum em ticket de iniciante é misturar o que você **viu** com o que você **acha**.

| Fato (verificável) | Hipótese (sua interpretação) |
|---|---|
| "O processo `excel.exe` criou `powershell.exe` com `-enc`." | "Provavelmente uma macro maliciosa." |
| "Houve 4.000 consultas DNS para subdomínios de `xk2jq9v[.]top`." | "Possível canal de C2 por DNS." |
| "A conta `adm.ricardo` apagou o log às 03:17 de sábado." | "A conta pode estar comprometida." |

Escreva os dois, **separados e identificados**. Hipóteses são valiosas (o N2 quer a sua leitura), mas precisam estar marcadas como hipóteses. Um "foi um ataque de ransomware" escrito como fato, e que não era, pode disparar uma crise desnecessária.

## 4. Indicadores com segurança: *defang*

Nunca cole um link malicioso "vivo" num ticket, chat ou e-mail. Alguém clica, ou o sistema gera uma pré-visualização que acessa o link. Use a forma **defanged**:

| Original | Defanged |
|---|---|
| `http://atualiza-boleto.example/pagar` | `hxxp://atualiza-boleto[.]example/pagar` |
| `203.0.113.77` | `203.0.113[.]77` |
| `financeiro@pantera-logistica.example` | `financeiro[@]pantera-logistica[.]example` |

O CyberChef faz isso com a operação **Defang URL** e **Defang IP Addresses**.

## 5. Horários e fusos

Toda linha do tempo precisa dizer o **fuso**. Ferramentas diferentes usam fusos diferentes (você viu isso no módulo 7: o Hayabusa em horário de Brasília, o Chainsaw em UTC). Escolha um padrão para o ticket (muitos SOCs usam UTC; outros usam o horário local) e **diga qual é**. Uma linha do tempo com três horas de diferença escondida pode inverter a ordem dos fatos.

## 6. Passagem de turno

A passagem de turno é o momento em que casos "caem no chão". Um bom resumo de turno tem:

1. **Casos abertos**, um por linha: número, situação atual, próximo passo e **quem está esperando o quê**.
2. **Casos fechados no turno** que merecem atenção (por exemplo, falsos positivos que se repetiram).
3. **Pendências com terceiros**: "Aguardando a TI confirmar o deploy do serviço X; prometeram até as 10h."
4. **Alertas de contexto**: manutenções programadas, ferramentas fora do ar, regras que estão gerando ruído.

!!! erro "Erro comum de N1"
    "Deixei tudo no sistema, é só olhar." O colega que chega não tem como saber qual dos 40 tickets abertos é urgente. A passagem de turno é **curadoria**: você diz o que importa.

## 7. Falando com quem não é técnico

O gerente financeiro não quer saber o que é `GetDelegateForFunctionPointer`. Ele quer saber:

1. **O que aconteceu**, em uma frase.
2. **Qual o impacto** (ou o que ainda não se sabe).
3. **O que está sendo feito**.
4. **O que ele precisa fazer** (se precisar).
5. **Quando terá a próxima atualização**.

Compare:

> ❌ "Detectamos execução de PowerShell ofuscado com indicadores de carregador em memória e beacon para infraestrutura C2 na estação PL-FIN-07."

> ✅ "Uma planilha recebida por e-mail tentou instalar um programa malicioso no computador da Joana, às 7h48. Isolamos o computador às 7h55 e, até agora, não vimos sinal de que o problema se espalhou. A Joana vai receber outra máquina enquanto analisamos. Por precaução, pedimos que ninguém do financeiro abra anexos do fornecedor 'Transportes Andorinha' até novo aviso. Próxima atualização às 11h."

Nenhuma informação técnica errada, nenhuma informação técnica desnecessária, e um pedido claro.

## 8. Lab: reescreva o ticket

!!! cenario "Cenário"
    Este ticket foi escrito por um analista na correria do turno da noite. Ele vai para o N2. Reescreva usando a estrutura da seção 2.

```
titulo: alerta estranho

vi um alerta de lsass no pc do rh, parece mimikatz. o arquivo tava no desktop do
usuario. mandei msg pro usuario perguntando se ele baixou alguma coisa mas ele nao
respondeu. acho que é hacker. o ip era 10.10.8.37. olhei o wazuh e tinha mais umas
coisas mas nao lembro. o site que ele acessou foi http://ferramentas-gratis.example/mimi.zip
fechei o alerta pq ja passei pro n2
```

Informações adicionais que você levantou ao reabrir o caso:

- Máquina: `PL-RH-03` (estação do RH), IP `10.10.8.37`, usuário `marcos.alves`.
- Alerta do Wazuh às 02:14:33 BRT: Sysmon 10, `C:\Users\marcos.alves\Desktop\mimi\mimikatz.exe` acessou `lsass.exe` com `GrantedAccess 0x1010`.
- Às 02:10:05 BRT, o Firefox baixou `mimi.zip` de `http://ferramentas-gratis.example/mimi.zip`.
- Às 02:16:40 BRT, logon tipo 3 da conta `adm.backup` em `SRV-ARQ01` vindo de `10.10.8.37`.
- O `marcos.alves` trabalha das 8h às 17h.

<details markdown="1">
<summary>Ver uma versão reescrita</summary>

```
TÍTULO: [CRÍTICA] Ferramenta de roubo de credenciais executada e possível uso de conta
        administrativa - PL-RH-03 / SRV-ARQ01

RESUMO
  O Mimikatz (ferramenta de roubo de senhas) foi baixado e executado na estação PL-RH-03,
  de madrugada, fora do horário do usuário. Dois minutos depois, a conta adm.backup fez
  logon no servidor de arquivos a partir dessa estação. Avaliação: provável comprometimento
  de credenciais com movimento lateral em andamento.

LINHA DO TEMPO (BRT)
  2026-10-26 02:10:05  Firefox baixa mimi.zip de hxxp://ferramentas-gratis[.]example/mimi.zip
  2026-10-26 02:14:33  mimikatz.exe (Desktop de marcos.alves) acessa lsass.exe (Sysmon 10, 0x1010)
  2026-10-26 02:16:40  logon tipo 3 de adm.backup em SRV-ARQ01, origem 10.10.8[.]37 (PL-RH-03)

ATIVOS
  PL-RH-03 (10.10.8.37), estação do RH, usuário marcos.alves; criticidade média.
  SRV-ARQ01, servidor de arquivos; criticidade alta.
  Conta adm.backup: conta administrativa de backup; criticidade alta.

EVIDÊNCIAS
  Alerta Wazuh (Sysmon 10) de 02:14:33; evento de download do Firefox de 02:10:05;
  evento 4624 tipo 3 em SRV-ARQ01 de 02:16:40.

INDICADORES
  URL hxxp://ferramentas-gratis[.]example/mimi.zip
  Arquivo C:\Users\marcos.alves\Desktop\mimi\mimikatz.exe

VERIFICADO
  - Horário fora da jornada do usuário (8h às 17h).
  - Usuário contatado por chat às 02:30; sem resposta.

AVALIAÇÃO
  Fato: Mimikatz executado e acessou o LSASS; adm.backup logou em SRV-ARQ01 a partir da
        mesma estação 2 minutos depois.
  Hipótese: alguém com acesso à estação (remoto ou físico) roubou a credencial de
        adm.backup e está se movendo para o servidor de arquivos. Também não se pode
        descartar que a própria conta marcos.alves esteja comprometida.

AÇÕES
  Tomadas: nenhuma além da análise.
  Recomendadas (urgente): isolar PL-RH-03; desabilitar/redefinir adm.backup e marcos.alves;
  verificar atividade de adm.backup em SRV-ARQ01 e outros servidores; verificar se há dados
  pessoais de colaboradores no SRV-ARQ01 (pasta do RH) e, se sim, avisar a encarregada.

ESCALADO PARA
  N2 de plantão, 2026-10-26 02:35 BRT. Alerta mantido ABERTO até o N2 assumir.
```

Repare nas correções:

- **Título** diz a gravidade, o quê e onde.
- O ticket original **não tinha horários**; o novo tem linha do tempo com fuso.
- A **conexão com o servidor** (a parte mais grave) estava ausente no original.
- O link foi **defanged**.
- "acho que é hacker" virou **avaliação com fato e hipótese separados**.
- Mandar mensagem ao usuário de madrugada, num caso em que a conta dele pode estar comprometida, avisa o atacante. Na dúvida, escale antes de contatar o usuário.
- O original **fechou o alerta** ao escalar. Um caso escalado continua aberto até alguém assumir.
- O servidor do RH pode ter dados pessoais: isso foi sinalizado para a encarregada (módulo 11).

</details>

## Checagem

1. Quais são as partes essenciais de um ticket?
2. Por que separar fato de hipótese?
3. Como fica `http://malware.example/a.exe` defanged? E o IP `198.51.100.23`?
4. O que não pode faltar numa passagem de turno?
5. Quais as cinco coisas que um gestor não técnico quer saber?

<details markdown="1">
<summary>Ver respostas</summary>

1. Título claro, resumo, linha do tempo com fuso, ativos envolvidos, evidências localizáveis, indicadores defanged, o que já foi verificado, avaliação (fato e hipótese), ações tomadas e recomendadas, e para quem e quando foi escalado.
2. Porque quem lê precisa saber o que está comprovado e o que é interpretação. Hipótese escrita como fato pode levar a decisões erradas, para mais (pânico) ou para menos (descaso).
3. `hxxp://malware[.]example/a.exe` e `198.51.100[.]23`.
4. Casos abertos com situação e próximo passo, quem espera o quê, pendências com terceiros e alertas de contexto (manutenções, ruídos).
5. O que aconteceu, o impacto, o que está sendo feito, o que ele precisa fazer e quando vem a próxima atualização.

</details>
