#!/bin/bash
# Roda uma unica vez, no primeiro boot de cada copia da VM:
# senhas novas do Wazuh, identidade unica da maquina e remocao do usuario de build.
set -euo pipefail

ESTADO=/var/lib/besafe
WAZUH_DIR=/opt/besafe/wazuh
FERRAMENTA=/usr/share/wazuh-indexer/plugins/opensearch-security/tools/wazuh-passwords-tool.sh
USUARIO="${BESAFE_USUARIO:-analista}"
LOG="$ESTADO/primeiro-boot.log"

mkdir -p "$ESTADO"
touch "$LOG"
chmod 600 "$LOG"
exec >>"$LOG" 2>&1
echo "== primeiro boot $(date -Is)"

# identidade da maquina (o build zerou machine-id e chaves SSH)
[ -s /etc/machine-id ] || systemd-machine-id-setup
ssh-keygen -A

# usuario temporario do Packer
if [ -f "$ESTADO/usuario-build" ]; then
  u=$(cat "$ESTADO/usuario-build")
  if id "$u" >/dev/null 2>&1; then
    userdel -r "$u" || userdel "$u"
  fi
  rm -f "$ESTADO/usuario-build"
fi

# senhas do Wazuh: cada copia da VM ganha as suas
if [ -x "$FERRAMENTA" ] || [ -f "$FERRAMENTA" ]; then
  for i in $(seq 1 60); do
    curl -sk -o /dev/null https://127.0.0.1:9200 && break
    sleep 5
  done

  api_senha=$(awk -F"'" '/api_username: .wazuh.$/{getline; print $2}' "$WAZUH_DIR/senhas-build.txt")
  # a ferramenta gera senhas com "tr | head" e enche o stderr de "Broken pipe" inofensivo
  saida=$(bash "$FERRAMENTA" --api --change-all --admin-user wazuh --admin-password "$api_senha" 2> >(grep -v 'Broken pipe' >&2))
  # nenhuma senha vai para o log (indexer e API usam frases diferentes)
  echo "$saida" | sed -E 's/(password for .* is ).*/\1***/I'

  admin=$(echo "$saida" | sed -nE "s/.*password for user admin is (.*)$/\1/Ip" | head -1)
  if [ -n "$admin" ]; then
    destino="/home/$USUARIO/.besafe"
    install -d -m 700 -o "$USUARIO" -g "$USUARIO" "$destino"
    printf 'Wazuh dashboard: https://localhost\nusuario: admin\nsenha: %s\n' "$admin" > "$destino/wazuh.txt"
    chown "$USUARIO:$USUARIO" "$destino/wazuh.txt"
    chmod 600 "$destino/wazuh.txt"
  fi
  # as senhas do build nao valem mais e nao devem ficar na imagem
  rm -f "$WAZUH_DIR/senhas-build.txt"
  # dashboard, manager e filebeat so leem as senhas novas depois de reiniciar
  systemctl restart wazuh-manager filebeat wazuh-dashboard
fi

touch "$ESTADO/primeiro-boot.ok"
echo "== concluido"
