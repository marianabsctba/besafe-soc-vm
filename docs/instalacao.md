<p align="center">
  <img src="img/pantera.png" width="110" alt="Pantera Be Safe">
</p>

# Instalando o Be Safe SOC Lab, passo a passo

Este guia é para quem **nunca usou uma máquina virtual**. Siga na ordem e não pule a parte de conferir os arquivos: ela evita a maioria dos problemas.

> **Resumo para quem tem pressa:** confira os requisitos (passos 1 e 2), rode o **instalador automático** (passo 3) e ligue a VM. Login `analista` / `analista`.

---

## 0. Entendendo o que você vai baixar

- **Máquina virtual (VM)** é um computador inteiro que roda dentro do seu, como se fosse um programa. O que acontece lá dentro não afeta o seu computador.
- **OVA** é o arquivo que carrega a VM pronta: sistema, ferramentas e treinamento já instalados. Não é uma ISO. Uma ISO é um instalador, e você teria que instalar tudo do zero. A OVA você só **importa** e liga.
- O GitHub não aceita arquivos maiores que 2 GB, então a OVA (vários GB) foi **dividida em partes**. Você baixa as partes e junta de volta com um comando.

---

## 1. Seu computador aguenta?

| | Mínimo | Recomendado |
|---|---|---|
| Memória RAM do computador | 8 GB (sem a IA local) | **16 GB ou mais** |
| Processador | 64 bits com virtualização, 4 núcleos | 6 núcleos ou mais |
| Espaço livre em disco | **60 GB** | 80 GB, de preferência SSD |
| Sistema | Windows 10/11, Linux ou Mac com processador Intel | |

Sobre o espaço em disco: são uns 15 GB durante a instalação (partes + OVA juntada, que você pode apagar depois) e a VM importada ocupa cerca de 20 GB no começo e pode crescer até uns 45 GB com o uso.

> [!WARNING]
> **Mac com chip Apple (M1, M2, M3, M4)**
> A VM é feita para processadores **x86 (Intel e AMD)**. Ela **não roda** em Macs com chip Apple. Em Mac com processador Intel funciona no VMware Fusion.

### Confira se a virtualização está ligada

Sem isso a VM não liga ou fica extremamente lenta.

**No Windows:** abra o **Gerenciador de Tarefas** (`Ctrl` + `Shift` + `Esc`) > aba **Desempenho** > **CPU**. Embaixo do gráfico deve aparecer **Virtualização: Habilitado**.

Se aparecer **Desabilitado**, é preciso ligar na BIOS/UEFI do computador:

1. Reinicie e entre na BIOS (geralmente `F2`, `Del`, `F10` ou `Esc` logo ao ligar; procure "tecla BIOS" + o modelo do seu computador).
2. Procure uma opção chamada **Intel Virtualization Technology**, **VT-x**, **SVM Mode** ou **AMD-V** (costuma ficar em *Advanced*, *CPU Configuration* ou *Security*).
3. Mude para **Enabled**, salve (geralmente `F10`) e reinicie.

**No Linux:** rode `egrep -c '(vmx|svm)' /proc/cpuinfo`. Qualquer número acima de 0 indica suporte; se a VM reclamar mesmo assim, ligue na BIOS como acima.

---

## 2. Instale um programa de virtualização

Escolha **um**. Se você não tiver nenhum, o instalador automático (passo 3) **oferece instalar o VirtualBox** para você: no Windows pelo `winget`, no Ubuntu pelo `apt` e no Mac pelo Homebrew. O VMware precisa ser instalado na mão, porque o download exige cadastro no site da Broadcom.

| Programa | Quando usar |
|---|---|
| **VMware Workstation Pro** (gratuito para uso pessoal) | **Recomendado no Windows**, principalmente se você usa WSL, Docker Desktop ou Hyper-V. Baixe no site da Broadcom (pede um cadastro gratuito). No Mac Intel, o equivalente é o **VMware Fusion**. |
| **VirtualBox 7** (gratuito, virtualbox.org) | Funciona bem em Linux e em Windows **sem** WSL, Docker ou Hyper-V. |

