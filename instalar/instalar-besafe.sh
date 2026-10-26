#!/usr/bin/env bash
# Be Safe SOC Lab: baixa, confere e importa a VM no Linux e no Mac (Intel).
#
# Como rodar, no terminal, dentro da pasta onde você salvou este arquivo:
#
#     bash instalar-besafe.sh
#
# O que este script faz, em ordem:
#   1. confere se o computador tem memória, disco e virtualização para a VM;
#   2. consulta o último release no GitHub;
#   3. baixa as partes da OVA e o SHA256SUMS.txt (se a internet cair, rode de novo: ele continua de onde parou);
#   4. confere o SHA-256 de cada parte e baixa de novo a que vier corrompida;
#   5. junta as partes numa OVA e confere o SHA-256 dela;
#   6. importa a VM no VMware ou no VirtualBox, se encontrar algum instalado.
#
# Ele só baixa arquivos de dados do release. Nada baixado da internet é executado.
#
# Opções:
#   --pasta DIR        onde salvar os downloads (padrão: ~/BeSafe)
#   --versao 0.2.0     uma versão específica em vez da mais recente
#   --sem-importar     só baixa, confere e junta; a importação fica com você
#   --manter-partes    não apaga as partes depois de juntar
#
# Powered By Mariana BS
set -euo pipefail

PASTA="$HOME/BeSafe"
VERSAO=latest
IMPORTAR=1
MANTER=0
API="${BESAFE_API:-https://api.github.com/repos/marianabsctba/besafe-soc-vm/releases}"
while [ $# -gt 0 ]; do
  case "$1" in
    --pasta) PASTA=$2; shift ;;
    --versao) VERSAO=$2; shift ;;
    --sem-importar) IMPORTAR=0 ;;
    --manter-partes) MANTER=1 ;;
    *) echo "opção desconhecida: $1"; exit 1 ;;
  esac
  shift
done

R=$'\e[35m'; V=$'\e[32m'; A=$'\e[33m'; E=$'\e[31m'; N=$'\e[0m'
passo() { printf '\n%s== %s%s\n' "$R" "$1" "$N"; }
ok() { printf '   %s[ok]%s %s\n' "$V" "$N" "$1"; }
aviso() { printf '   %s[atenção]%s %s\n' "$A" "$N" "$1"; }
falha() { printf '\n%sERRO: %s%s\n\n' "$E" "$1" "$N"; exit 1; }

printf '\n  %sBE SAFE SOC LAB  |  instalador%s\n  Powered By Mariana BS\n' "$R" "$N"

# ------------------------------------------------------------------ 1. o computador aguenta?
passo "Conferindo o seu computador"
SO=$(uname -s)
[ "$(uname -m)" = "x86_64" ] || falha "A VM é feita para processadores x86 (Intel e AMD). Ela não roda em $(uname -m), como os Macs com chip Apple."
command -v curl >/dev/null || falha "Instale o curl (ex.: sudo apt install curl) e rode de novo."
if command -v sha256sum >/dev/null; then sha() { sha256sum "$1" | cut -d' ' -f1; }
else sha() { shasum -a 256 "$1" | cut -d' ' -f1; }; fi

if [ "$SO" = Darwin ]; then ram=$(( $(sysctl -n hw.memsize) / 1073741824 ))
else ram=$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1048576 )); fi
POUCA_RAM=0
[ "$ram" -ge 7 ] || falha "Este computador tem $ram GB de RAM. A VM precisa de pelo menos 8 GB."
if [ "$ram" -lt 15 ]; then POUCA_RAM=1; aviso "$ram GB de RAM: a VM vai ser configurada com 5 GB e 2 núcleos (sem a IA local)."
else ok "$ram GB de RAM"; fi

if [ "$SO" = Linux ]; then
  if grep -Eq '(vmx|svm)' /proc/cpuinfo; then ok "processador com virtualização"
  else aviso "não achei suporte a virtualização (VT-x/AMD-V). Confira se está ligada na BIOS (passo 1 do guia)."; fi
fi

