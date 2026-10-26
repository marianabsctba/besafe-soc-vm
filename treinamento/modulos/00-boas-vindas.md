<!-- descricao: Conheça a VM, faça login no Wazuh e prepare seu caderno de anotações. -->
# Módulo 0: Boas-vindas

<p class="sub">Antes de investigar qualquer coisa, você precisa conhecer o seu posto de trabalho.</p>

!!! objetivo "Ao final deste módulo você vai saber"
    - entrar na VM e abrir o terminal;
    - encontrar a sua senha do Wazuh e fazer o primeiro login;
    - entender por que o navegador reclama do certificado (e por que aqui isso é normal);
    - onde ficam os arquivos dos labs;
    - montar o seu caderno de anotações de analista.

## 1. O que é esta VM

Uma **VM** (máquina virtual) é um computador inteiro rodando dentro do seu computador, como um programa. Tudo que acontece aqui dentro fica isolado: se você apagar algo importante, a sua máquina de verdade não sofre nada. Por isso ela é perfeita para treinar.

Esta VM roda **Ubuntu Linux** e simula a estação de trabalho de um analista de SOC. Dentro dela já estão:

| O que | Para que serve no dia a dia |
|---|---|
| **Wazuh** | o SIEM: a central onde os alertas de toda a empresa chegam |
| **Suricata** | o IDS: vigia o tráfego de rede e acusa padrões de ataque |
| **Wireshark / tshark** | abrir e examinar tráfego de rede pacote por pacote |
| **Hayabusa / Chainsaw** | procurar sinais de ataque em logs de Windows |
| **CyberChef** | decodificar textos escondidos (base64, URL, etc.) |
| **oletools, pdfid, exiftool, YARA** | examinar anexos suspeitos sem abri-los |

Não se preocupe se esses nomes ainda não significam nada. Cada um tem o seu módulo.

!!! atencao "A VM funciona sem internet"
    Tudo foi pensado para funcionar offline. Isso é proposital: você vai mexer com arquivos que imitam ataques, e o ideal é que nada disso tenha caminho para fora.

## 2. Primeiro acesso

1. Ligue a VM. Você vai ver a pantera da Be Safe no boot e depois a tela de login.
2. Entre com o usuário **`analista`** e a senha **`analista`**.
3. Na área de trabalho, abra o **Terminal** (ícone na barra inferior, ou `Ctrl` + `Alt` + `T`).

O terminal vai mostrar um banner rosa com os endereços importantes e um *prompt* parecido com este:

```
analista@besafe:~$
```

Isso quer dizer: você é o usuário `analista`, na máquina `besafe`, dentro da sua pasta pessoal (o `~`), e o `$` indica que o terminal está esperando um comando. No módulo 1 você vai aprender a usar o terminal de verdade. Por enquanto, só um comando.

## 3. Sua senha do Wazuh

Cada cópia desta VM gera, no primeiro boot, uma senha própria para o Wazuh. Assim ninguém tem a mesma senha que você. Ela aparece em três lugares:

- no arquivo **CREDENCIAIS.txt**, na área de trabalho;
- no fim do banner rosa, toda vez que você abre um terminal;
- no arquivo `~/.besafe/wazuh.txt`, que você pode ler assim:

```bash
cat ~/.besafe/wazuh.txt
```

Você vai ver algo assim (a senha será outra):

```
Wazuh dashboard: https://localhost
usuario: admin
senha: Xk3.p9...
```

!!! erro "Erro comum de N1"
    Copiar a senha para um bloco de notas na área de trabalho, mandar por chat ou colar num ticket. Credencial nunca vai para lugar nenhum além do campo de login. No mundo real, uma senha de SIEM vazada dá ao atacante uma visão completa do que a defesa enxerga.

## 4. Primeiro login no Wazuh

1. Abra o **Firefox** e acesse `https://localhost`.
2. O Firefox vai mostrar **"Tenha cautela. Algo não parece estar certo."** Clique em **Avançado** e depois em **Prosseguir para localhost (arriscado)**, no fim da página.
3. Entre com o usuário `admin` e a senha do passo anterior.

### Por que apareceu o aviso de segurança?

Este é o seu primeiro conceito de segurança de verdade, então vale entender.