> [!TIP]
> **Usa WSL ou Docker Desktop no Windows?**
> Eles ligam o Hyper-V, e o VirtualBox fica muito lento ou trava nesse cenário (aparece uma tartaruga verde no canto da janela da VM). Use o **VMware**, que convive bem com o Hyper-V.

---

## 3. Jeito fácil: o instalador automático (recomendado)

O instalador faz sozinho os passos chatos: confere se o seu computador aguenta, oferece instalar o VirtualBox se você ainda não tiver nenhum programa de virtualização, baixa as partes (e continua de onde parou se a internet cair), confere o hash de cada uma, baixa de novo a que vier corrompida, junta tudo numa OVA, confere a OVA e importa no VMware ou no VirtualBox. Se o seu computador tiver menos de 16 GB de RAM, ele já ajusta a VM para 5 GB.

> [!IMPORTANT]
> **Leia antes de rodar.** Copiar da internet um comando que baixa e já executa um script é exatamente o que um atacante quer que você faça. Por isso aqui é diferente: você baixa o script, **abre num editor de texto e lê** (ele é curto e comentado em português) e só então roda. Ele só baixa arquivos de dados do release; nada baixado da internet é executado. Pegue esse hábito para a vida, bebê: é o primeiro reflexo de quem trabalha com segurança.

### No Windows

