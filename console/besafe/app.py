"""Console Be Safe: plantao, tickets, nota, servicos simulados e IA.

Roda em 127.0.0.1:8080 (servico besafe-console). Os eventos dos cenarios sao gravados em
/var/log/besafe/eventos.json, que o Wazuh le e transforma em alertas.
"""
import hashlib
import json
import re
import os
import secrets
import sqlite3
import threading
import time
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import VERSAO, certificado, ia
from .motor import BRT, agora, carregar_cenarios, linha_json, montar_plantao
from .mundo import gerar_mundo
from .nota import avaliar, nota_do_plantao

ESTADO = Path(os.environ.get("BESAFE_ESTADO", "/var/lib/besafe"))
ARQ_EVENTOS = Path(os.environ.get("BESAFE_EVENTOS", "/var/log/besafe/eventos.json"))
ARQ_SEMENTE = ESTADO / "semente"
BANCO = ESTADO / "console.db"
ESTATICO = Path(__file__).resolve().parent / "static"
BRANDING = Path(os.environ.get("BESAFE_BRANDING", "/usr/share/besafe/branding"))
NOTA_MINIMA = 70          # nota da prova final que libera o certificado
DURACAO_PROVA = 60        # minutos

# ------------------------------------------------------------------ estado global
def _semente() -> int:
    ESTADO.mkdir(parents=True, exist_ok=True)
    if not ARQ_SEMENTE.exists():
        ARQ_SEMENTE.write_text(str(secrets.randbits(63)))
        os.chmod(ARQ_SEMENTE, 0o600)
    return int(ARQ_SEMENTE.read_text().strip())


SEMENTE = _semente()
MUNDO = gerar_mundo(SEMENTE)
CENARIOS = carregar_cenarios()


