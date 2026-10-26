<!-- descricao: Quando um incidente envolve dados pessoais, o relógio começa a correr. O que o N1 precisa reconhecer e fazer. -->
# Módulo 11: LGPD para o analista N1

<p class="sub">O N1 não decide se a empresa comunica a ANPD. Mas, se ele não reconhece o caso e não escala a tempo, ninguém decide nada dentro do prazo.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - o que é dado pessoal e dado pessoal sensível;
    - quem é quem na LGPD: titular, controlador, operador e encarregado;
    - o que é um incidente de segurança com dados pessoais (inclusive os que não são vazamento);
    - por que existe um **prazo** e quando ele começa a contar;
    - quais critérios tornam um incidente relevante;
    - o que o N1 deve (e não deve) fazer quando um caso envolve dados pessoais.

!!! atencao "Este módulo não é consultoria jurídica"
    O objetivo é que você **reconheça** casos com dados pessoais e os encaminhe certo. Quem avalia juridicamente e decide sobre comunicações é a encarregada (DPO) com o jurídico da empresa.

## 1. Por que isso é assunto do SOC

A **LGPD** (Lei Geral de Proteção de Dados, Lei nº 13.709/2018) obriga as empresas a proteger dados pessoais e, quando acontece um incidente que pode causar risco ou dano relevante às pessoas, a **comunicar a ANPD** (Autoridade Nacional de Proteção de Dados) e os **titulares** afetados.

Quem descobre o incidente, quase sempre, é o SOC. E a regulamentação da ANPD define um **prazo curto** para a comunicação. Cada hora que um caso com dados pessoais fica parado na fila do N1 é uma hora a menos para a empresa avaliar, investigar e decidir.

## 2. Os conceitos

### Dado pessoal

Qualquer informação relacionada a uma **pessoa natural identificada ou identificável**. Não é só nome e CPF:

- nome, CPF, RG, e-mail, telefone, endereço;
- IP associado a uma pessoa, identificador de dispositivo, geolocalização;
- matrícula de funcionário, placa de veículo, conta bancária;
- foto, gravação de voz, hábitos de navegação ligados a alguém.

### Dado pessoal sensível

Uma categoria com proteção reforçada: origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou organização religiosa, filosófica ou política, dados de **saúde** ou vida sexual, dados **genéticos** ou **biométricos**, quando vinculados a uma pessoa.

Na Pantera Logística, exemplos reais estariam no RH: atestados médicos (saúde), filiação sindical, digitais do ponto eletrônico (biometria).

### Quem é quem

| Papel | Quem é | Na Pantera Logística |
|---|---|---|
| **Titular** | a pessoa a quem os dados se referem | clientes, colaboradores, motoristas |
| **Controlador** | quem decide como e por que os dados são tratados | a própria Pantera Logística |
| **Operador** | quem trata dados em nome do controlador | a empresa que processa a folha de pagamento |
| **Encarregado (DPO)** | o canal entre a empresa, os titulares e a ANPD | a encarregada de proteção de dados |

## 3. O que é um incidente de segurança com dados pessoais

Não é só "vazamento". A regulamentação da ANPD trata como incidente qualquer **evento adverso confirmado** que viole a **confidencialidade**, a **integridade**, a **disponibilidade** ou a **autenticidade** de dados pessoais.

| Propriedade violada | Exemplo no SOC |
|---|---|
| **Confidencialidade** | planilha de clientes enviada para fora; acesso indevido a pasta do RH |
| **Integridade** | dados bancários de fornecedores alterados por um invasor |
| **Disponibilidade** | **ransomware** criptografou o servidor com as fichas dos colaboradores |
| **Autenticidade** | e-mails falsos enviados em nome da empresa usando dados de clientes |

!!! erro "Erro comum de N1"
    Achar que ransomware "não tem LGPD" porque "ninguém levou os dados, só criptografou". Indisponibilidade de dados pessoais também é incidente. E muitos grupos de ransomware hoje **copiam os dados antes** de criptografar, para chantagear com a divulgação.

## 4. O prazo e a relevância

A **Resolução CD/ANPD nº 15/2024** (Regulamento de Comunicação de Incidente de Segurança) estabelece, entre outros pontos:

