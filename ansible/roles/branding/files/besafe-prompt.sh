# Be Safe: prompt rosa, banner e senha do Wazuh em todo terminal interativo.
# Carregado pelo ~/.bashrc (o terminal do XFCE nao e shell de login).
case "$-" in
  *i*)
    PS1='\[\e[38;2;252;19;180m\]\u@besafe\[\e[0m\]:\[\e[38;2;255;111;208m\]\w\[\e[0m\]\$ '
    [ -x /etc/update-motd.d/10-besafe ] && /etc/update-motd.d/10-besafe
    if [ -r "$HOME/.besafe/wazuh.txt" ]; then
      printf '  Wazuh: usuario admin | senha %s\n\n' "$(sed -n 's/^senha: //p' "$HOME/.besafe/wazuh.txt")"
    fi
    ;;
esac
