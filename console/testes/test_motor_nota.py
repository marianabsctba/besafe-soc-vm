"""Testes do motor de cenarios e da nota. Rodar: python -m pytest console/testes (ou python console/testes/test_motor_nota.py)"""
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from besafe.motor import BRT, MARCADOR, carregar_cenarios, instanciar, linha_json, montar_plantao  # noqa: E402
from besafe.mundo import gerar_mundo  # noqa: E402
from besafe.nota import avaliar, nota_do_plantao  # noqa: E402

INICIO = datetime(2026, 10, 26, 14, 0, tzinfo=BRT)
CENARIOS = carregar_cenarios()


def test_mundo_deterministico_e_ips_unicos():
    for semente in range(100):
        m1, m2 = gerar_mundo(semente), gerar_mundo(semente)
        assert m1.como_dict() == m2.como_dict()
        ips = [m.ip for m in m1.maquinas]
        assert len(ips) == len(set(ips))
        assert m1.maquina("SRV-SCAN01").ip == "10.10.1.50"


def test_todos_os_cenarios_resolvem_os_marcadores():
    mundo = gerar_mundo(7)
    for cid, cenario in CENARIOS.items():
        caso = instanciar(cenario, mundo, random.Random(1), "PL-0001", INICIO)
        assert caso.eventos, cid
        for _, evento in caso.eventos:
            assert not MARCADOR.findall(linha_json(evento)), cid
            assert evento["besafe"]["caso"] == "PL-0001"
        assert caso.verdade["classificacao"] in {"vp", "fp", "vpb"}
        assert len(caso.dicas) == 3, cid


def test_ips_externos_so_de_documentacao():
    mundo = gerar_mundo(11)
    for cenario in CENARIOS.values():
        caso = instanciar(cenario, mundo, random.Random(3), "PL-0002", INICIO)
        for _, ev in caso.eventos:
            texto = linha_json(ev)
            for faixa in ("8.8.", "1.1.1.1"):
                assert faixa not in texto


def test_plantao_tem_ataque_e_ruido_e_muda_com_a_semente():
    for numero in range(1, 6):
        casos = montar_plantao(CENARIOS, gerar_mundo(99), numero, INICIO)
        tipos = [c.verdade["classificacao"] for c in casos]
        assert len(casos) == 6
        assert tipos.count("vp") >= 2 and len(tipos) - tipos.count("vp") >= 2
        assert len({c.id for c in casos}) == 6
    a = [c.id for c in montar_plantao(CENARIOS, gerar_mundo(1), 1, INICIO)]
    b = [c.id for c in montar_plantao(CENARIOS, gerar_mundo(2), 1, INICIO)]
    assert a != b


def test_nota():
    verdade = {"classificacao": "vp", "severidade": "critica", "escalar": True,
               "iocs": ["203.0.113.9", "ruim.example"], "taticas": []}
    perfeito = {"classificacao": "vp", "severidade": "critica", "escalar": True,
                "iocs": ["203.0.113[.]9", "hxxp://ruim[.]example/x"], "resumo": "x" * 90}
    assert avaliar(perfeito, verdade)["total"] == 100
    assert avaliar(perfeito, verdade, dicas_usadas=2)["total"] == 90
    errado = dict(perfeito, classificacao="fp", escalar=False, severidade="baixa")
    assert avaliar(errado, verdade)["total"] == 20  # so indicadores e resumo
    benigno = {"classificacao": "vpb", "severidade": "baixa", "escalar": False, "iocs": [], "taticas": []}
    quase = {"classificacao": "fp", "severidade": "baixa", "escalar": False, "iocs": [], "resumo": "y" * 90}
    assert avaliar(quase, benigno)["total"] == 80
    plantao = nota_do_plantao(["A", "B"], {"A": {"total": 100}})
    assert plantao["media"] == 50 and plantao["perdidos"] == ["B"]


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
