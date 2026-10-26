"""Certificado de conclusao do Be Safe SOC Lab (PNG), com selo dourado e hash.

O certificado e emitido localmente, sem verificacao online: o hash SHA-256 no rodape
resume os dados do certificado (nome, nota, data, plantao e semente da VM).
"""
import hashlib
import math
import os
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTES = Path(os.environ.get("BESAFE_FONTES", "/usr/local/share/fonts/besafe"))
BRANDING = Path(os.environ.get("BESAFE_BRANDING", "/usr/share/besafe/branding"))

L, A = 3300, 2334  # A4 deitado
PRETO = (6, 4, 8)
ROSA = (252, 19, 180)
ROSA_CLARO = (255, 111, 208)
TEXTO = (245, 233, 242)
MUDO = (170, 150, 165)
OURO_ESCURO = (150, 104, 30)
OURO = (212, 164, 64)
OURO_CLARO = (255, 226, 140)

APRENDIDO = [
    "Terminal Linux e análise de logs",
    "Redes: IP, portas, TCP, DNS e HTTP",
    "Windows pelos logs: processos e logons",
    "Fundamentos de SOC e triagem",
    "Wazuh (SIEM) e MITRE ATT&CK",
    "Suricata e Wireshark",
    "Caça em EVTX: Hayabusa e Chainsaw",
    "Análise de phishing e anexos",
    "CyberChef, YARA e Sigma",
    "Ticket, plantão e comunicação",
    "LGPD para o analista N1",
    "Plantão simulado com prova final",
]

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


# ------------------------------------------------------------------ utilidades
def _fonte(nome, tamanho, variacao=None):
    for pasta in (FONTES, Path(__file__).resolve().parents[2] / "branding" / "fonts"):
        caminho = pasta / nome
        if caminho.exists():
            f = ImageFont.truetype(str(caminho), tamanho)
            if variacao:
                f.set_variation_by_name(variacao)
            return f
    return ImageFont.load_default(tamanho)


def _mono(tamanho):
    for caminho in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "consola.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(caminho, tamanho)
        except OSError:
            continue
    return ImageFont.load_default(tamanho)


def titulo(t, v="Black"):
    return _fonte("Orbitron.ttf", t, v)


def corpo(t, negrito=False):
    return _fonte("Rajdhani-Bold.ttf" if negrito else "Rajdhani-Medium.ttf", t)


def _gradiente_vertical(tamanho, cores):
    """Imagem RGB com gradiente vertical passando pelas cores dadas."""
    w, h = tamanho
    im = Image.new("RGB", (1, h))
    px = im.load()
    trechos = len(cores) - 1
    for y in range(h):
        pos = y / max(1, h - 1) * trechos
        i = min(int(pos), trechos - 1)
        t = pos - i
        c = tuple(round(cores[i][k] + (cores[i + 1][k] - cores[i][k]) * t) for k in range(3))
        px[0, y] = c
    return im.resize((w, h))


