#!/bin/bash
# Roda uma unica vez, no primeiro boot de cada copia da VM:
# senhas novas do Wazuh, identidade unica da maquina e remocao do usuario de build.
#
# Em maquinas lentas o Wazuh demora a subir. Por isso as etapas sao separadas:
#   1. senha do admin (so depende do indexer): grava o CREDENCIAIS.txt na hora;
#   2. senhas da API (dependem da API, que reinicia junto com o manager): extra,
#      com novas tentativas, e nunca impede o aluno de ter as credenciais.
# Se algo essencial falhar, o servico nao marca como concluido e roda de novo no proximo boot.
set -uo pipefail

ESTADO=/var/lib/besafe
WAZUH_DIR=/opt/besafe/wazuh
LOG="$ESTADO/primeiro-boot.log"
# shellcheck source=besafe-senha-wazuh
. /usr/local/sbin/besafe-senha-wazuh

mkdir -p "$ESTADO"
touch "$LOG"
chmod 600 "$LOG"
exec >>"$LOG" 2>&1
echo "== primeiro boot $(date -Is)"

# ------------------------------------------------------------------ identidade da maquina
# o build zerou machine-id e chaves SSH
[ -s /etc/machine-id ] || systemd-machine-id-setup
ssh-keygen -A

# usuario temporario do Packer
if [ -f "$ESTADO/usuario-build" ]; then
  u=$(cat "$ESTADO/usuario-build")
  if id "$u" >/dev/null 2>&1; then
    userdel -r "$u" || userdel "$u" || true
  fi
  rm -f "$ESTADO/usuario-build" /etc/sudoers.d/90-build
fi

# ------------------------------------------------------------------ 1. senha do admin do Wazuh
mesa="/home/$USUARIO/Desktop"
if [ ! -f "$ESTADO/senha-admin.ok" ]; then
  # o aluno pode entrar antes de terminar: o arquivo ja aparece e explica
  install -d -m 755 -o "$USUARIO" -g "$USUARIO" "$mesa"
  cat > "$mesa/CREDENCIAIS.txt" <<'AGUARDE'
BE SAFE SOC LAB - credenciais desta VM

Login da VM e sudo
  usuario: analista
  senha:   analista

Wazuh dashboard: a senha desta copia ESTA SENDO GERADA.
Isso leva de 2 a 15 minutos no primeiro boot, conforme o computador.
Este arquivo e atualizado sozinho: feche e abra de novo daqui a pouco.

Passou de 20 minutos? Abra o terminal e rode:
  sudo besafe-senha-wazuh

Powered By Mariana BS
AGUARDE
  chown "$USUARIO:$USUARIO" "$mesa/CREDENCIAIS.txt"
  chmod 644 "$mesa/CREDENCIAIS.txt"

  esperar_indexer || echo "indexer ainda nao respondeu; tentando assim mesmo"
  admin=""
  rc=1
  for tentativa in 1 2 3; do
    # todos os usuarios do indexer ganham senhas novas (sem --api: nao depende da API).
    # A ferramenta tambem atualiza Filebeat, manager e dashboard e reinicia os tres.
    saida=$(bash "$FERRAMENTA" --change-all 2> >(grep -v 'Broken pipe' >&2))
    rc=$?
    # nenhuma senha vai para o log
    echo "$saida" | sed -E 's/(password for .* is ).*/\1***/I'
    admin=$(echo "$saida" | sed -nE "s/.*password for user admin is (.*)$/\1/Ip" | head -1)
    [ "$rc" = 0 ] && break
    echo "tentativa $tentativa falhou (codigo $rc); esperando o indexer"
    sleep 30
    esperar_indexer || true
  done
  # a troca geral funcionou mas a saida nao trouxe a senha: define uma conhecida so para o admin
  if [ "$rc" = 0 ] && [ -z "$admin" ]; then
    senha=$(gerar_senha)
    bash "$FERRAMENTA" -u admin -p "$senha" >/dev/null && admin=$senha
  fi
  if [ -z "$admin" ]; then
    echo "== senha do admin NAO gerada; o servico roda de novo no proximo boot"
    exit 1
  fi
  gravar_credenciais "$admin"
  touch "$ESTADO/senha-admin.ok"
  echo "credenciais gravadas"
fi

# ------------------------------------------------------------------ 2. senhas da API (extra)
esperar_api() {
  local i
  for i in $(seq 1 120); do  # ate 10 minutos: a API reinicia junto com o manager
    [ "$(curl -sk -o /dev/null -w '%{http_code}' --max-time 5 https://127.0.0.1:55000/)" = 401 ] && return 0
    sleep 5
  done
  return 1
}

if [ -f "$WAZUH_DIR/senhas-build.txt" ]; then
  api_atual=$(awk -F"'" '/api_username: .wazuh.$/{getline; print $2}' "$WAZUH_DIR/senhas-build.txt")
  wui_mudou=0
  # wazuh-wui primeiro: a troca usa o token do usuario wazuh, que muda por ultimo
  for usuario_api in wazuh-wui wazuh; do
    nova=$(gerar_senha)
    feito=0
    for tentativa in 1 2 3 4 5; do
      esperar_api || true
      if bash "$FERRAMENTA" --api -u "$usuario_api" -p "$nova" --admin-user wazuh --admin-password "$api_atual" >/dev/null 2>&1; then
        feito=1; break
      fi
      echo "API: tentativa $tentativa para $usuario_api falhou"
      sleep 20
    done
    if [ "$feito" = 1 ]; then
      echo "API: senha de $usuario_api trocada"
      [ "$usuario_api" = wazuh ] && api_atual=$nova
      [ "$usuario_api" = wazuh-wui ] && wui_mudou=1
    else
      echo "API: senha de $usuario_api mantida (a API so escuta em localhost)"
    fi
  done
  # a senha atual da API fica so para o root, caso precise no futuro
  umask 077
  printf 'api wazuh: %s\n' "$api_atual" > "$WAZUH_DIR/api.txt"
  # as senhas do build nao valem mais e nao devem ficar na imagem
  rm -f "$WAZUH_DIR/senhas-build.txt"
  [ "$wui_mudou" = 1 ] && systemctl restart wazuh-dashboard
fi

# ------------------------------------------------------------------ Console
# Semente e plantoes sao desta copia. Qualquer resto do build e descartado.
# O Console e ordenado depois deste servico (After=) e sobe sozinho quando ele termina.
# Esperar por ele aqui (systemctl start sem --no-block) trava os dois ate o timeout.
if [ -d "$ESTADO/console" ]; then
  rm -f "$ESTADO/console/semente" "$ESTADO/console/console.db"
  : > /var/log/besafe/eventos.json
  systemctl start --no-block besafe-console || true
fi

touch "$ESTADO/primeiro-boot.ok"
echo "== concluido $(date -Is)"