1. Na página do release mais recente, em **Assets**, baixe o **`instalar-besafe.ps1`**. Ele também está no repositório, na pasta [`instalar`](../instalar).
2. Abra o arquivo no Bloco de Notas e leia.
3. Na pasta onde ele foi salvo (geralmente **Downloads**), clique com o botão direito num espaço vazio > **Abrir no Terminal** e rode:

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar-besafe.ps1
```

O Windows bloqueia scripts baixados por padrão. O `-ExecutionPolicy Bypass` libera **só esta execução**, sem mudar nenhuma configuração do sistema.

Os downloads vão para a pasta `BeSafe` dentro da sua pasta de usuário. Para usar outro disco, acrescente `-Pasta D:\BeSafe` no fim do comando.

### No Linux e no Mac (Intel)

1. Baixe o **`instalar-besafe.sh`** dos **Assets** do release (ou da pasta [`instalar`](../instalar) do repositório).
2. Leia: `less instalar-besafe.sh`
3. Rode:

```bash
bash instalar-besafe.sh
```

Para usar outro disco: `bash instalar-besafe.sh --pasta /caminho/BeSafe`.

### Quando ele terminar

- Se ele importou no **VMware**, a VM abre sozinha no VMware (ou fica na pasta que ele mostrar). Clique em **Power on**.
- Se importou no **VirtualBox**, abra o VirtualBox, selecione **Be Safe SOC Lab** e clique em **Iniciar**.
- Se não encontrou nenhum dos dois e você não quis instalar o VirtualBox, ele avisa onde a OVA ficou: instale o VMware ou o VirtualBox e importe como no passo 4.4.
- No Linux, se o computador usa **Secure Boot**, o Ubuntu pode pedir para registrar uma chave (MOK) ao instalar o VirtualBox. No próximo boot aparece uma tela azul: escolha **Enroll MOK**, digite a senha que você criou e reinicie.

Agora pule para o **passo 5 (Primeiro boot)**.

---

## 4. Jeito manual, passo a passo

Prefere fazer na mão, ou o instalador deu algum erro? Siga daqui.

### 4.1 Baixe as partes

1. Abra a página de **Releases** do repositório e entre na versão mais recente.
2. Em **Assets**, baixe **todos** estes arquivos para a **mesma pasta** (por exemplo `Downloads\besafe`):
    - todas as partes: `besafe-soc-lab-<versão>.ova.part01`, `part02`, `part03`... (a quantidade está na página do release);
    - o `SHA256SUMS.txt`.
3. Espere **todos** os downloads terminarem. Um arquivo pela metade é a causa número 1 de erro na importação.

Não tente abrir uma parte sozinha: nenhuma delas funciona isolada.

---

### 4.2 Confira se os arquivos chegaram inteiros

Cada arquivo tem uma "impressão digital" (hash SHA-256) publicada no `SHA256SUMS.txt`. Se o hash calculado no seu computador for igual ao publicado, o arquivo chegou perfeito. Analista de SOC confere hash. Comece agora. 😉

**Windows (PowerShell):** clique com o botão direito na pasta dos downloads > **Abrir no Terminal** e rode:

```powershell
Get-FileHash .\besafe-soc-lab-*.part* -Algorithm SHA256 | Format-Table Hash, Path
Get-Content .\SHA256SUMS.txt
```

Compare cada hash da primeira lista com o da segunda (pode comparar o começo e o fim de cada um).

**Linux:**

```bash
sha256sum -c SHA256SUMS.txt --ignore-missing
```

Todas as linhas devem terminar em `OK`.

**Mac:**

```bash
shasum -a 256 -c SHA256SUMS.txt --ignore-missing
```

Se algum hash não bater, **baixe aquela parte de novo**.

---

### 4.3 Junte as partes numa OVA

Os comandos abaixo usam a versão 0.2.0 como exemplo. Troque pelo número da versão que você baixou.

**Windows:** na mesma pasta, abra o **Prompt de Comando** (digite `cmd` na barra de endereço do Explorador de Arquivos e aperte Enter) e rode:

```bat
copy /b besafe-soc-lab-0.2.0.ova.part01 + besafe-soc-lab-0.2.0.ova.part02 + besafe-soc-lab-0.2.0.ova.part03 + besafe-soc-lab-0.2.0.ova.part04 besafe-soc-lab-0.2.0.ova
```

Liste **todas** as partes, em ordem, separadas por `+`. O comando exato da versão está nas notas do release, é só copiar e colar.

Está no PowerShell em vez do Prompt de Comando? Coloque `cmd /c` antes do comando.

**Linux e Mac:**

```bash
cat besafe-soc-lab-0.2.0.ova.part* > besafe-soc-lab-0.2.0.ova
```

Confira o resultado: a OVA juntada também tem o hash dela no `SHA256SUMS.txt`. Rode o mesmo comando do passo 4.2 apontando para a `.ova`:

```powershell
Get-FileHash .\besafe-soc-lab-0.2.0.ova -Algorithm SHA256
```

Bateu? Pode apagar as partes para liberar espaço.

---

### 4.4 Importe a VM

#### No VMware Workstation (ou Fusion)

1. **File > Open** (Arquivo > Abrir) e escolha a `besafe-soc-lab-<versão>.ova`.
2. Dê um nome e escolha uma pasta com **pelo menos 50 GB livres**. Clique em **Import**.
3. Se aparecer um aviso sobre especificação OVF, clique em **Retry**. É normal.
4. A importação leva de 5 a 15 minutos.

#### No VirtualBox

1. **Arquivo > Importar Appliance** e escolha a `.ova`.
2. Na tela de configurações, em **Pasta Base da Máquina**, escolha um disco com **pelo menos 50 GB livres**.
3. Em **Política de Endereço MAC**, deixe **Gerar novos endereços MAC para todas as placas de rede**.
4. Clique em **Finalizar** e aguarde.

#### Ajuste a memória se o seu computador tiver 8 GB

A VM vem com **12 GB de RAM e 4 núcleos**. Num computador com 8 GB isso trava tudo. Antes de ligar:

- **VMware:** **Edit virtual machine settings > Memory** > `5 GB`. **Processors** > `2`.
- **VirtualBox:** **Configurações > Sistema** > Memória base `5120 MB` e, na aba Processador, `2` CPUs.

Com 5 GB, o Wazuh, as ferramentas e o treinamento funcionam. A IA local (mentor, entrevista e copiloto) precisa de mais memória: o Console vai mostrar as dicas escritas no lugar das respostas da IA.

---

## 5. Primeiro boot

1. Ligue a VM. Você vai ver a pantera da Be Safe.
2. O **primeiro** boot leva cerca de 1 minuto a mais: é quando a VM gera as senhas e a semente de cenários exclusivas da sua cópia. Não desligue no meio.
3. Na tela de login: usuário **`analista`**, senha **`analista`**.
4. O teclado já vem no padrão brasileiro **ABNT2** (com `ç`).

Na área de trabalho você encontra:

| Ícone | O que é |
|---|---|
| **Treinamento Be Safe** | os 14 módulos. **Comece pelo módulo 0.** |
| **CREDENCIAIS.txt** | usuário e senha do Wazuh desta cópia |
| **Wazuh** | o SIEM, em `https://localhost` |
| **Console Be Safe** | plantões, tickets, nota, prova final e certificado |
| **CyberChef** | decodificação offline |

