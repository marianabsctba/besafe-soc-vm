"""Gera os e-mails de treino do modulo 8 (inertes).

Todos os dominios usam o TLD reservado .example (RFC 2606) e os IPs as faixas de
documentacao (RFC 5737). O anexo PDF contem apenas um JavaScript que exibe uma
mensagem de treinamento. Nenhuma empresa ou marca real e imitada.

Uso: python3 gerar_amostras.py [pasta]   (padrao: a pasta deste script)
"""
import sys
from email.message import EmailMessage
from email.utils import format_datetime
from datetime import datetime, timezone, timedelta
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
SAIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent


def pdf_treino():
    """PDF minimo com /OpenAction e /JavaScript que so mostra um aviso."""
    js = b"app.alert('Treinamento Be Safe: este PDF tentou executar JavaScript ao abrir.');"
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R /OpenAction 4 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 5 0 R /Resources << /Font << /F1 6 0 R >> >> >>",
        b"<< /Type /Action /S /JavaScript /JS (" + js + b") >>",
        None,  # conteudo da pagina, montado abaixo
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Title (Boleto Outubro) /Author (Financeiro) /Creator (Gerador de Boletos 3.1) "
        b"/Producer (Treinamento Be Safe) /CreationDate (D:20261020091512-03'00') >>",
    ]
    texto = b"BT /F1 14 Tf 72 760 Td (Boleto - Transportes Andorinha - Outubro) Tj ET"
    objetos[4] = b"<< /Length " + str(len(texto)).encode() + b" >>\nstream\n" + texto + b"\nendstream"

    saida = bytearray(b"%PDF-1.4\n")
    deslocamentos = []
    for i, corpo in enumerate(objetos, start=1):
        deslocamentos.append(len(saida))
        saida += f"{i} 0 obj\n".encode() + corpo + b"\nendobj\n"
    inicio_xref = len(saida)
    saida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for d in deslocamentos:
        saida += f"{d:010d} 00000 n \n".encode()
    saida += (f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R /Info 7 0 R >>\n"
              f"startxref\n{inicio_xref}\n%%EOF\n").encode()
    return bytes(saida)


def boleto_falso():
    m = EmailMessage()
    m["Return-Path"] = "<financeiro@transportes-andorinha.example>"
    m["Received"] = ("from mail.andorinha-cobranca.example (unknown [203.0.113.66]) "
                     "by mx.pantera-logistica.example with ESMTP id 4F2A1; Tue, 20 Oct 2026 09:17:03 -0300")
    m["Authentication-Results"] = ("mx.pantera-logistica.example; spf=fail "
                                   "(domain of transportes-andorinha.example does not designate 203.0.113.66 as permitted sender) "
                                   "smtp.mailfrom=transportes-andorinha.example; dkim=none; dmarc=fail header.from=transportes-andorinha.example")
    m["From"] = "Transportes Andorinha - Financeiro <financeiro@transportes-andorinha.example>"
    m["Reply-To"] = "financeiro.andorinha@correio-rapido.example"
    m["To"] = "contas.pagar@pantera-logistica.example"
    m["Subject"] = "URGENTE: boleto de outubro com novos dados bancarios"
    m["Date"] = format_datetime(datetime(2026, 10, 20, 9, 17, 0, tzinfo=BRT))
    m["Message-ID"] = "<20261020091700.4F2A1@andorinha-cobranca.example>"
    m["X-Mailer"] = "PHPMailer 6.8.1"
    m.set_content(
        "Prezados,\n\n"
        "Informamos que, devido a uma mudanca no nosso banco, o boleto de outubro foi emitido com NOVOS DADOS BANCARIOS.\n"
        "Pedimos a gentileza de efetuar o pagamento HOJE para evitar a suspensao dos servicos de transporte.\n\n"
        "O boleto segue em anexo. Caso nao consiga abrir, acesse: http://boletos.andorinha-pagamentos.example/2via?id=88213\n\n"
        "Qualquer duvida, responda este e-mail.\n\n"
        "Atenciosamente,\nDepartamento Financeiro\nTransportes Andorinha\n")
    m.add_attachment(pdf_treino(), maintype="application", subtype="pdf", filename="boleto_outubro.pdf")
    return m