def db():
    con = sqlite3.connect(BANCO, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def criar_tabelas():
    with closing(db()) as con, con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS plantoes (
            numero INTEGER PRIMARY KEY, inicio TEXT, fim_previsto TEXT, encerrado_em TEXT, resultado TEXT);
        CREATE TABLE IF NOT EXISTS casos (
            id TEXT PRIMARY KEY, plantao INTEGER, cenario TEXT, titulo TEXT, verdade TEXT, dicas TEXT,
            extras TEXT, primeiro_evento TEXT);
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, caso TEXT, quando TEXT, corpo TEXT, enviado INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS tickets (
            caso TEXT PRIMARY KEY, dados TEXT, avaliacao TEXT, criado_em TEXT);
        CREATE TABLE IF NOT EXISTS dicas_usadas (caso TEXT PRIMARY KEY, nivel INTEGER);
        CREATE TABLE IF NOT EXISTS certificados (
            plantao INTEGER PRIMARY KEY, nome TEXT, nota INTEGER, hash TEXT, arquivo TEXT, emitido_em TEXT);
        """)
        colunas = {r["name"] for r in con.execute("PRAGMA table_info(plantoes)")}
        if "modo_prova" not in colunas:
            con.execute("ALTER TABLE plantoes ADD COLUMN modo_prova INTEGER DEFAULT 0")


def plantao_ativo():
    with closing(db()) as con:
        return con.execute("SELECT * FROM plantoes WHERE encerrado_em IS NULL ORDER BY numero DESC LIMIT 1").fetchone()


def casos_do_plantao(numero, so_entregues=False):
    with closing(db()) as con:
        linhas = con.execute("SELECT * FROM casos WHERE plantao=? ORDER BY primeiro_evento", (numero,)).fetchall()
    if so_entregues:
        momento = agora().isoformat()
        linhas = [c for c in linhas if c["primeiro_evento"] <= momento]
    return linhas


def caso(cid):
    with closing(db()) as con:
        c = con.execute("SELECT * FROM casos WHERE id=?", (cid,)).fetchone()
    if not c:
        raise HTTPException(404, "Caso não encontrado. Confira o ID no alerta do Wazuh (campo data.besafe.caso).")
    return c


# ------------------------------------------------------------------ agendador de eventos
def agendador():
    ARQ_EVENTOS.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            momento = agora().isoformat()
            with closing(db()) as con, con:
                pendentes = con.execute(
                    "SELECT id, corpo FROM eventos WHERE enviado=0 AND quando<=? ORDER BY quando", (momento,)).fetchall()
                if pendentes:
                    with ARQ_EVENTOS.open("a", encoding="utf-8") as f:
                        for ev in pendentes:
                            corpo = json.loads(ev["corpo"])
                            corpo["timestamp"] = agora().isoformat(timespec="milliseconds")
                            f.write(linha_json(corpo) + "\n")
                    con.executemany("UPDATE eventos SET enviado=1 WHERE id=?", [(e["id"],) for e in pendentes])
        except Exception as erro:  # o agendador nunca pode morrer
            print("agendador:", erro, flush=True)
        time.sleep(1)


# ------------------------------------------------------------------ app
app = FastAPI(title="Console Be Safe", version=VERSAO)


@app.on_event("startup")
def iniciar():
    criar_tabelas()
    threading.Thread(target=agendador, daemon=True).start()
    threading.Thread(target=ia.vigiar_ociosidade, daemon=True).start()


class NovoPlantao(BaseModel):
    duracao_min: int = Field(60, ge=15, le=240)
    modo_prova: bool = False


@app.get("/api/estado")
def estado():
    p = plantao_ativo()
    with closing(db()) as con:
        historico = [dict(x) for x in con.execute(
            "SELECT numero, inicio, encerrado_em, resultado, modo_prova FROM plantoes "
            "WHERE encerrado_em IS NOT NULL ORDER BY numero DESC")]
        emitidos = {r["plantao"]: dict(r) for r in con.execute("SELECT plantao, nome, nota, hash FROM certificados")}
    for h in historico:
        h["resultado"] = json.loads(h["resultado"] or "{}")
        h["modo_prova"] = bool(h["modo_prova"])
        h["aprovado"] = h["modo_prova"] and h["resultado"].get("media", 0) >= NOTA_MINIMA
        h["certificado"] = emitidos.get(h["numero"])
    if not p:
        return {"plantao": None, "historico": historico, "ia": ia.disponivel(), "versao": VERSAO,
                "nota_minima": NOTA_MINIMA}
    todos = casos_do_plantao(p["numero"])
    entregues = casos_do_plantao(p["numero"], so_entregues=True)
    with closing(db()) as con:
        com_ticket = {r["caso"] for r in con.execute("SELECT caso FROM tickets")}
    return {
        "plantao": {"numero": p["numero"], "inicio": p["inicio"], "fim_previsto": p["fim_previsto"],
                    "modo_prova": bool(p["modo_prova"]),
                    "casos_total": len(todos), "casos_chegaram": len(entregues),
                    "tickets": len([c for c in todos if c["id"] in com_ticket])},
        "historico": historico, "ia": ia.disponivel(), "versao": VERSAO, "nota_minima": NOTA_MINIMA,
    }


@app.post("/api/plantao/iniciar")
def iniciar_plantao(dados: NovoPlantao):
    if plantao_ativo():
        raise HTTPException(409, "Já existe um plantão em andamento. Encerre-o antes de iniciar outro.")
    with closing(db()) as con:
        ultimo = con.execute("SELECT MAX(numero) AS n FROM plantoes").fetchone()["n"] or 0
    numero = ultimo + 1
    inicio = agora()
    duracao = DURACAO_PROVA if dados.modo_prova else dados.duracao_min
    casos = montar_plantao(CENARIOS, MUNDO, numero, inicio, duracao_min=duracao)
    with closing(db()) as con, con:
        con.execute("INSERT INTO plantoes (numero, inicio, fim_previsto, modo_prova) VALUES (?,?,?,?)",
                    (numero, inicio.isoformat(), (inicio + timedelta(minutes=duracao)).isoformat(),
                     int(dados.modo_prova)))
        for c in casos:
            con.execute("INSERT INTO casos VALUES (?,?,?,?,?,?,?,?)",
                        (c.id, numero, c.cenario, c.titulo, json.dumps(c.verdade, ensure_ascii=False),
                         json.dumps(c.dicas, ensure_ascii=False), json.dumps(c.extras, ensure_ascii=False),
                         c.eventos[0][0].isoformat()))
            con.executemany("INSERT INTO eventos (caso, quando, corpo) VALUES (?,?,?)",
                            [(c.id, q.isoformat(), json.dumps(corpo, ensure_ascii=False)) for q, corpo in c.eventos])
    return {"numero": numero, "casos": len(casos), "duracao_min": duracao, "modo_prova": dados.modo_prova}


@app.post("/api/plantao/encerrar")
def encerrar_plantao():
    p = plantao_ativo()
    if not p:
        raise HTTPException(409, "Não há plantão em andamento.")
    casos = casos_do_plantao(p["numero"])
    with closing(db()) as con, con:
        avaliacoes = {r["caso"]: json.loads(r["avaliacao"]) for r in con.execute(
            "SELECT caso, avaliacao FROM tickets WHERE caso IN (%s)" % ",".join("?" * len(casos)),
            [c["id"] for c in casos])}
        resultado = nota_do_plantao([c["id"] for c in casos], avaliacoes)
        resultado["numero"] = p["numero"]
        resultado["modo_prova"] = bool(p["modo_prova"])
        resultado["aprovado"] = resultado["modo_prova"] and resultado["media"] >= NOTA_MINIMA
        resultado["nota_minima"] = NOTA_MINIMA
        resultado["detalhes"] = [{
            "caso": c["id"], "titulo": c["titulo"], "verdade": json.loads(c["verdade"]),
            "avaliacao": avaliacoes.get(c["id"])} for c in casos]
        con.execute("UPDATE plantoes SET encerrado_em=?, resultado=? WHERE numero=?",
                    (agora().isoformat(), json.dumps(resultado, ensure_ascii=False), p["numero"]))
        # eventos que nao chegaram a sair nao saem mais
        con.execute("UPDATE eventos SET enviado=1 WHERE caso IN (%s)" % ",".join("?" * len(casos)),
                    [c["id"] for c in casos])
    return resultado


# ------------------------------------------------------------------ tickets
class Ticket(BaseModel):
    caso: str
    classificacao: str = Field(pattern="^(vp|fp|vpb)$")
    severidade: str = Field(pattern="^(baixa|media|alta|critica)$")
    escalar: bool
    iocs: list[str] = []
    resumo: str = ""


@app.get("/api/tickets")
def listar_tickets():
    p = plantao_ativo()
    if not p:
        return []
    ids = {c["id"] for c in casos_do_plantao(p["numero"])}
    with closing(db()) as con:
        linhas = con.execute("SELECT caso, dados, criado_em FROM tickets").fetchall()
    return [{"caso": r["caso"], "criado_em": r["criado_em"], **json.loads(r["dados"])}
            for r in linhas if r["caso"] in ids]


@app.post("/api/tickets")
def salvar_ticket(t: Ticket):
    p = plantao_ativo()
    c = caso(t.caso.strip().upper())
    if not p or c["plantao"] != p["numero"]:
        raise HTTPException(409, "Este caso não pertence ao plantão em andamento.")
    if c["primeiro_evento"] > agora().isoformat():
        raise HTTPException(404, "Caso não encontrado. Confira o ID no alerta do Wazuh (campo data.besafe.caso).")
    with closing(db()) as con, con:
        usadas = con.execute("SELECT nivel FROM dicas_usadas WHERE caso=?", (c["id"],)).fetchone()
        avaliacao = avaliar(t.model_dump(), json.loads(c["verdade"]), usadas["nivel"] if usadas else 0)
        con.execute("INSERT OR REPLACE INTO tickets VALUES (?,?,?,?)",
                    (c["id"], json.dumps(t.model_dump(), ensure_ascii=False),
                     json.dumps(avaliacao, ensure_ascii=False), agora().isoformat()))
    return {"ok": True, "caso": c["id"], "mensagem": "Ticket registrado. A nota sai ao encerrar o plantão."}


# ------------------------------------------------------------------ servicos simulados
def _extras_entregues():
    p = plantao_ativo()
    if not p:
        return []
    return [(c, json.loads(c["extras"])) for c in casos_do_plantao(p["numero"], so_entregues=True)]


def _ferias_forcadas():
    p = plantao_ativo()
    if not p:
        return set()
    return {json.loads(c["extras"]).get("diretorio_ferias") for c in casos_do_plantao(p["numero"])} - {None}


@app.get("/api/diretorio")
def diretorio():
    ferias = _ferias_forcadas()
    saida = []
    for c in MUNDO.colaboradores:
        d = c.__dict__.copy()
        d["ferias"] = d["ferias"] or c.login in ferias
        saida.append(d)
    return saida


@app.get("/api/inventario")
def inventario():
    return [m.__dict__ for m in MUNDO.maquinas]


@app.get("/api/mudancas")
def mudancas():
    return [e["mudanca"] for _, e in _extras_entregues() if "mudanca" in e]


@app.get("/api/phishing")
def caixa_phishing():
    return [{"caso": c["id"], **e["phishing"]} for c, e in _extras_entregues() if "phishing" in e]


@app.get("/api/intel")
def intel(valor: str):
    """Reputacao simulada: coerente com os casos do plantao e estavel para a mesma semente."""
    v = valor.strip().lower().replace("[.]", ".").replace("hxxp", "http")
    if not v:
        raise HTTPException(400, "Informe um IP, domínio ou hash.")
    if v.startswith(("10.", "192.168.", "127.")) or any(m.ip == v for m in MUNDO.maquinas):
        return {"valor": v, "veredito": "interno", "deteccoes": "0/70",
                "comentario": "Endereço da rede interna. Consulte o Inventário para saber de quem é."}
    maliciosos = set()
    for c, _ in _extras_entregues():
        verdade = json.loads(c["verdade"])
        if verdade["classificacao"] == "vp":
            maliciosos |= {str(i).lower() for i in verdade.get("iocs", [])}
    h = int(hashlib.sha256(f"{SEMENTE}-{v}".encode()).hexdigest(), 16)
    if any(v == i or v in i or i in v for i in maliciosos if len(i) > 4):
        n = 3 + h % 9
        return {"valor": v, "veredito": "suspeito" if n < 6 else "malicioso", "deteccoes": f"{n}/70",
                "primeira_vez_visto": "há 2 dias",
                "comentario": "Poucos motores detectam, e o indicador é recente. Ausência de consenso não significa inocência."
                if n < 6 else "Vários motores classificam como malicioso. Associado a campanhas recentes."}
    if v.endswith(".example") or v.count(".") == 3:
        return {"valor": v, "veredito": "desconhecido", "deteccoes": "0/70",
                "comentario": "Sem histórico. Desconhecido não é o mesmo que confiável."}
    return {"valor": v, "veredito": "sem dados", "deteccoes": "-",
            "comentario": "Formato não reconhecido. Use IP, domínio ou hash SHA-256."}


# ------------------------------------------------------------------ IA
def _bloquear_na_prova(c):
    with closing(db()) as con:
        p = con.execute("SELECT modo_prova, encerrado_em FROM plantoes WHERE numero=?", (c["plantao"],)).fetchone()
    if p and p["modo_prova"] and p["encerrado_em"] is None:
        raise HTTPException(403, "Assistentes desligados durante a prova final. Você consegue!")


class Pergunta(BaseModel):
    caso: str
    texto: str = ""
    nova_dica: bool = False


@app.post("/api/mentor")
def mentor(p: Pergunta):
    c = caso(p.caso.strip().upper())
    _bloquear_na_prova(c)
    dicas = json.loads(c["dicas"])
    with closing(db()) as con, con:
        linha = con.execute("SELECT nivel FROM dicas_usadas WHERE caso=?", (c["id"],)).fetchone()
        nivel = linha["nivel"] if linha else 0
        if p.nova_dica and nivel < len(dicas):
            nivel += 1
            con.execute("INSERT OR REPLACE INTO dicas_usadas VALUES (?,?)", (c["id"], nivel))
    if nivel == 0:
        return {"nivel": 0, "resposta": "Peça uma dica para começarmos. Cada dica custa 5 pontos no caso.", "ia": False}
    dica = dicas[nivel - 1]
    pergunta = p.texto.strip() or "Me ajude a pensar sobre este caso."
    resposta = ia.conversar(ia.SISTEMA_MENTOR, [{"role": "user", "content": f"DICA: {dica}\n\nPergunta do N1: {pergunta}"}])
    return {"nivel": nivel, "dica": dica, "resposta": resposta or dica, "ia": resposta is not None}


@app.post("/api/pessoa")
def pessoa(p: Pergunta):
    c = caso(p.caso.strip().upper())
    _bloquear_na_prova(c)
    ficha = json.loads(c["extras"]).get("pessoa")
    if not ficha:
        raise HTTPException(404, "Não há ninguém para entrevistar neste caso.")
    texto = ia.conversar(ia.SISTEMA_PESSOA + json.dumps(ficha, ensure_ascii=False),
                         [{"role": "user", "content": p.texto or "Oi, aqui é do SOC. Pode me contar o que aconteceu?"}])
    return {"nome": ficha["nome"], "resposta": texto or ficha["lembra"], "ia": texto is not None}


@app.get("/api/copiloto/{cid}")
def copiloto(cid: str):
    c = caso(cid.strip().upper())
    _bloquear_na_prova(c)
    with closing(db()) as con:
        eventos = [json.loads(r["corpo"]) for r in con.execute(
            "SELECT corpo FROM eventos WHERE caso=? AND enviado=1 ORDER BY quando LIMIT 8", (c["id"],))]
    if not eventos:
        raise HTTPException(404, "Ainda não chegaram eventos deste caso.")
    for e in eventos:
        e.pop("besafe", None)
    texto = ia.conversar(ia.SISTEMA_COPILOTO, [{"role": "user", "content": json.dumps(eventos, ensure_ascii=False, indent=1)}],
                         max_tokens=300, temperatura=0.1)
    return {"caso": c["id"], "resumo": texto, "ia": texto is not None,
            "aviso": "O copiloto resume os campos dos eventos. Confira sempre o evento bruto no Wazuh."}


# ------------------------------------------------------------------ certificado
NOME_VALIDO = re.compile(r"^[^\W\d_]+(?:[ '.-][^\W\d_]+)*$")


class PedidoCertificado(BaseModel):
    plantao: int
    nome: str = Field(min_length=3, max_length=60)


@app.post("/api/certificado")
def emitir_certificado(pedido: PedidoCertificado):
    nome = " ".join(pedido.nome.split())
    if not NOME_VALIDO.match(nome):
        raise HTTPException(400, "Use só letras, espaços, apóstrofo, ponto e hífen no nome.")
    with closing(db()) as con, con:
        p = con.execute("SELECT * FROM plantoes WHERE numero=? AND encerrado_em IS NOT NULL",
                        (pedido.plantao,)).fetchone()
        if not p or not p["modo_prova"]:
            raise HTTPException(404, "O certificado é emitido a partir de uma prova final encerrada.")
        nota = json.loads(p["resultado"] or "{}").get("media", 0)
        if nota < NOTA_MINIMA:
            raise HTTPException(403, f"A nota mínima para o certificado é {NOTA_MINIMA}. Faça uma nova prova final.")
        arquivo = ESTADO / "certificados" / f"certificado-plantao-{p['numero']}.png"
        emissao = date.fromisoformat(p["encerrado_em"][:10])
        info = certificado.gerar(nome, nota, p["numero"], SEMENTE, arquivo, emissao=emissao)
        con.execute("INSERT OR REPLACE INTO certificados VALUES (?,?,?,?,?,?)",
                    (p["numero"], info["nome"], nota, info["hash"], str(arquivo), agora().isoformat()))
    info.pop("arquivo", None)
    return {**info, "url": f"/api/certificado/{p['numero']}.png"}


@app.get("/api/certificado/{numero}.png")
def baixar_certificado(numero: int):
    with closing(db()) as con:
        r = con.execute("SELECT arquivo FROM certificados WHERE plantao=?", (numero,)).fetchone()
    if not r or not Path(r["arquivo"]).exists():
        raise HTTPException(404, "Certificado ainda não emitido.")
    return FileResponse(r["arquivo"], media_type="image/png",
                        filename=f"certificado-besafe-soc-lab-{numero}.png")


# ------------------------------------------------------------------ paginas e artes
if BRANDING.exists():
    app.mount("/branding", StaticFiles(directory=BRANDING), name="branding")
app.mount("/static", StaticFiles(directory=ESTATICO), name="static")


@app.get("/")
def pagina():
    return FileResponse(ESTATICO / "index.html")