O **Terminal** fica na barra inferior e também abre com `Ctrl` + `Alt` + `T`.

> [!TIP]
> **Tire um snapshot agora**
> Um **snapshot** é um "ponto de restauração" da VM. Se algo der errado mais tarde, você volta para ele em segundos.
>
> **VMware:** VM > Snapshot > Take Snapshot. **VirtualBox:** Máquina > Criar Snapshot.
> Dê o nome `limpa, primeiro boot`.

### O Wazuh vai mostrar um aviso de segurança. É esperado.

Ao abrir `https://localhost`, o Firefox avisa que a conexão "não é segura". Isso acontece porque o Wazuh usa um certificado gerado dentro da própria VM. Clique em **Avançado** e depois em **Prosseguir para localhost (arriscado)**, no fim da página. O módulo 0 explica em detalhe por que isso é normal aqui e **não** é normal num site da internet.

Logo depois de ligar a VM, o Wazuh pode levar **2 a 3 minutos** para ficar pronto. Se aparecer "Wazuh dashboard server is not ready yet", espere um pouco e recarregue.

---

## 6. Deu problema?

| O que aparece | O que fazer |
|---|---|
| "a execução de scripts foi desabilitada neste sistema" ao rodar o instalador | Faltou o começo do comando. Rode exatamente `powershell -ExecutionPolicy Bypass -File .\instalar-besafe.ps1` |
| O instalador parou no meio do download | Rode o mesmo comando de novo: ele continua de onde parou e confere tudo. |
| "VT-x is disabled", "AMD-V is disabled" ou "This host supports Intel VT-x, but it is disabled" | A virtualização está desligada na BIOS. Veja o passo 1. |
| VirtualBox muito lento, travando, tartaruga verde no canto | Hyper-V ligado (WSL, Docker Desktop). Use o VMware. |
| Erro ao importar, "invalid file", "checksum", "unexpected end of file" | A OVA está incompleta. Rode o instalador de novo (ele baixa só o que estiver errado) ou confira os hashes (passo 4.2), baixe a parte que não bateu e junte de novo. |
| O computador inteiro fica lento ao ligar a VM | Pouca RAM. Reduza para 5 GB e 2 núcleos (passo 4.4). Feche o navegador e outros programas pesados do seu computador. |
| "Not enough physical memory" | Mesma solução: reduza a memória da VM. |
| Tela da VM pequena | Maximize a janela ou use tela cheia (VMware: `Ctrl` + `Alt` + `Enter`; VirtualBox: `Host` + `F`). A resolução se ajusta sozinha. |
| O mouse ficou "preso" dentro da VM | VMware: `Ctrl` + `Alt`. VirtualBox: tecla `Ctrl` da direita. |
| Wazuh não abre ou dá erro de login | Espere 3 minutos depois do boot. A senha certa está no **CREDENCIAIS.txt** da área de trabalho (ela é diferente em cada cópia). |
| Mentor/IA demora na primeira pergunta | Normal: o modelo carrega sob demanda. As próximas respostas são bem mais rápidas. |
| Esqueci o que fiz e quero recomeçar | Volte ao snapshot do passo 5. |

A VM **não precisa de internet**. Ela funciona totalmente offline, e isso é proposital: você vai lidar com arquivos que imitam ataques.

---

## 7. Próximo passo

Abra o **Treinamento Be Safe**, comece pelo **módulo 0** e siga na ordem. Quando chegar no módulo 13, faça plantões de treino no Console e, quando estiver confiante, a **prova final**: com nota 70 ou mais você gera o seu certificado.

Bons estudos e bom plantão. 🐾

<p align="center"><b>Powered By Mariana BS</b></p>
