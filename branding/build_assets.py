"""Gera as artes da VM Be Safe a partir de branding/src/pantera.webp.

Uso: python branding/build_assets.py
Saida: branding/out/ (papel de parede, login, GRUB, Plymouth, logos)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "pantera.webp"
FONTS = ROOT / "fonts"
OUT = ROOT / "out"

# Paleta Be Safe (rosa amostrado do logo original)
BLACK = (5, 4, 7)
SURFACE = (18, 10, 18)
PINK = (252, 19, 180)
PINK_SOFT = (255, 111, 208)
TEXT = (245, 233, 242)
MUTED = (150, 120, 140)

ASSINATURA = "Powered By Mariana BS"


def fonte(nome, tamanho, variacao=None):
    f = ImageFont.truetype(str(FONTS / nome), tamanho)
    if variacao:
        f.set_variation_by_name(variacao)
    return f


def titulo(tamanho):
    return fonte("Orbitron.ttf", tamanho, "Black")


def texto(tamanho, negrito=False):
    return fonte("Rajdhani-Bold.ttf" if negrito else "Rajdhani-Medium.ttf", tamanho)


def pantera_recortada():
    """Pantera com fundo transparente; o preto interno da cabeca continua opaco."""
    im = Image.open(SRC).convert("RGB")
    # remove a barra rosa do topo do arquivo original
    im = im.crop((0, 120, im.width, im.height))
    lum = im.convert("L")
    # tudo que for quase preto e estiver ligado a borda vira fundo
    mascara = lum.point(lambda v: 255 if v > 28 else 0)
    # fecha as frestas do contorno (boca, bigode) para o preenchimento nao vazar
    preenchida = mascara.filter(ImageFilter.MaxFilter(15))
    ImageDraw.floodfill(preenchida, (0, 0), 128, thresh=0)
    fundo = preenchida.point(lambda v: 255 if v == 128 else 0)
    alfa = fundo.point(lambda v: 0 if v else 255).filter(ImageFilter.GaussianBlur(1.2))
    # o brilho rosa nas bordas mantem a transparencia proporcional ao rosa
    brilho = lum.point(lambda v: 0 if v < 20 else min(255, v * 3))
    alfa = Image.composite(Image.new("L", im.size, 255), brilho, alfa.point(lambda v: 255 if v > 250 else 0))
    rgba = im.convert("RGBA")
    rgba.putalpha(alfa)
    return rgba.crop(rgba.getbbox())


def fundo_neon(w, h, foco=(0.68, 0.5)):
    """Fundo preto com halo rosa suave e grade discreta de SOC."""
    base = Image.new("RGB", (w, h), BLACK)
    halo = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(halo)
    cx, cy = int(w * foco[0]), int(h * foco[1])
    r = int(min(w, h) * 0.55)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=34)
    halo = halo.filter(ImageFilter.GaussianBlur(r // 2))
    base = Image.composite(Image.new("RGB", (w, h), PINK), base, halo)

    grade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(grade)
    passo = max(40, w // 40)
    for x in range(0, w, passo):
        g.line((x, 0, x, h), fill=PINK + (10,))
    for y in range(0, h, passo):
        g.line((0, y, w, y), fill=PINK + (10,))
    base = base.convert("RGBA")
    base.alpha_composite(grade)
    return base


def colar_pantera(img, pantera, altura, centro):
    menor = pantera.copy()
    menor.thumbnail((altura * 2, altura), Image.LANCZOS)
    # margem transparente para o brilho nao ser cortado nas bordas
    pad = altura // 8
    p = Image.new("RGBA", (menor.width + 2 * pad, menor.height + 2 * pad), (0, 0, 0, 0))
    p.alpha_composite(menor, (pad, pad))
    brilho = p.split()[3].filter(ImageFilter.GaussianBlur(altura // 25))
    glow = Image.new("RGBA", p.size, PINK + (0,))
    glow.putalpha(brilho.point(lambda v: v // 2))
    x, y = centro[0] - p.width // 2, centro[1] - p.height // 2
    img.alpha_composite(glow, (x, y))
    img.alpha_composite(p, (x, y))


def escrever(d, xy, s, f, cor, ancora="la"):
    d.text(xy, s, font=f, fill=cor, anchor=ancora)


def assinatura(img, escala, base=40):
    """base: distancia da borda inferior (maior no desktop, acima do painel do XFCE)."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    m = int(40 * escala)
    b = int(base * escala)
    f = texto(int(30 * escala), negrito=True)
    escrever(d, (w - m, h - b), ASSINATURA, f, PINK_SOFT, "rs")
    larg = d.textlength(ASSINATURA, font=f)
    y = h - b + int(10 * escala)
    d.line((w - m - larg, y, w - m, y), fill=PINK, width=max(2, int(3 * escala)))