- o controlador deve comunicar à ANPD e aos titulares o incidente que possa acarretar **risco ou dano relevante**, no prazo de **3 (três) dias úteis**, contados do **conhecimento** de que o incidente afetou dados pessoais;
- o incidente é considerado relevante quando puder **afetar significativamente** interesses e direitos fundamentais dos titulares **e** envolver pelo menos um destes critérios:
    - dados pessoais **sensíveis**;
    - dados de **crianças, adolescentes ou idosos**;
    - dados **financeiros**;
    - dados de **autenticação** em sistemas (senhas, tokens);
    - dados protegidos por **sigilo** legal, judicial ou profissional;
    - dados em **larga escala**;
- o controlador deve manter um **registro de todos os incidentes**, inclusive os que não forem comunicados, por no mínimo **5 anos**.

Três dias úteis é **muito pouco tempo** para descobrir o que aconteceu, quais dados foram afetados, quantas pessoas, e decidir. É por isso que o encaminhamento rápido pelo SOC faz diferença.

## 5. O papel do N1

### O que fazer

1. **Reconhecer**: em todo incidente confirmado ou provável, pergunte: *há dados pessoais nos sistemas, arquivos ou contas envolvidos?*
2. **Registrar no ticket** o que se sabe sobre os dados, sem exagerar nem minimizar:
    - quais sistemas, pastas ou bases foram afetados;
    - que **tipos** de dados existem lá (cadastro, financeiro, saúde, senhas...);
    - estimativa de **volume** e de **quem** são os titulares (clientes, colaboradores, crianças?);
    - se há indício de **cópia, alteração, indisponibilidade** ou **acesso**;
    - **quando** o SOC tomou conhecimento.
3. **Escalar pelo canal definido** no playbook, sinalizando "possível envolvimento de dados pessoais". Na Pantera Logística, isso significa escalar ao N2 **e** acionar a encarregada.
4. **Preservar as evidências**: não apagar, não "limpar", não reinstalar nada por conta própria.

### O que não fazer

- **Não decidir** se é ou não caso de comunicação. Isso é da encarregada e do jurídico.
- **Não contatar** a ANPD, os titulares, clientes ou a imprensa.
- **Não especular por escrito** ("vazaram os dados de todos os clientes!") sem base. O ticket pode virar documento num processo.
- **Não abrir ou copiar** os dados pessoais além do estritamente necessário para entender o incidente. Investigar um vazamento não justifica ler as fichas médicas dos colaboradores.
- **Não comentar** o caso fora do SOC.

!!! atacante "Como o atacante pensa"
    Para um criminoso, dados pessoais são produto: bases de clientes são vendidas, dados de funcionários alimentam golpes direcionados (o "golpe do falso RH", o "falso boleto do fornecedor"), e a ameaça de divulgação vira chantagem. Quanto mais sensível o dado, maior o valor e maior o dano para as pessoas.

## 6. Lab: tem LGPD aqui?

!!! cenario "Cenário"
    Para cada situação abaixo, responda: (a) há dados pessoais envolvidos? (b) qual propriedade foi violada? (c) algum critério de relevância parece presente? (d) o que você escreve no ticket para a encarregada?

1. O Wazuh mostra que a conta de serviço do sistema de rastreamento fez download, às 3h, de uma exportação com nome, CPF, telefone e endereço de **120 mil clientes**, enviada para um IP externo.
2. Ransomware criptografou o servidor de arquivos do RH, onde ficam fichas de admissão, atestados médicos e dados bancários para pagamento dos 800 colaboradores. Não há backup recente.
3. Um analista de marketing enviou por engano uma planilha com o **e-mail de 35 clientes** para outro cliente.
4. Um atacante usou credenciais roubadas para entrar no painel do site e **alterou o texto da página inicial** (sem acesso à base de clientes, que fica em outro servidor).
5. Um phishing levou 12 motoristas a digitarem **usuário e senha** do aplicativo de entregas da empresa num site falso.

<details markdown="1">
<summary>Ver uma resolução comentada</summary>

