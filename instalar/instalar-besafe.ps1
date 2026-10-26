<#
  Be Safe SOC Lab: baixa, confere e importa a VM no Windows.

  Como rodar (no PowerShell, dentro da pasta onde você salvou este arquivo):

      powershell -ExecutionPolicy Bypass -File .\instalar-besafe.ps1

  O "-ExecutionPolicy Bypass" vale só para esta execução: nenhuma configuração do Windows é alterada.

  O que este script faz, em ordem:
    1. confere se o computador tem memória, disco e virtualização para a VM;
       se não houver VMware nem VirtualBox, oferece instalar o VirtualBox pelo winget (só com o seu "sim");
    2. consulta o último release no GitHub;
    3. baixa as partes da OVA e o SHA256SUMS.txt (se a internet cair, rode de novo: ele continua de onde parou);
    4. confere o SHA-256 de cada parte e baixa de novo a que vier corrompida;
    5. junta as partes numa OVA e confere o SHA-256 dela;
    6. importa a VM no VMware ou no VirtualBox, se encontrar algum instalado.

  Ele só baixa arquivos de dados do release. Nada baixado da internet é executado.

  Opções:
    -Pasta D:\BeSafe    onde salvar os downloads (padrão: BeSafe dentro da sua pasta de usuário)
    -Versao 0.2.0       uma versão específica em vez da mais recente
    -SemImportar        só baixa, confere e junta; a importação fica com você
    -ManterPartes       não apaga as partes depois de juntar

  Powered By Mariana BS
#>
param(
  [string]$Pasta = (Join-Path $env:USERPROFILE "BeSafe"),
  [string]$Versao = "latest",
  [switch]$SemImportar,
  [switch]$ManterPartes,
  [string]$Api = "https://api.github.com/repos/marianabsctba/besafe-soc-vm/releases"
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Passo($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Magenta }
function Ok($t) { Write-Host "   [ok] $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "   [atenção] $t" -ForegroundColor Yellow }
function Falha($t) { Write-Host ""; Write-Host "ERRO: $t" -ForegroundColor Red; Write-Host ""; exit 1 }
function Sha256($arquivo) { (Get-FileHash -Algorithm SHA256 $arquivo).Hash.ToLower() }

Write-Host ""
Write-Host "  BE SAFE SOC LAB  |  instalador" -ForegroundColor Magenta
Write-Host "  Powered By Mariana BS" -ForegroundColor DarkMagenta

# ------------------------------------------------------------------ 1. o computador aguenta?
Passo "Conferindo o seu computador"
if (-not [Environment]::Is64BitOperatingSystem) { Falha "A VM precisa de um Windows de 64 bits." }
if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) {
  Falha "Não encontrei o curl.exe. Ele vem no Windows 10 (versão 1803 ou mais nova) e no Windows 11. Atualize o Windows ou siga o guia manual."
}
$sistema = Get-CimInstance Win32_ComputerSystem
$ramGB = [math]::Round($sistema.TotalPhysicalMemory / 1GB)
$poucaRam = $ramGB -lt 15
if ($ramGB -lt 7) { Falha "Este computador tem $ramGB GB de RAM. A VM precisa de pelo menos 8 GB." }
if ($poucaRam) { Aviso "$ramGB GB de RAM: a VM vai ser configurada com 5 GB e 2 núcleos (sem a IA local)." }
else { Ok "$ramGB GB de RAM" }

$hyperv = [bool]$sistema.HypervisorPresent
$virt = (Get-CimInstance Win32_Processor | Select-Object -First 1).VirtualizationFirmwareEnabled
if ($hyperv) { Ok "virtualização ativa (Hyper-V ligado: prefira o VMware ao VirtualBox)" }
elseif ($virt) { Ok "virtualização ligada na BIOS" }
else { Aviso "a virtualização parece DESLIGADA na BIOS. A VM não vai ligar até você ativar (veja o passo 1 do guia)." }

function Primeiro($caminhos) { $caminhos | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1 }
function AcharVirtualizadores {
  $pf86 = ${env:ProgramFiles(x86)}
  $script:ovftool = Primeiro @("$pf86\VMware\VMware Workstation\OVFTool\ovftool.exe", "$pf86\VMware\VMware Player\OVFTool\ovftool.exe",
                               "$env:ProgramFiles\VMware\VMware Workstation\OVFTool\ovftool.exe")
  $script:vmware = Primeiro @("$pf86\VMware\VMware Workstation\vmware.exe", "$pf86\VMware\VMware Player\vmplayer.exe",
                              "$env:ProgramFiles\VMware\VMware Workstation\vmware.exe")
  $script:vbox = Primeiro @("$env:VBOX_MSI_INSTALL_PATH\VBoxManage.exe", "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe")
}
AcharVirtualizadores
if ($ovftool) { Ok "VMware encontrado" }
if ($vbox) { Ok "VirtualBox encontrado" }

# sem nenhum programa de virtualizacao: oferece instalar o VirtualBox agora, antes do download longo
if (-not $SemImportar -and -not $ovftool -and -not $vbox) {
  Aviso "não encontrei o VMware nem o VirtualBox."
  if ($hyperv) {
    Write-Host "   Este computador usa Hyper-V (WSL, Docker Desktop). O VirtualBox fica muito lento nesse cenário."
    Write-Host "   O recomendado é instalar o VMware Workstation Pro (gratuito, site da Broadcom) e rodar este script de novo."
  }
  if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
    Write-Host "   Instale o VMware ou o VirtualBox e rode este script de novo. Vou continuar só com o download."
  } else {
    $padrao = if ($hyperv) { "n" } else { "S" }
    $r = Read-Host "   Instalar o VirtualBox (gratuito, da Oracle) agora pelo winget? O Windows vai pedir permissão de administrador. [S/n, padrão $padrao]"
    if (-not $r) { $r = $padrao }
    if ($r -match '^[sSyY]') {
      Passo "Instalando o VirtualBox"
      Write-Host "   Ao continuar, você aceita a licença do VirtualBox (Oracle) e os termos do winget."
      & winget.exe install --id Oracle.VirtualBox --exact --silent --accept-package-agreements --accept-source-agreements
      AcharVirtualizadores
      if ($vbox) { Ok "VirtualBox instalado" }
      else { Aviso "o VirtualBox não foi instalado. Vou continuar só com o download; depois importe a OVA manualmente." }
    }
  }
}