def papel_de_parede(pantera, w, h):
    img = fundo_neon(w, h)
    e = h / 1080
    colar_pantera(img, pantera, int(h * 0.60), (int(w * 0.70), int(h * 0.47)))
    d = ImageDraw.Draw(img)
    x = int(w * 0.07)
    escrever(d, (x, int(h * 0.36)), "BE SAFE", titulo(int(110 * e)), TEXT)
    escrever(d, (x + int(6 * e), int(h * 0.50)), "SOC  LAB  //  ANALISTA N1", texto(int(44 * e), True), PINK)
    d.rectangle((x, int(h * 0.585), x + int(120 * e), int(h * 0.585) + int(6 * e)), fill=PINK)
    escrever(d, (x + int(4 * e), int(h * 0.62)), "detectar  .  triar  .  escalar", texto(int(32 * e)), MUTED)
    assinatura(img, e, base=90)
    return img.convert("RGB")


def tela_login(pantera, w, h):
    img = fundo_neon(w, h, foco=(0.5, 0.42))
    e = h / 1080
    colar_pantera(img, pantera, int(h * 0.42), (w // 2, int(h * 0.30)))
    d = ImageDraw.Draw(img)
    escrever(d, (w // 2, int(h * 0.58)), "BE SAFE  SOC LAB", titulo(int(54 * e)), TEXT, "mm")
    assinatura(img, e)
    return img.convert("RGB")


def grub(pantera, w, h):
    img = Image.new("RGBA", (w, h), BLACK + (255,))
    e = h / 1080
    colar_pantera(img, pantera, int(h * 0.34), (w // 2, int(h * 0.22)))
    assinatura(img, e)
    return img.convert("RGB")


def plymouth(pantera):
    """Logo e assinatura separados: o script do Plymouth anima o logo."""
    logo = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
    colar_pantera(logo, pantera, 300, (210, 210))
    f = texto(30, negrito=True)
    medida = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), ASSINATURA, font=f)
    ass = Image.new("RGBA", (medida[2] + 8, medida[3] + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(ass)
    d.text((4, 0), ASSINATURA, font=f, fill=PINK_SOFT)
    d.line((4, ass.height - 4, ass.width - 4, ass.height - 4), fill=PINK, width=3)
    barra = Image.new("RGBA", (360, 6), PINK + (255,))
    trilho = Image.new("RGBA", (360, 6), SURFACE + (255,))
    return logo, ass, barra, trilho


def main():
    OUT.mkdir(exist_ok=True)
    pantera = pantera_recortada()
    pantera.save(OUT / "pantera.png")
    for tam in (256, 128, 64, 48, 32):
        ic = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
        p = pantera.copy()
        p.thumbnail((tam, tam), Image.LANCZOS)
        ic.alpha_composite(p, ((tam - p.width) // 2, (tam - p.height) // 2))
        ic.save(OUT / f"icone-{tam}.png")

    for w, h in ((1920, 1080), (2560, 1440), (1366, 768)):
        papel_de_parede(pantera, w, h).save(OUT / f"wallpaper-{w}x{h}.png")
    tela_login(pantera, 1920, 1080).save(OUT / "login.png")
    grub(pantera, 1920, 1080).save(OUT / "grub-fundo.png")
    # pecas da caixa de selecao do menu do GRUB (styled box)
    for peca in ("c", "n", "s", "e", "w", "ne", "nw", "se", "sw"):
        Image.new("RGB", (4, 4), PINK).save(OUT / f"grub-sel_{peca}.png")

    logo, ass, barra, trilho = plymouth(pantera)
    logo.save(OUT / "plymouth-logo.png")
    ass.save(OUT / "plymouth-assinatura.png")
    barra.save(OUT / "plymouth-barra.png")
    trilho.save(OUT / "plymouth-trilho.png")
    print("artes geradas em", OUT)


if __name__ == "__main__":
    main()