Quando você acessa um site com `https://`, o servidor apresenta um **certificado digital**: um documento que diz "eu sou o site X" e que foi **assinado por uma Autoridade Certificadora** (AC) em quem o seu navegador confia. É assim que o navegador sabe que está falando com o banco de verdade, e não com um impostor no meio do caminho.

O Wazuh desta VM usa um certificado **autoassinado**: ele mesmo se apresenta e ele mesmo assina. O navegador não tem como confirmar a identidade, por isso avisa. Aqui não há risco, porque o servidor está dentro da sua própria VM (`localhost` significa "esta máquina").

!!! atacante "Como o atacante pensa"
    Um atacante que consegue se colocar entre você e um site (numa rede Wi-Fi falsa, por exemplo) também apresenta um certificado que o navegador não reconhece. O aviso é exatamente o mesmo. Por isso a regra de ouro fora do laboratório é: **aviso de certificado num site que você usa todo dia é motivo para parar, não para clicar em "continuar"**. No SOC, usuários que relatam esse aviso podem estar diante de um ataque de interceptação.

## 5. Onde ficam os labs

Os arquivos de exercício estão em `~/labs`, organizados por módulo:

```bash
ls ~/labs
```

Os logs reais de ataques a Windows, usados nos módulos 3 e 7, ficam em:

```
/opt/besafe/chainsaw/EVTX-ATTACK-SAMPLES
```

Esses arquivos vêm do projeto público **EVTX-ATTACK-SAMPLES**, de Samir Bousseaden, distribuído sob a licença GPL-3.0. São registros gravados em máquinas Windows durante ataques reais de laboratório.

## 6. Seu caderno de anotações

Analistas experientes anotam **tudo**: o comando que funcionou, o Event ID que significa logon de rede, o filtro do Wazuh que achou o ataque. Daqui a três meses, num plantão de madrugada, essa anotação vale ouro.

Crie o seu caderno agora:

```bash
mkdir -p ~/caderno
mousepad ~/caderno/anotacoes.md &
```

O `mousepad` é um editor de texto simples. O `&` no final faz ele abrir sem prender o terminal.

Sugestão de estrutura para o caderno:

```markdown
# Caderno do analista

## Comandos que uso sempre

## Event IDs do Windows

## Filtros úteis no Wazuh

## Dúvidas para pesquisar
```

## 7. Se algo der errado

| Problema | O que fazer |
|---|---|
| O Wazuh não abre ou fica carregando | Logo depois de ligar a VM ele leva de 2 a 4 minutos para subir. Espere e recarregue. |
| Ainda não abre depois de 5 minutos | No terminal: `sudo systemctl restart wazuh-dashboard` (a senha do sudo é `analista`). |
| Esqueci a senha do Wazuh | arquivo **CREDENCIAIS.txt** na área de trabalho, ou `cat ~/.besafe/wazuh.txt` |
| A VM está lenta | Feche abas do Firefox que não está usando e confirme que a VM tem pelo menos 8 GB de RAM. |

## Checagem

1. Por que a senha do Wazuh é diferente em cada cópia da VM?
2. O que significa `localhost`?
3. Num computador da empresa, um usuário liga dizendo que o site do banco mostrou um aviso de certificado. O que isso pode indicar?

<details markdown="1">
<summary>Ver respostas</summary>

1. Para que ninguém conheça a senha de outra pessoa. Se todas as cópias tivessem a mesma senha, bastaria uma pessoa publicar a dela para todas as VMs ficarem vulneráveis. É o mesmo motivo pelo qual equipamentos de rede modernos não saem de fábrica com a senha "admin".
2. "Esta máquina." Quando você acessa `https://localhost`, o navegador conversa com um serviço rodando no próprio computador, sem passar pela rede.
3. Pode ser um problema inofensivo (relógio do computador errado, por exemplo), mas também pode ser uma tentativa de **interceptação**: alguém entre o usuário e o banco apresentando um certificado falso. Vale registrar, perguntar em que rede o usuário estava (Wi-Fi de hotel, aeroporto?) e escalar se houver qualquer sinal de que ele digitou a senha.

</details>

!!! dica "Para ir além"
    Pesquise como funciona a "cadeia de certificados" no HTTPS. No Firefox, clique no cadeado de qualquer site conhecido e em "Conexão segura" > "Mais informações" > "Ver certificado". Veja quem assinou o certificado e quem assinou quem assinou.