# ------------------------------------------------------------------ 2. release
Passo "Consultando o release no GitHub"
$url = if ($Versao -eq "latest") { "$Api/latest" } else { "$Api/tags/v$Versao" }
try { $release = Invoke-RestMethod $url -Headers @{ "User-Agent" = "besafe-instalador" } }
catch { Falha "Não consegui consultar o GitHub ($url). Confira a internet e tente de novo." }
$ver = $release.tag_name -replace '^v', ''
$partes = @($release.assets | Where-Object { $_.name -match '\.ova\.part\d+$' } | Sort-Object name)
$somas = $release.assets | Where-Object { $_.name -eq "SHA256SUMS.txt" }
if ($partes.Count -eq 0 -or -not $somas) { Falha "O release $($release.tag_name) não tem as partes da OVA ou o SHA256SUMS.txt." }
$nomeOva = $partes[0].name -replace '\.part\d+$', ''
$tamanho = ($partes | Measure-Object size -Sum).Sum
Ok ("versão {0}: {1} partes, {2:N1} GB no total" -f $ver, $partes.Count, ($tamanho / 1GB))

New-Item -ItemType Directory -Force $Pasta | Out-Null
$Pasta = (Resolve-Path $Pasta).Path
$livre = (Get-PSDrive (Split-Path -Qualifier $Pasta).TrimEnd(':')).Free
$precisa = 2 * $tamanho + 25GB
if ($livre -lt $precisa) {
  Falha ("Espaço insuficiente em {0}: {1:N0} GB livres, precisa de uns {2:N0} GB (download, OVA e VM importada). Rode de novo com -Pasta apontando para outro disco, por exemplo: -Pasta D:\BeSafe" -f (Split-Path -Qualifier $Pasta), ($livre / 1GB), ($precisa / 1GB))
}
Ok ("{0:N0} GB livres em {1}" -f ($livre / 1GB), $Pasta)

# ------------------------------------------------------------------ 3 e 4. baixar e conferir
Passo "Baixando e conferindo as partes (pode levar um bom tempo)"
$arqSomas = Join-Path $Pasta "SHA256SUMS.txt"
& curl.exe -sSL --fail --retry 5 -o $arqSomas $somas.browser_download_url
if ($LASTEXITCODE -ne 0) { Falha "Não consegui baixar o SHA256SUMS.txt." }
$esperado = @{}
foreach ($linha in Get-Content $arqSomas) {
  if ($linha -match '^([0-9a-fA-F]{64})\s+\*?(.+)$') { $esperado[$Matches[2].Trim()] = $Matches[1].ToLower() }
}