# ------------------------------------------------------------------ 2. release
passo "Consultando o release no GitHub"
if [ "$VERSAO" = latest ]; then URL="$API/latest"; else URL="$API/tags/v$VERSAO"; fi
JSON=$(curl -fsSL -H "User-Agent: besafe-instalador" "$URL") || falha "Não consegui consultar o GitHub ($URL). Confira a internet e tente de novo."
TAG=$(printf '%s' "$JSON" | grep -o '"tag_name": *"[^"]*"' | head -1 | cut -d'"' -f4)
VER=${TAG#v}
URLS=$(printf '%s' "$JSON" | grep -o '"browser_download_url": *"[^"]*"' | cut -d'"' -f4)
PARTES=$(printf '%s\n' "$URLS" | grep -E '\.ova\.part[0-9]+$' | sort || true)
URL_SOMAS=$(printf '%s\n' "$URLS" | grep -E '/SHA256SUMS\.txt$' || true)
[ -n "$PARTES" ] && [ -n "$URL_SOMAS" ] || falha "O release $TAG não tem as partes da OVA ou o SHA256SUMS.txt."
NPARTES=$(printf '%s\n' "$PARTES" | wc -l | tr -d ' ')
OVA=$(basename "$(printf '%s\n' "$PARTES" | head -1)" | sed -E 's/\.part[0-9]+$//')
TAMANHO=$(printf '%s' "$JSON" | grep -o '"size": *[0-9]*' | awk '{s+=$2} END {print s}')
ok "versão $VER: $NPARTES partes, $(( TAMANHO / 1073741824 )) GB no total"

mkdir -p "$PASTA"; cd "$PASTA"
LIVRE=$(( $(df -Pk . | awk 'NR==2 {print $4}') / 1048576 ))
PRECISA=$(( 2 * TAMANHO / 1073741824 + 25 ))
[ "$LIVRE" -ge "$PRECISA" ] || falha "Espaço insuficiente em $PASTA: $LIVRE GB livres, precisa de uns $PRECISA GB (download, OVA e VM importada). Use --pasta para apontar outro disco."
ok "$LIVRE GB livres em $PASTA"

# ------------------------------------------------------------------ 3 e 4. baixar e conferir
passo "Baixando e conferindo as partes (pode levar um bom tempo)"
curl -fsSL --retry 5 -o SHA256SUMS.txt "$URL_SOMAS" || falha "Não consegui baixar o SHA256SUMS.txt."
esperado() { awk -v n="$1" '{f=$2; sub(/^\*/, "", f)} f == n {print tolower($1)}' SHA256SUMS.txt; }

if [ -f "$OVA" ] && [ -n "$(esperado "$OVA")" ] && [ "$(sha "$OVA")" = "$(esperado "$OVA")" ]; then
  ok "a OVA já estava baixada e conferida"
else
  for url in $PARTES; do
    nome=$(basename "$url"); hash=$(esperado "$nome")
    [ -n "$hash" ] || falha "O SHA256SUMS.txt não tem o hash de $nome."
    for tentativa in 1 2 3; do
      [ -f "$nome" ] && [ "$(sha "$nome")" = "$hash" ] && break
      # na segunda tentativa o arquivo veio inteiro, mas corrompido: recomeça do zero
      [ "$tentativa" -gt 1 ] && rm -f "$nome"
      echo "   baixando $nome..."
      curl -fL --retry 5 --retry-delay 5 -C - -# -o "$nome" "$url" || true
    done
    [ "$(sha "$nome")" = "$hash" ] || falha "$nome continua chegando corrompida. Tente mais tarde ou baixe pelo navegador."
    ok "$nome conferida"
  done

  # ---------------------------------------------------------------- 5. juntar
  passo "Juntando as partes em $OVA"
  for url in $PARTES; do cat "$(basename "$url")"; done > "$OVA"
  if [ -n "$(esperado "$OVA")" ]; then
    [ "$(sha "$OVA")" = "$(esperado "$OVA")" ] || falha "A OVA juntada não bateu com o SHA256SUMS.txt. Apague $PASTA e rode de novo."
    ok "OVA conferida"
  fi
  if [ "$MANTER" = 0 ]; then
    for url in $PARTES; do rm -f "$(basename "$url")"; done
    ok "partes apagadas para liberar espaço"
  fi
fi

# ------------------------------------------------------------------ 6. importar
NOME_VM="Be Safe SOC Lab $VER"
OVFTOOL=""
for c in "$(command -v ovftool || true)" "/Applications/VMware Fusion.app/Contents/Library/VMware OVF Tool/ovftool"; do
  [ -n "$c" ] && [ -x "$c" ] && { OVFTOOL=$c; break; }
done
VBOX=$(command -v VBoxManage || true)

ESCOLHA=nenhum
if [ "$IMPORTAR" = 1 ]; then
  if [ -n "$OVFTOOL" ] && [ -n "$VBOX" ]; then
    printf '\nEncontrei o VMware e o VirtualBox. Importar em qual? [1] VMware  [2] VirtualBox: '
    read -r r; if [ "$r" = 2 ]; then ESCOLHA=vbox; else ESCOLHA=vmware; fi
  elif [ -n "$OVFTOOL" ]; then ESCOLHA=vmware
  elif [ -n "$VBOX" ]; then ESCOLHA=vbox; fi
fi

case "$ESCOLHA" in
  vmware)
    passo "Importando no VMware (5 a 15 minutos)"
    if [ "$SO" = Darwin ]; then DESTINO="$HOME/Virtual Machines.localized"; else DESTINO="$HOME/vmware"; fi
    mkdir -p "$DESTINO"
    if [ "$SO" = Darwin ]; then VMX="$DESTINO/$NOME_VM.vmwarevm/$NOME_VM.vmx"; ALVO="$DESTINO/$NOME_VM.vmwarevm"
    else VMX="$DESTINO/$NOME_VM/$NOME_VM.vmx"; ALVO="$DESTINO"; fi
    [ ! -e "$VMX" ] || falha "Já existe uma VM em $(dirname "$VMX"). Apague ou renomeie e rode de novo."
    "$OVFTOOL" --acceptAllEulas "--name=$NOME_VM" "$OVA" "$ALVO" || falha "O VMware não conseguiu importar. Abra a OVA pelo menu File > Open."
    [ -f "$VMX" ] || VMX=$(find "$DESTINO" -name "$NOME_VM.vmx" | head -1)
    if [ "$POUCA_RAM" = 1 ] && [ -f "$VMX" ]; then
      sed -i.bak -e 's/^memsize = .*/memsize = "5120"/' -e 's/^numvcpus = .*/numvcpus = "2"/' "$VMX" && rm -f "$VMX.bak"
    fi
    ok "VM importada em $(dirname "$VMX"). Abra esse .vmx no VMware e ligue a VM."
    ;;
  vbox)
    passo "Importando no VirtualBox (5 a 15 minutos)"
    OPCOES=(import "$OVA" --vsys 0 --vmname "$NOME_VM")
    [ "$POUCA_RAM" = 1 ] && OPCOES+=(--memory 5120 --cpus 2)
    "$VBOX" "${OPCOES[@]}" || falha "O VirtualBox não conseguiu importar. Use Arquivo > Importar Appliance com a OVA."
    ok "VM importada: abra o VirtualBox, selecione '$NOME_VM' e clique em Iniciar"
    ;;
  *)
    passo "Pronto para importar"
    [ "$IMPORTAR" = 0 ] || aviso "não encontrei o VMware (ovftool) nem o VirtualBox (VBoxManage)."
    echo "   Abra a OVA no seu programa de virtualização:"
    echo "     VMware:     File > Open"
    echo "     VirtualBox: Arquivo > Importar Appliance"
    ;;
esac

printf '\n   OVA: %s/%s\n   (depois de importar e ligar a VM, você pode apagar a OVA para liberar espaço)\n\n' "$PASTA" "$OVA"
printf '  %sLogin da VM: analista / analista%s\n' "$R" "$N"
printf '  %sO primeiro boot leva 1 minuto a mais. Depois, abra o ícone Treinamento Be Safe.%s\n' "$R" "$N"
printf '  %sBons estudos e bom plantão!%s\n\n' "$R" "$N"
