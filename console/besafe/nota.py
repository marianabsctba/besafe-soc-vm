"""Nota deterministica: compara o ticket do aluno com a verdade do cenario.

A IA nunca participa da nota. Cada criterio devolve pontos e um comentario, para o
aluno entender o que acertou e o que faltou.
"""
SEVERIDADES = ["baixa", "media", "alta", "critica"]
ROTULO_SEVERIDADE = {"baixa": "baixa", "media": "média", "alta": "alta", "critica": "crítica"}
NOMES_CLASSIFICACAO = {
    "vp": "verdadeiro positivo (ataque)",
    "fp": "falso positivo",
    "vpb": "verdadeiro positivo benigno (autorizado)",
}
PESOS = {"classificacao": 40, "escalar": 25, "severidade": 15, "iocs": 15, "resumo": 5}
CUSTO_DICA = 5


def _normalizar(texto):
    return (texto or "").strip().lower().replace("[.]", ".").replace("hxxp", "http").replace("[@]", "@")


def avaliar(ticket: dict, verdade: dict, dicas_usadas: int = 0) -> dict:
    itens = []

    # classificacao
    esperado, dado = verdade["classificacao"], ticket.get("classificacao")
    if dado == esperado:
        pts, msg = PESOS["classificacao"], f"Classificação correta: {NOMES_CLASSIFICACAO[esperado]}."
    elif {dado, esperado} <= {"fp", "vpb"}:
        pts = PESOS["classificacao"] // 2
        msg = (f"Quase: não era ataque, mas o certo era {NOMES_CLASSIFICACAO[esperado]}. "
               "Benigno é quando o comportamento é real e autorizado; falso positivo é quando a regra se enganou.")
    else:
        pts = 0
        msg = f"Classificação incorreta: o esperado era {NOMES_CLASSIFICACAO[esperado]}."
    itens.append(("classificacao", pts, msg))

    # escalonamento
    escalar = bool(ticket.get("escalar"))
    if escalar == verdade["escalar"]:
        pts = PESOS["escalar"]
        msg = "Decisão de escalonamento correta." if escalar else "Correto não escalar."
    else:
        pts = 0
        msg = ("Este caso precisava ser escalado ao N2." if verdade["escalar"]
               else "Este caso não precisava de escalonamento: na dúvida é melhor escalar, mas aqui havia como resolver no N1.")
    itens.append(("escalar", pts, msg))

    # severidade
    try:
        diferenca = abs(SEVERIDADES.index(ticket.get("severidade")) - SEVERIDADES.index(verdade["severidade"]))
    except ValueError:
        diferenca = 9
    if diferenca == 0:
        pts, msg = PESOS["severidade"], f"Severidade correta ({ROTULO_SEVERIDADE[verdade['severidade']]})."
    elif diferenca == 1:
        pts, msg = 8, f"Severidade próxima: o esperado era {ROTULO_SEVERIDADE[verdade['severidade']]}."
    else:
        pts, msg = 0, f"Severidade distante: o esperado era {ROTULO_SEVERIDADE[verdade['severidade']]}."
    itens.append(("severidade", pts, msg))

    # indicadores
    esperados = [_normalizar(i) for i in verdade.get("iocs", [])]
    texto_aluno = _normalizar(" ".join(ticket.get("iocs", [])) + " " + (ticket.get("resumo") or ""))
    if not esperados:
        pts, msg = PESOS["iocs"], "Este caso não tinha indicadores a listar."
    else:
        achados = [i for i in esperados if i in texto_aluno]
        pts = round(PESOS["iocs"] * len(achados) / len(esperados))
        faltando = [i for i in esperados if i not in achados]
        msg = f"Indicadores: {len(achados)} de {len(esperados)}."
        if faltando:
            msg += " Faltou: " + ", ".join(faltando) + "."
    itens.append(("iocs", pts, msg))

    # resumo
    resumo = (ticket.get("resumo") or "").strip()
    if len(resumo) >= 80:
        pts, msg = PESOS["resumo"], "Resumo registrado."
    else:
        pts, msg = 0, "Resumo muito curto: descreva o que viu, onde, quando e a sua avaliação (módulo 10)."
    itens.append(("resumo", pts, msg))

    bruto = sum(p for _, p, _ in itens)
    desconto = CUSTO_DICA * max(0, dicas_usadas)
    if desconto:
        itens.append(("dicas", -desconto, f"{dicas_usadas} dica(s) do mentor: -{desconto} pontos."))
    total = max(0, bruto - desconto)
    return {"total": total, "maximo": sum(PESOS.values()),
            "itens": [{"criterio": c, "pontos": p, "comentario": m} for c, p, m in itens]}


def nota_do_plantao(casos_ids: list, avaliacoes: dict) -> dict:
    """Media do plantao. Caso sem ticket vale zero: e um alerta perdido."""
    notas, perdidos = [], []
    for cid in casos_ids:
        if cid in avaliacoes:
            notas.append(avaliacoes[cid]["total"])
        else:
            notas.append(0)
            perdidos.append(cid)
    media = round(sum(notas) / len(notas)) if notas else 0
    return {"media": media, "casos": len(casos_ids), "com_ticket": len(casos_ids) - len(perdidos),
            "perdidos": perdidos}
