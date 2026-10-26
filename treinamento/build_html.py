"""Gera o treinamento em HTML (preto e rosa, offline) a partir dos modulos em Markdown.

Uso: python treinamento/build_html.py [--saida DIR] [--logo CAMINHO]
Padrao: saida em treinamento/out, logo em branding/out/icone-128.png
"""
import argparse
import html
import re
import shutil
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parent
MODULOS = RAIZ / "modulos"

CSS = """
:root {
  --preto: #050407; --superficie: #120a12; --superficie2: #1c101b;
  --rosa: #fc13b4; --rosa-claro: #ff6fd0; --texto: #f5e9f2; --mudo: #a8939f;
  --verde: #5ee3a1; --amarelo: #ffd166; --vermelho: #ff4d6d;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0; background: var(--preto); color: var(--texto);
  font: 17px/1.7 "Rajdhani", "Segoe UI", system-ui, sans-serif;
}
a { color: var(--rosa-claro); }
a:hover { color: var(--rosa); }
.topo {
  position: sticky; top: 0; z-index: 5; display: flex; align-items: center; gap: 14px;
  padding: 10px 24px; background: rgba(5,4,7,.94); border-bottom: 1px solid #3a1630;
  backdrop-filter: blur(6px);
}
.topo img { width: 38px; height: 38px; }
.topo .marca { font: 700 18px "Orbitron", sans-serif; letter-spacing: 2px; color: var(--texto); text-decoration: none; }
.topo .marca span { color: var(--rosa); }
.topo nav { margin-left: auto; display: flex; gap: 18px; font-weight: 600; }
.topo nav a { text-decoration: none; color: var(--mudo); }
.topo nav a:hover { color: var(--rosa-claro); }
.layout { display: grid; grid-template-columns: 270px minmax(0, 1fr); max-width: 1320px; margin: 0 auto; }
.lateral {
  position: sticky; top: 59px; align-self: start; max-height: calc(100vh - 59px); overflow: auto;
  padding: 24px 12px 24px 24px; border-right: 1px solid #22121f;
}
.lateral h4 { margin: 0 0 10px; font: 700 12px "Orbitron", sans-serif; letter-spacing: 2px; color: var(--mudo); }
.lateral a { display: block; padding: 6px 10px; border-radius: 6px; text-decoration: none; color: var(--texto); font-weight: 500; line-height: 1.35; }
.lateral a:hover { background: var(--superficie); }
.lateral a.atual { background: var(--superficie2); color: var(--rosa-claro); border-left: 3px solid var(--rosa); }
.lateral .num { display: inline-block; width: 26px; color: var(--rosa); font-weight: 700; }
main { padding: 32px 48px 80px; min-width: 0; }
h1, h2, h3 { font-family: "Orbitron", sans-serif; line-height: 1.25; }
h1 { font-size: 34px; margin: 0 0 6px; }
h1 + p.sub { color: var(--mudo); margin-top: 0; font-size: 19px; }
h2 { font-size: 23px; margin-top: 46px; padding-bottom: 8px; border-bottom: 2px solid var(--rosa); display: inline-block; }
h3 { font-size: 18px; margin-top: 30px; color: var(--rosa-claro); }
code {
  font: 14.5px/1.5 "DejaVu Sans Mono", Consolas, monospace; background: var(--superficie2);
  padding: 2px 6px; border-radius: 4px; color: #ffd6f1;
}
pre {
  background: #0c070c; border: 1px solid #2c1428; border-left: 3px solid var(--rosa);
  border-radius: 8px; padding: 14px 16px; overflow-x: auto;
}
pre code { background: none; padding: 0; color: var(--texto); }
table { border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 16px; }
th, td { border: 1px solid #2c1428; padding: 8px 12px; text-align: left; vertical-align: top; }
th { background: var(--superficie2); color: var(--rosa-claro); }
tr:nth-child(even) td { background: #0b060b; }
blockquote { margin: 18px 0; padding: 10px 18px; border-left: 3px solid var(--mudo); background: var(--superficie); color: #e0cfdb; }
.admonition { margin: 22px 0; padding: 14px 18px; border-radius: 8px; background: var(--superficie); border-left: 4px solid var(--rosa); }
.admonition-title { margin: 0 0 6px; font-weight: 700; font-family: "Orbitron", sans-serif; font-size: 14px; letter-spacing: 1px; }
.admonition.objetivo { border-color: var(--rosa); } .admonition.objetivo .admonition-title { color: var(--rosa); }
.admonition.cenario { border-color: #7aa2ff; } .admonition.cenario .admonition-title { color: #a3beff; }
.admonition.atencao { border-color: var(--amarelo); } .admonition.atencao .admonition-title { color: var(--amarelo); }
.admonition.erro { border-color: var(--vermelho); } .admonition.erro .admonition-title { color: var(--vermelho); }
.admonition.atacante { border-color: #b16cff; } .admonition.atacante .admonition-title { color: #c9a0ff; }
.admonition.dica { border-color: var(--verde); } .admonition.dica .admonition-title { color: var(--verde); }
details { margin: 14px 0; padding: 10px 16px; border: 1px dashed var(--rosa); border-radius: 8px; background: #0c070c; }
details summary { cursor: pointer; font-weight: 700; color: var(--rosa-claro); }
details[open] summary { margin-bottom: 10px; }
.passo { counter-increment: passo; }
.rodape-nav { display: flex; justify-content: space-between; gap: 16px; margin-top: 60px; padding-top: 20px; border-top: 1px solid #2c1428; }
.rodape-nav a { padding: 12px 18px; border: 1px solid #3a1630; border-radius: 8px; text-decoration: none; max-width: 48%; }
.rodape-nav a:hover { border-color: var(--rosa); }
.rodape-nav small { display: block; color: var(--mudo); }
.assinatura { margin-top: 40px; text-align: right; color: var(--rosa-claro); font-weight: 700; }
.cartoes { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 14px; margin: 22px 0; }
.cartao { display: block; padding: 16px; border: 1px solid #2c1428; border-radius: 10px; background: var(--superficie); text-decoration: none; color: var(--texto); }
.cartao:hover { border-color: var(--rosa); }
.cartao b { display: block; color: var(--rosa-claro); font-family: "Orbitron", sans-serif; font-size: 14px; margin-bottom: 4px; }
.cartao span { color: var(--mudo); font-size: 15px; line-height: 1.4; display: block; }
@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .lateral { position: static; max-height: none; border-right: 0; border-bottom: 1px solid #22121f; }
  main { padding: 24px 16px 60px; }
  .topo nav { display: none; }
}
"""