def senha_expirando():
    m = EmailMessage()
    m["Return-Path"] = "<noreply@pantera-logistica-suporte.example>"
    m["Received"] = ("from smtp.pantera-logistica-suporte.example (unknown [198.51.100.140]) "
                     "by mx.pantera-logistica.example with ESMTPS id 7C11B; Wed, 21 Oct 2026 07:02:41 -0300")
    m["Authentication-Results"] = ("mx.pantera-logistica.example; spf=pass smtp.mailfrom=pantera-logistica-suporte.example; "
                                   "dkim=pass header.d=pantera-logistica-suporte.example; dmarc=pass header.from=pantera-logistica-suporte.example")
    m["From"] = "Suporte de TI <suporte@pantera-logistica-suporte.example>"
    m["To"] = "joana.lima@pantera-logistica.example"
    m["Subject"] = "Sua senha expira hoje - acao necessaria"
    m["Date"] = format_datetime(datetime(2026, 10, 21, 7, 2, 30, tzinfo=BRT))
    m["Message-ID"] = "<7C11B.20261021@pantera-logistica-suporte.example>"
    texto = ("Ola,\n\nSua senha de rede expira hoje. Para manter o acesso, confirme seus dados em:\n"
             "https://portal.pantera-logistica.example/senha\n\nEquipe de TI\n")
    html = ("<html><body style='font-family:Arial'>"
            "<p>Ol&aacute;,</p><p>Sua senha de rede <b>expira hoje</b>. Para manter o acesso, confirme seus dados em:</p>"
            "<p><a href='http://pantera-logistica.login-seguro.example/owa/auth.php?u=joana.lima'>"
            "https://portal.pantera-logistica.example/senha</a></p>"
            "<p>Se n&atilde;o confirmar em 2 horas, sua conta ser&aacute; bloqueada.</p>"
            "<p>Equipe de TI</p></body></html>")
    m.set_content(texto)
    m.add_alternative(html, subtype="html")
    return m


def legitimo():
    m = EmailMessage()
    m["Return-Path"] = "<rh@pantera-logistica.example>"
    m["Received"] = ("from exch01.pantera-logistica.example (exch01.pantera-logistica.example [10.10.2.15]) "
                     "by mx.pantera-logistica.example with ESMTPS id 1A9D0; Thu, 22 Oct 2026 10:30:12 -0300")
    m["Authentication-Results"] = ("mx.pantera-logistica.example; spf=pass smtp.mailfrom=pantera-logistica.example; "
                                   "dkim=pass header.d=pantera-logistica.example; dmarc=pass header.from=pantera-logistica.example")
    m["From"] = "Recursos Humanos <rh@pantera-logistica.example>"
    m["To"] = "todos@pantera-logistica.example"
    m["Subject"] = "Campanha de vacinacao na sede - quinta-feira"
    m["Date"] = format_datetime(datetime(2026, 10, 22, 10, 30, 0, tzinfo=BRT))
    m["Message-ID"] = "<1A9D0.20261022@exch01.pantera-logistica.example>"
    m.set_content(
        "Ola, pessoal!\n\nNesta quinta-feira, das 9h as 16h, teremos vacinacao contra a gripe na sala 3 da sede.\n"
        "Nao e necessario agendar. Leve um documento com foto.\n\nRH Pantera Logistica\n")
    return m


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    for nome, msg in (("01-boleto.eml", boleto_falso()), ("02-senha.eml", senha_expirando()),
                      ("03-rh.eml", legitimo())):
        (SAIDA / nome).write_bytes(bytes(msg))
    print("amostras geradas em", SAIDA)


if __name__ == "__main__":
    main()
