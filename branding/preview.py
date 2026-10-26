"""Monta previas da VM (boot e desktop) para o README.

Uso: python branding/preview.py  (depois de build_assets.py)
Saida: docs/preview-boot.png e docs/preview-desktop.png
"""
from PIL import Image, ImageDraw, ImageFont

from build_assets import BLACK, MUTED, OUT, PINK, PINK_SOFT, ROOT, SURFACE, TEXT, texto, titulo

DOCS = ROOT.parent / "docs"
W, H = 1920, 1080


def _mono(tamanho):
    # fonte monoespacada do sistema, so para a previa (Windows ou Linux)
    for nome in ("consola.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default(tamanho)


MONO = _mono(20)

BANNER = [
    "   ____  _____    ____    _    _____ _____",
    "  | __ )| ____|  / ___|  / \\  |  ___| ____|",
    "  |  _ \\|  _|    \\___ \\ / _ \\ | |_  |  _|",
    "  | |_) | |___    ___) / ___ \\|  _| | |___",
    "  |____/|_____|  |____/_/   \\_\\_|   |_____|",
]


def boot():
    img = Image.new("RGBA", (W, H), BLACK + (255,))
    logo = Image.open(OUT / "plymouth-logo.png")
    trilho = Image.open(OUT / "plymouth-trilho.png")
    barra = Image.open(OUT / "plymouth-barra.png")
    ass = Image.open(OUT / "plymouth-assinatura.png")
    cx, cy = W // 2, H // 2
    img.alpha_composite(logo, (cx - logo.width // 2, cy - logo.height // 2 - 60))
    y = cy + logo.height // 2
    img.alpha_composite(trilho, (cx - trilho.width // 2, y))
    parcial = barra.crop((0, 0, int(barra.width * 0.62), barra.height))
    img.alpha_composite(parcial, (cx - barra.width // 2, y))
    img.alpha_composite(ass, (W - ass.width - 40, H - ass.height - 40))
    return img.convert("RGB")


def desktop():
    img = Image.open(OUT / "wallpaper-1920x1080.png").convert("RGBA")
    d = ImageDraw.Draw(img)

    # painel inferior do XFCE
    d.rectangle((0, H - 44, W, H), fill=SURFACE + (255,))
    d.line((0, H - 44, W, H - 44), fill=PINK, width=2)
    icone = Image.open(OUT / "icone-32.png")
    img.alpha_composite(icone, (12, H - 38))
    f = texto(22, True)
    x = 60
    for nome in ("Console Be Safe", "Wazuh", "Terminal", "Wireshark", "CyberChef"):
        d.text((x, H - 22), nome, font=f, fill=TEXT, anchor="lm")
        x += d.textlength(nome, font=f) + 36
    d.text((W - 20, H - 22), "plantao 01  |  26/10  08:00", font=f, fill=PINK_SOFT, anchor="rm")

    # janela de terminal com o banner de login
    jx, jy, jw, jh = 100, 290, 780, 470
    sombra = Image.new("RGBA", (jw + 30, jh + 30), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rectangle((15, 15, jw + 15, jh + 15), fill=PINK + (40,))
    img.alpha_composite(sombra, (jx - 15, jy - 15))
    d.rectangle((jx, jy, jx + jw, jy + jh), fill=BLACK + (250,), outline=PINK, width=2)
    d.rectangle((jx, jy, jx + jw, jy + 38), fill=SURFACE + (255,))
    d.text((jx + 16, jy + 19), "analista@besafe: ~", font=titulo(16), fill=TEXT, anchor="lm")
    for i, cor in enumerate((PINK, MUTED, MUTED)):
        d.ellipse((jx + jw - 30 - i * 26, jy + 12, jx + jw - 16 - i * 26, jy + 26), fill=cor)

    y = jy + 58
    for linha in BANNER:
        d.text((jx + 16, y), linha, font=MONO, fill=PINK)
        y += 26
    y += 14
    linhas = [
        ("  SOC LAB  //  ANALISTA N1        versao 0.1.0", TEXT),
        ("", TEXT),
        ("  Console do plantao:  http://localhost:8080", MUTED),
        ("  Wazuh:               https://localhost", MUTED),
        ("", TEXT),
        ("                              Powered By Mariana BS", PINK_SOFT),
    ]
    for s, cor in linhas:
        d.text((jx + 16, y), s, font=texto(22), fill=cor)
        y += 28
    d.text((jx + 16, y + 6), "analista@besafe", font=texto(22, True), fill=PINK)
    d.text((jx + 16 + d.textlength("analista@besafe", font=texto(22, True)), y + 6), ":~$ _", font=texto(22, True), fill=TEXT)
    return img.convert("RGB")


if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    boot().save(DOCS / "preview-boot.png")
    desktop().save(DOCS / "preview-desktop.png")
    print("previas em", DOCS)
