"""Motor de cenarios: transforma cenarios YAML em eventos para o Wazuh e em casos com gabarito.

Fluxo:
  1. carregar_cenarios() le os YAML de besafe/cenarios
  2. montar_plantao() sorteia os casos do plantao (mais ruido que ataque) e resolve os atores
  3. cada caso vira uma lista de eventos com horario absoluto
  4. o agendador (no Console) grava cada evento em /var/log/besafe/eventos.json na hora certa

Os eventos sao apenas metadados de log (processo, IPs, Event ID, usuario). Nada aqui executa codigo.
"""
import base64
import json
import random
import re
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from .mundo import Mundo, ip_externo

PASTA_CENARIOS = Path(__file__).resolve().parent / "cenarios"
BRT = timezone(timedelta(hours=-3))
MARCADOR = re.compile(r"\{([a-z_][a-z0-9_.]*)\}")


@dataclass
class Caso:
    id: str
    cenario: str
    titulo: str
    verdade: dict
    dicas: list
    contexto: dict
    eventos: list = field(default_factory=list)
    extras: dict = field(default_factory=dict)


def carregar_cenarios(pasta: Path = PASTA_CENARIOS) -> dict:
    cenarios = {}
    for arq in sorted(pasta.glob("*.yml")):
        dados = yaml.safe_load(arq.read_text(encoding="utf-8"))
        cenarios[dados["id"]] = dados
    return cenarios


# ------------------------------------------------------------ resolucao de atores
def _rotulo_aleatorio(r, tamanho):
    return "".join(r.choice(string.ascii_lowercase + string.digits) for _ in range(tamanho))


def _ps_codificado(texto):
    """Comando PowerShell codificado (-enc). Usado so com textos inofensivos de treino."""
    return base64.b64encode(texto.encode("utf-16-le")).decode()


def _resolver_ator(espec, r, mundo, usados):
    tipo, valor = next(iter(espec.items()))
    if tipo == "colaborador":
        filtro = valor or {}
        candidatos = [c for c in mundo.colaboradores
                      if c.login not in usados
                      and all(getattr(c, k) == v for k, v in filtro.items())]
        escolhido = r.choice(candidatos)
        usados.add(escolhido.login)
        m = mundo.maquina(escolhido.maquina)
        return {"login": escolhido.login, "nome": escolhido.nome, "setor": escolhido.setor,
                "email": escolhido.email, "maquina": escolhido.maquina, "ip": m.ip}
    if tipo == "servidor":
        m = mundo.maquina(valor)
        return {"nome": m.nome, "ip": m.ip, "funcao": m.funcao}
    if tipo == "ip_externo":
        return ip_externo(r)
    if tipo == "dominio":
        return valor.replace("{rand}", _rotulo_aleatorio(r, 6))
    if tipo == "numero":
        return r.randint(valor[0], valor[1])
    if tipo == "ps_codificado":
        return _ps_codificado(valor)
    if tipo == "texto":
        return valor
    raise ValueError(f"tipo de ator desconhecido: {tipo}")


def _buscar(contexto, caminho):
    atual = contexto
    for parte in caminho.split("."):
        atual = atual[parte] if isinstance(atual, dict) else getattr(atual, parte)
    return atual


def preencher(valor, contexto):
    """Substitui {ator.campo} em strings, listas e dicionarios (recursivo)."""
    if isinstance(valor, str):
        inteiro = MARCADOR.fullmatch(valor)
        if inteiro:  # o valor inteiro e um marcador: preserva o tipo (numero, lista...)
            return _buscar(contexto, inteiro.group(1))
        return MARCADOR.sub(lambda m: str(_buscar(contexto, m.group(1))), valor)
    if isinstance(valor, list):
        return [preencher(v, contexto) for v in valor]
    if isinstance(valor, dict):
        return {k: preencher(v, contexto) for k, v in valor.items()}
    return valor