$caminhoOva = Join-Path $Pasta $nomeOva
$ovaPronta = (Test-Path $caminhoOva) -and $esperado[$nomeOva] -and ((Sha256 $caminhoOva) -eq $esperado[$nomeOva])
if ($ovaPronta) { Ok "a OVA já estava baixada e conferida" }
else {
  foreach ($p in $partes) {
    $destino = Join-Path $Pasta $p.name
    if (-not $esperado[$p.name]) { Falha "O SHA256SUMS.txt não tem o hash de $($p.name)." }
    for ($tentativa = 1; $tentativa -le 3; $tentativa++) {
      if ((Test-Path $destino) -and (Sha256 $destino) -eq $esperado[$p.name]) { break }
      if ((Test-Path $destino) -and (Get-Item $destino).Length -ge $p.size) { Remove-Item $destino }  # inteiro, mas corrompido
      Write-Host "   baixando $($p.name)..."
      & curl.exe -L --fail --retry 5 --retry-delay 5 -C - -# -o $destino $p.browser_download_url
    }
    if ((Sha256 $destino) -ne $esperado[$p.name]) { Falha "$($p.name) continua chegando corrompida. Tente mais tarde ou baixe pelo navegador." }
    Ok "$($p.name) conferida"
  }

  # ---------------------------------------------------------------- 5. juntar
  Passo "Juntando as partes em $nomeOva"
  $saida = [IO.File]::Create($caminhoOva)
  try {
    foreach ($p in $partes) {
      $entrada = [IO.File]::OpenRead((Join-Path $Pasta $p.name))
      try { $entrada.CopyTo($saida, 8MB) } finally { $entrada.Close() }
    }
  } finally { $saida.Close() }
  if ($esperado[$nomeOva]) {
    if ((Sha256 $caminhoOva) -ne $esperado[$nomeOva]) { Falha "A OVA juntada não bateu com o SHA256SUMS.txt. Apague a pasta $Pasta e rode de novo." }
    Ok "OVA conferida"
  }
  if (-not $ManterPartes) {
    foreach ($p in $partes) { Remove-Item (Join-Path $Pasta $p.name) }
    Ok "partes apagadas para liberar espaço"
  }
}

# ------------------------------------------------------------------ 6. importar
$nomeVm = "Be Safe SOC Lab $ver"

$escolha = $null
if ($SemImportar) { $escolha = "nenhum" }
elseif ($ovftool -and $vbox) {
  Write-Host ""
  $r = Read-Host "Encontrei o VMware e o VirtualBox. Importar em qual? [1] VMware (recomendado)  [2] VirtualBox"
  $escolha = if ($r -eq "2") { "vbox" } else { "vmware" }
}
elseif ($ovftool) { $escolha = "vmware" }
elseif ($vbox) { $escolha = "vbox" }
else { $escolha = "nenhum" }

if ($escolha -eq "vbox" -and $hyperv) { Aviso "com o Hyper-V ligado (WSL, Docker), o VirtualBox pode ficar muito lento. Se travar, use o VMware." }

if ($escolha -eq "vmware") {
  Passo "Importando no VMware (5 a 15 minutos)"
  $pastaVms = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Virtual Machines"
  $vmx = Join-Path $pastaVms "$nomeVm\$nomeVm.vmx"
  if (Test-Path $vmx) { Falha "Já existe uma VM em $(Split-Path $vmx). Apague ou renomeie essa pasta e rode de novo." }
  & $ovftool --acceptAllEulas "--name=$nomeVm" $caminhoOva $pastaVms
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $vmx)) { Falha "O VMware não conseguiu importar. Abra a OVA pelo menu File > Open do VMware." }
  if ($poucaRam) {
    (Get-Content $vmx) -replace '^memsize = .*', 'memsize = "5120"' -replace '^numvcpus = .*', 'numvcpus = "2"' | Set-Content $vmx -Encoding UTF8
  }
  Ok "VM importada em $(Split-Path $vmx)"
  if ($vmware) { Start-Process $vmware -ArgumentList "`"$vmx`"" }
}
elseif ($escolha -eq "vbox") {
  Passo "Importando no VirtualBox (5 a 15 minutos)"
  $opcoes = @("import", $caminhoOva, "--vsys", "0", "--vmname", $nomeVm)
  if ($poucaRam) { $opcoes += @("--memory", "5120", "--cpus", "2") }
  & $vbox @opcoes
  if ($LASTEXITCODE -ne 0) { Falha "O VirtualBox não conseguiu importar. Use Arquivo > Importar Appliance com a OVA." }
  Ok "VM importada no VirtualBox: abra o VirtualBox, selecione '$nomeVm' e clique em Iniciar"
}
else {
  Passo "Pronto para importar"
  if (-not $SemImportar) { Aviso "não encontrei o VMware nem o VirtualBox instalados." }
  Write-Host "   Abra a OVA no seu programa de virtualização:"
  Write-Host "     VMware:     File > Open"
  Write-Host "     VirtualBox: Arquivo > Importar Appliance"
}

Write-Host ""
Write-Host "   OVA: $caminhoOva" -ForegroundColor Gray
Write-Host "   (depois de importar e ligar a VM, você pode apagar a OVA para liberar espaço)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Login da VM: analista / analista" -ForegroundColor Magenta
Write-Host "  O primeiro boot leva 1 minuto a mais. Depois, abra o ícone Treinamento Be Safe." -ForegroundColor Magenta
Write-Host "  Bons estudos e bom plantão!" -ForegroundColor Magenta
Write-Host ""