MODELO = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} | Treinamento Be Safe</title>
<link rel="stylesheet" href="estilo.css">
</head>
<body>
<header class="topo">
  <img src="logo.png" alt="">
  <a class="marca" href="index.html">BE SAFE <span>SOC LAB</span></a>
  <nav><a href="index.html">Início</a><a href="glossario.html">Glossário</a><a href="cola.html">Cola de comandos</a></nav>
</header>
<div class="layout">
  <aside class="lateral"><h4>MÓDULOS</h4>{menu}</aside>
  <main>
{conteudo}
{navegacao}
    <p class="assinatura">Powered By Mariana BS</p>
  </main>
</div>
</body>
</html>
"""


def titulo_de(texto):
    m = re.search(r"^#\s+(.+)$", texto, re.M)
    return m.group(1).strip() if m else "Sem título"


def nome_curto(titulo):
    """'Modulo 3: Redes' vira 'Redes' (o numero ja aparece no menu)."""
    return re.sub(r"^M[oó]dulo\s+\d+\s*[:.]?\s*", "", titulo)


def descricao_de(texto):
    m = re.search(r"^<!--\s*descricao:\s*(.+?)\s*-->", texto, re.M)
    return m.group(1) if m else ""


def converter(texto):
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "admonition", "md_in_html", "attr_list", "toc", "sane_lists"],
        extension_configs={"toc": {"permalink": False}},
    )
    return md.convert(texto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=str(RAIZ / "out"))
    ap.add_argument("--logo", default=str(RAIZ.parent / "branding" / "out" / "icone-128.png"))
    args = ap.parse_args()
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)

    arquivos = sorted(MODULOS.glob("[0-9][0-9]-*.md"))
    extras = [MODULOS / "glossario.md", MODULOS / "cola.md"]
    paginas = []
    for arq in arquivos:
        texto = arq.read_text(encoding="utf-8")
        num = arq.name[:2]
        paginas.append({"arq": arq, "html": arq.stem + ".html", "num": num,
                        "titulo": titulo_de(texto), "desc": descricao_de(texto), "texto": texto})

    def menu(atual):
        itens = []
        for p in paginas:
            classe = ' class="atual"' if p["html"] == atual else ""
            nome = nome_curto(p["titulo"])
            itens.append(f'<a{classe} href="{p["html"]}"><span class="num">{int(p["num"])}</span>{html.escape(nome)}</a>')
        return "\n".join(itens)

    for i, p in enumerate(paginas):
        ant = paginas[i - 1] if i > 0 else None
        prox = paginas[i + 1] if i + 1 < len(paginas) else None
        nav = ['<div class="rodape-nav">']
        nav.append(f'<a href="{ant["html"]}"><small>anterior</small>{html.escape(ant["titulo"])}</a>' if ant else "<span></span>")
        nav.append(f'<a href="{prox["html"]}" style="text-align:right"><small>próximo</small>{html.escape(prox["titulo"])}</a>' if prox else "<span></span>")
        nav.append("</div>")
        (saida / p["html"]).write_text(
            MODELO.format(titulo=html.escape(p["titulo"]), menu=menu(p["html"]),
                          conteudo=converter(p["texto"]), navegacao="\n".join(nav)),
            encoding="utf-8")

    for arq in extras:
        if arq.exists():
            texto = arq.read_text(encoding="utf-8")
            (saida / (arq.stem + ".html")).write_text(
                MODELO.format(titulo=html.escape(titulo_de(texto)), menu=menu(""),
                              conteudo=converter(texto), navegacao=""),
                encoding="utf-8")

    cartoes = "\n".join(
        f'<a class="cartao" href="{p["html"]}"><b>{int(p["num"]):02d}. {html.escape(nome_curto(p["titulo"]))}</b>'
        f'<span>{html.escape(p["desc"])}</span></a>'
        for p in paginas)
    indice = (MODULOS / "index.md").read_text(encoding="utf-8")
    corpo = converter(indice).replace("<p>{{cartoes}}</p>", f'<div class="cartoes">{cartoes}</div>')
    (saida / "index.html").write_text(
        MODELO.format(titulo="Início", menu=menu("index.html"), conteudo=corpo, navegacao=""),
        encoding="utf-8")

    (saida / "estilo.css").write_text(CSS, encoding="utf-8")
    if Path(args.logo).exists():
        shutil.copy(args.logo, saida / "logo.png")
    print(f"{len(paginas)} modulos gerados em {saida}")


if __name__ == "__main__":
    main()