# ------------------------------------------------------------ montagem
def instanciar(cenario: dict, mundo: Mundo, r: random.Random, id_caso: str, inicio: datetime) -> Caso:
    usados = set()
    contexto = {"caso": id_caso, "dominio_empresa": mundo.dominio}
    for nome, espec in (cenario.get("atores") or {}).items():
        contexto[nome] = _resolver_ator(espec, r, mundo, usados)

    eventos = []
    for passo in cenario["linha_do_tempo"]:
        repetir = passo.get("repetir", 1)
        intervalo = passo.get("intervalo", 0)
        for i in range(repetir):
            contexto["i"] = i + 1
            contexto["rotulo"] = _rotulo_aleatorio(r, passo.get("rotulo_tamanho", 24))
            contexto["porta_aleatoria"] = r.choice(passo.get("portas", [22, 80, 443]))
            # "escolher": a cada repeticao, sorteia um valor da lista (ex.: nomes de usuario tentados)
            for nome, opcoes in (passo.get("escolher") or {}).items():
                contexto[nome] = r.choice(opcoes)
            quando = inicio + timedelta(seconds=passo.get("atraso", 0) + i * intervalo + r.uniform(0, 2))
            corpo = preencher({k: v for k, v in passo.items()
                               if k not in ("atraso", "repetir", "intervalo", "rotulo_tamanho", "portas", "escolher")},
                              contexto)
            corpo["besafe"] = {"caso": id_caso, "cenario": cenario["id"], "fonte": corpo.pop("fonte"),
                               "evento": str(corpo.pop("evento"))}
            corpo["timestamp"] = quando.isoformat(timespec="milliseconds")
            eventos.append((quando, corpo))
    for temporario in ["i", "rotulo", "porta_aleatoria"] + [
            n for p in cenario["linha_do_tempo"] for n in (p.get("escolher") or {})]:
        contexto.pop(temporario, None)

    extras = preencher(cenario.get("extras") or {}, contexto)
    return Caso(id=id_caso, cenario=cenario["id"], titulo=cenario["titulo"],
                verdade=preencher(cenario["verdade"], contexto),
                dicas=preencher(cenario.get("dicas", []), contexto),
                contexto=contexto, eventos=sorted(eventos, key=lambda e: e[0]), extras=extras)


def montar_plantao(cenarios: dict, mundo: Mundo, numero: int, inicio: datetime,
                   duracao_min: int = 60, quantos: int = 6) -> list:
    """Sorteia os casos do plantao: pelo menos 2 ataques e pelo menos 2 ruidos."""
    r = random.Random(f"plantao-{mundo.semente}-{numero}")
    ataques = [c for c in cenarios.values() if c["verdade"]["classificacao"] == "vp"]
    ruidos = [c for c in cenarios.values() if c["verdade"]["classificacao"] != "vp"]
    n_ruidos = min(len(ruidos), max(2, quantos - 3))
    n_ataques = min(len(ataques), quantos - n_ruidos)
    escolhidos = r.sample(ataques, n_ataques) + r.sample(ruidos, n_ruidos)
    r.shuffle(escolhidos)

    casos, usados_ids = [], set()
    janela = max(60, duracao_min * 60 - 600)  # o ultimo caso comeca a 10 min do fim
    for cen in escolhidos:
        while True:
            id_caso = f"PL-{r.randint(1000, 9999)}"
            if id_caso not in usados_ids:
                usados_ids.add(id_caso)
                break
        comeco = inicio + timedelta(seconds=r.randint(30, janela))
        casos.append(instanciar(cen, mundo, r, id_caso, comeco))
    return sorted(casos, key=lambda c: c.eventos[0][0] if c.eventos else inicio)


def linha_json(evento: dict) -> str:
    return json.dumps(evento, ensure_ascii=False, separators=(",", ":"))


def agora() -> datetime:
    return datetime.now(BRT)