def _texto_dourado(base, xy, texto, fonte, ancora="mm", brilho=True):
    """Desenha texto preenchido com gradiente dourado (e um leve brilho)."""
    d = ImageDraw.Draw(base)
    caixa = d.textbbox(xy, texto, font=fonte, anchor=ancora)
    w, h = caixa[2] - caixa[0], caixa[3] - caixa[1]
    mascara = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mascara).text((xy[0] - caixa[0], xy[1] - caixa[1]), texto, font=fonte, fill=255, anchor=ancora)
    ouro = _gradiente_vertical((w, h), [OURO_CLARO, OURO, OURO_ESCURO, OURO])
    if brilho:
        halo = Image.new("RGBA", (w + 80, h + 80), OURO + (0,))
        halo.putalpha(Image.new("L", (w + 80, h + 80), 0))
        m = Image.new("L", (w + 80, h + 80), 0)
        m.paste(mascara, (40, 40))
        halo.putalpha(m.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v // 3))
        base.alpha_composite(halo, (caixa[0] - 40, caixa[1] - 40))
    camada = Image.new("RGBA", (w, h))
    camada.paste(ouro, (0, 0))
    camada.putalpha(mascara)
    base.alpha_composite(camada, (caixa[0], caixa[1]))


def _espacado(d, xy, texto, fonte, cor, espaco, ancora_centro=True):
    """Texto com espacamento entre letras (letter-spacing)."""
    larguras = [d.textlength(c, font=fonte) for c in texto]
    total = sum(larguras) + espaco * (len(texto) - 1)
    x = xy[0] - total / 2 if ancora_centro else xy[0]
    for c, w in zip(texto, larguras):
        d.text((x, xy[1]), c, font=fonte, fill=cor, anchor="ls")
        x += w + espaco


# ------------------------------------------------------------------ partes
def _fundo():
    im = Image.new("RGBA", (L, A), PRETO + (255,))
    # brilho rosa difuso
    halo = Image.new("L", (L, A), 0)
    hd = ImageDraw.Draw(halo)
    hd.ellipse((L * 0.55, -A * 0.25, L * 1.35, A * 0.75), fill=60)
    hd.ellipse((-L * 0.35, A * 0.45, L * 0.45, A * 1.35), fill=34)
    halo = halo.filter(ImageFilter.GaussianBlur(320))
    im = Image.composite(Image.new("RGBA", (L, A), ROSA + (255,)), im, halo)
    # grade fina
    grade = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    g = ImageDraw.Draw(grade)
    for x in range(0, L, 66):
        g.line((x, 0, x, A), fill=ROSA + (9,))
    for y in range(0, A, 66):
        g.line((0, y, L, y), fill=ROSA + (9,))
    im.alpha_composite(grade)
    # pantera como marca d'agua
    try:
        p = Image.open(BRANDING / "pantera.png").convert("RGBA")
        p.thumbnail((1500, 1500), Image.LANCZOS)
        p.putalpha(p.split()[3].point(lambda v: v * 10 // 100))
        im.alpha_composite(p, (L - p.width - 40, (A - p.height) // 2 + 120))
    except FileNotFoundError:
        pass
    return im


def _molduras(im):
    d = ImageDraw.Draw(im)
    d.rectangle((58, 58, L - 58, A - 58), outline=OURO, width=5)
    d.rectangle((80, 80, L - 80, A - 80), outline=ROSA + (170,), width=2)
    d.rectangle((96, 96, L - 96, A - 96), outline=OURO_ESCURO + (140,), width=1)
    # cantos ornamentados
    for cx, cy, sx, sy in ((58, 58, 1, 1), (L - 58, 58, -1, 1), (58, A - 58, 1, -1), (L - 58, A - 58, -1, -1)):
        for k, cor in ((150, OURO_CLARO), (110, OURO)):
            d.line((cx, cy, cx + sx * k, cy), fill=cor, width=9)
            d.line((cx, cy, cx, cy + sy * k), fill=cor, width=9)
        dx, dy = cx + sx * 36, cy + sy * 36
        d.polygon([(dx, dy - 20), (dx + 20, dy), (dx, dy + 20), (dx - 20, dy)], fill=ROSA)


def _selo(raio=185):
    """Selo dourado com borda serrilhada, texto circular e fitas."""
    tam = raio * 2 + 120
    s = Image.new("RGBA", (tam, tam + 150), (0, 0, 0, 0))
    c = tam // 2
    d = ImageDraw.Draw(s)
    # fitas
    for lado in (-1, 1):
        x0 = c + lado * 58
        pts = [(x0 - 50, c + 90), (x0 + 50, c + 90), (x0 + 50 + lado * 30, c + raio + 96),
               (x0 + lado * 14, c + raio + 66), (x0 - 50 + lado * 30, c + raio + 96)]
        d.polygon(pts, fill=ROSA if lado < 0 else (196, 12, 140))
        d.line(pts + [pts[0]], fill=OURO, width=4)
    # sombra
    sombra = Image.new("L", s.size, 0)
    ImageDraw.Draw(sombra).ellipse((c - raio - 20, c - raio - 6, c + raio + 26, c + raio + 34), fill=170)
    s.alpha_composite(Image.merge("RGBA", (Image.new("L", s.size, 0),) * 3 + (sombra.filter(ImageFilter.GaussianBlur(22)),)))
    # borda serrilhada
    pontos = []
    for i in range(96):
        ang = 2 * math.pi * i / 96
        r = raio + 14 if i % 2 == 0 else raio - 6
        pontos.append((c + r * math.cos(ang), c + r * math.sin(ang)))
    disco = Image.new("L", s.size, 0)
    ImageDraw.Draw(disco).polygon(pontos, fill=255)
    ouro = Image.new("RGBA", s.size)
    ouro.paste(_gradiente_vertical(s.size, [OURO_CLARO, OURO, OURO_ESCURO, OURO, OURO_CLARO]), (0, 0))
    ouro.putalpha(disco)
    s.alpha_composite(ouro)
    d = ImageDraw.Draw(s)
    # aneis internos
    for r, cor, w in ((raio - 22, OURO_ESCURO, 5), (raio - 32, OURO_CLARO, 2), (raio - 92, OURO_ESCURO, 4), (raio - 100, OURO_CLARO, 2)):
        d.ellipse((c - r, c - r, c + r, c + r), outline=cor, width=w)
    # texto circular
    texto = "BE SAFE • SOC LAB • ANALISTA N1 • CERTIFICADO • "
    fonte = corpo(36, negrito=True)
    r_txt = raio - 62
    passo = 360 / len(texto)
    for i, ch in enumerate(texto):
        ang = -90 + i * passo
        letra = Image.new("RGBA", (56, 56), (0, 0, 0, 0))
        ImageDraw.Draw(letra).text((28, 28), ch, font=fonte, fill=(84, 54, 10), anchor="mm")
        letra = letra.rotate(-(ang + 90), resample=Image.BICUBIC)
        x = c + r_txt * math.cos(math.radians(ang)) - 28
        y = c + r_txt * math.sin(math.radians(ang)) - 28
        s.alpha_composite(letra, (round(x), round(y)))
    # centro: pantera
    try:
        p = Image.open(BRANDING / "pantera.png").convert("RGBA")
        p.thumbnail((150, 150), Image.LANCZOS)
        s.alpha_composite(p, (c - p.width // 2, c - p.height // 2 - 8))
    except FileNotFoundError:
        d.text((c, c), "N1", font=titulo(110), fill=(84, 54, 10), anchor="mm")
    # brilho
    luz = Image.new("L", s.size, 0)
    ImageDraw.Draw(luz).ellipse((c - raio * 0.7, c - raio * 0.95, c + raio * 0.1, c - raio * 0.35), fill=90)
    s.alpha_composite(Image.merge("RGBA", (Image.new("L", s.size, 255),) * 3 + (luz.filter(ImageFilter.GaussianBlur(40)),)))
    return s


# ------------------------------------------------------------------ certificado
def codigo(nome, nota, emissao, plantao, semente):
    dados = f"BESAFE-SOC-LAB|{nome}|{nota}|{emissao.isoformat()}|{plantao}|{semente}"
    return hashlib.sha256(dados.encode("utf-8")).hexdigest()


def conceito(nota):
    return "APROVADO COM DISTINÇÃO" if nota >= 90 else "APROVADO"


def gerar(nome: str, nota: int, plantao: int, semente: int, saida: Path, emissao: date = None) -> dict:
    emissao = emissao or date.today()
    nome = " ".join(nome.split())[:60]
    hash_hex = codigo(nome, nota, emissao, plantao, semente)

    im = _fundo()
    _molduras(im)
    d = ImageDraw.Draw(im)
    cx = L // 2

    # cabecalho
    try:
        p = Image.open(BRANDING / "pantera.png").convert("RGBA")
        p.thumbnail((230, 230), Image.LANCZOS)
        brilho = Image.new("RGBA", p.size, ROSA + (0,))
        brilho.putalpha(p.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v: v // 2))
        im.alpha_composite(brilho, (cx - p.width // 2, 140))
        im.alpha_composite(p, (cx - p.width // 2, 140))
    except FileNotFoundError:
        pass
    _espacado(d, (cx, 440), "BE SAFE  SOC LAB", titulo(46, "Bold"), TEXTO, 14)

    _texto_dourado(im, (cx, 590), "CERTIFICADO", titulo(172))
    _espacado(d, (cx, 735), "DE CONCLUSÃO", corpo(60, negrito=True), ROSA, 26)

    d.text((cx, 830), "Certificamos que", font=corpo(58), fill=MUDO, anchor="mm")

    # nome
    fonte_nome = corpo(170, negrito=True)
    while d.textlength(nome, font=fonte_nome) > L - 900 and fonte_nome.size > 90:
        fonte_nome = corpo(fonte_nome.size - 8, negrito=True)
    d.text((cx, 955), nome, font=fonte_nome, fill=TEXTO, anchor="mm")
    largura = max(900, d.textlength(nome, font=fonte_nome) + 160)
    linha = _gradiente_vertical((int(largura), 6), [OURO_CLARO, OURO])
    mascara = Image.new("L", linha.size, 0)
    md = ImageDraw.Draw(mascara)
    for x in range(linha.width):  # some nas pontas
        md.line((x, 0, x, 6), fill=round(255 * math.sin(math.pi * x / linha.width)))
    tira = Image.new("RGBA", linha.size)
    tira.paste(linha, (0, 0))
    tira.putalpha(mascara)
    im.alpha_composite(tira, (cx - linha.width // 2, 1045))

    # texto principal
    frase1 = "concluiu o treinamento Analista SOC N1 do Be Safe SOC Lab"
    frase2 = f"e obteve aprovação na prova final de plantão simulado com nota {nota}/100."
    d.text((cx, 1125), frase1, font=corpo(56), fill=TEXTO, anchor="mm")
    d.text((cx, 1190), frase2, font=corpo(56), fill=TEXTO, anchor="mm")

    # selo de conceito
    texto_conceito = conceito(nota)
    fc = corpo(42, negrito=True)
    wc = d.textlength(texto_conceito, font=fc) + 80
    d.rounded_rectangle((cx - wc / 2, 1240, cx + wc / 2, 1310), radius=35,
                        outline=OURO, width=3, fill=(40, 24, 8) if nota >= 90 else (30, 8, 24))
    d.text((cx, 1275), texto_conceito, font=fc, fill=OURO_CLARO if nota >= 90 else ROSA_CLARO, anchor="mm")

    # o que foi aprendido
    _espacado(d, (cx, 1405), "O QUE FOI APRENDIDO", titulo(38, "Bold"), ROSA_CLARO, 10)
    d.line((cx - 640, 1392, cx - 360, 1392), fill=ROSA, width=2)
    d.line((cx + 360, 1392, cx + 640, 1392), fill=ROSA, width=2)
    colunas, por_coluna = 3, 4
    larg_col = 820
    x0 = cx - larg_col * colunas / 2 + 60
    for i, item in enumerate(APRENDIDO):
        col, lin = divmod(i, por_coluna)
        x, y = x0 + col * larg_col, 1480 + lin * 64
        d.polygon([(x, y - 12), (x + 12, y), (x, y + 12), (x - 12, y)], fill=ROSA)
        d.text((x + 30, y), item, font=corpo(44), fill=TEXTO, anchor="lm")

    # rodape: data, selo e assinatura
    base_y = 1985
    meses = MESES[emissao.month - 1]
    d.line((330, base_y, 1030, base_y), fill=OURO, width=3)
    d.text((680, base_y + 50), f"{emissao.day} de {meses} de {emissao.year}", font=corpo(50, True), fill=TEXTO, anchor="mm")
    d.text((680, base_y + 105), "Data de emissão", font=corpo(40), fill=MUDO, anchor="mm")

    d.line((L - 1030, base_y, L - 330, base_y), fill=OURO, width=3)
    d.text((L - 680, base_y + 50), "Mariana BS - Cybersecurity Engineer", font=corpo(50, True), fill=TEXTO, anchor="mm")
    d.text((L - 680, base_y + 105), "Be Safe", font=corpo(40), fill=MUDO, anchor="mm")

    selo = _selo()
    im.alpha_composite(selo, (cx - selo.width // 2, 1902 - selo.width // 2))

    # hash
    fm = _mono(30)
    d.text((cx, A - 128), f"SHA-256  {hash_hex}", font=fm, fill=MUDO, anchor="mm")
    d.text((L - 140, A - 128), "Powered By Mariana BS", font=corpo(40, True), fill=ROSA_CLARO, anchor="rm")
    d.text((140, A - 128), f"Prova final: plantão {plantao}", font=corpo(36), fill=MUDO, anchor="lm")

    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(saida, optimize=True)
    return {"arquivo": str(saida), "hash": hash_hex, "conceito": texto_conceito, "nome": nome, "nota": nota,
            "emissao": emissao.isoformat()}


if __name__ == "__main__":  # pre-visualizacao: python -m besafe.certificado
    import sys
    r = gerar(sys.argv[1] if len(sys.argv) > 1 else "Ana Beatriz Souza", int(sys.argv[2]) if len(sys.argv) > 2 else 92,
              3, 123456789, Path(sys.argv[3] if len(sys.argv) > 3 else "certificado-exemplo.png"))
    print(r)