1. **(a)** Sim, dados cadastrais de clientes. **(b)** Confidencialidade (cópia e envio para fora). **(c)** Larga escala (120 mil titulares); CPF e endereço aumentam o risco de fraude. **(d)** "Possível exfiltração de base de clientes: ~120 mil registros com nome, CPF, telefone e endereço, enviada para IP externo X às 03:xx; conta de serviço Y; conhecimento pelo SOC em [data e hora]." Escalar imediatamente ao N2 e à encarregada.
2. **(a)** Sim, inclusive **sensíveis** (atestados = saúde) e **financeiros** (dados bancários). **(b)** **Disponibilidade** (e talvez confidencialidade, se houve cópia antes). **(c)** Dados sensíveis e financeiros. **(d)** Registrar os tipos de dados no servidor, a ausência de backup, o número de colaboradores, e se há indício de cópia antes da criptografia (tráfego de saída incomum nos dias anteriores). Escalar imediatamente.
3. **(a)** Sim, e-mails de clientes. **(b)** Confidencialidade. **(c)** Pequeno volume, sem dados sensíveis, financeiros ou de autenticação; aparentemente sem critério de relevância, mas **quem avalia é a encarregada**. **(d)** Registrar o que foi enviado, para quem, quantos titulares, e se o destinatário foi contatado para apagar. O incidente entra no **registro** mesmo que não seja comunicado.
4. **(a)** Pela descrição, não houve dado pessoal afetado (o texto da página não é dado pessoal e a base está em outro servidor). **(b)** Integridade do site. **(c)** Não se aplica, se confirmado. **(d)** Registrar que a base de clientes **não** foi acessada **e como isso foi verificado**. Atenção: a credencial roubada é de quem? Se for de um colaborador, aquela credencial é dado pessoal de autenticação comprometido. Na dúvida, informe a encarregada.
5. **(a)** Sim, credenciais de 12 motoristas. **(b)** Confidencialidade. **(c)** **Dados de autenticação** é um dos critérios. **(d)** Registrar as 12 contas, quando foram digitadas, se houve uso das credenciais depois (logons de IPs estranhos), e as ações tomadas (troca de senha forçada). Escalar.

</details>

## Checagem

1. O que é dado pessoal sensível? Dê três exemplos.
2. Ransomware que só criptografou dados pessoais é incidente de segurança? Por quê?
3. Qual o prazo previsto na regulamentação para a comunicação, e a partir de quando ele conta?
4. Cite quatro critérios que tornam um incidente potencialmente relevante.
5. O N1 deve avisar os clientes afetados? Justifique.
6. Por que o horário em que o SOC tomou conhecimento é tão importante no ticket?

<details markdown="1">
<summary>Ver respostas</summary>

1. Dado sobre origem racial ou étnica, religião, opinião política, filiação sindical, saúde, vida sexual, dado genético ou biométrico, vinculado a uma pessoa. Exemplos: atestado médico, digital do ponto, filiação ao sindicato.
2. Sim. Incidente de segurança inclui a violação da **disponibilidade**, não só da confidencialidade. Além disso, é comum que os dados sejam copiados antes da criptografia.
3. **3 dias úteis**, contados do conhecimento, pelo controlador, de que o incidente afetou dados pessoais.
4. Quaisquer quatro: dados sensíveis; de crianças, adolescentes ou idosos; financeiros; de autenticação; protegidos por sigilo; em larga escala.
5. Não. A comunicação aos titulares é decisão e responsabilidade do controlador, conduzida pela encarregada e pelo jurídico, com conteúdo e momento definidos por eles. O N1 registra e escala.
6. Porque o prazo conta a partir do conhecimento. O registro preciso de quando o SOC identificou o envolvimento de dados pessoais ajuda a empresa a cumprir e a demonstrar o cumprimento do prazo.

</details>

!!! dica "Para ir além"
    - Leia a LGPD (Lei nº 13.709/2018), em especial os artigos 5º (definições), 46 (segurança) e 48 (comunicação de incidentes).
    - Leia a Resolução CD/ANPD nº 15/2024 e o material de orientação da ANPD sobre comunicação de incidentes, no site da ANPD (gov.br/anpd).
