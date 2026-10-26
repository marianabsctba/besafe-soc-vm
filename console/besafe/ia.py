"""IA local: sobe o llama-server (llama.cpp) sob demanda e conversa com ele.

- O servidor so e iniciado quando alguem usa um recurso de IA, e e derrubado depois de
  um tempo parado, para devolver a memoria (cerca de 3 GB) ao Wazuh.
- Se o binario ou o modelo nao existirem (ou a maquina nao aguentar), quem chama recebe
  None e usa a resposta escrita de reserva.
"""
import json
import os
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

PASTA = Path(os.environ.get("BESAFE_IA_DIR", "/opt/besafe/ia"))
BINARIO = PASTA / "llama-server"
MODELO = PASTA / "modelo.gguf"
PORTA = int(os.environ.get("BESAFE_IA_PORTA", "8081"))
OCIOSO_SEG = int(os.environ.get("BESAFE_IA_OCIOSO", "600"))
URL = f"http://127.0.0.1:{PORTA}"

_trava = threading.Lock()
_processo = None
_ultimo_uso = 0.0


def disponivel() -> bool:
    return BINARIO.exists() and MODELO.exists()


def _pronto() -> bool:
    try:
        with urllib.request.urlopen(f"{URL}/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _iniciar():
    global _processo
    if _processo and _processo.poll() is None:
        return
    nucleos = max(2, (os.cpu_count() or 4) - 1)
    _processo = subprocess.Popen(
        [str(BINARIO), "-m", str(MODELO), "--host", "127.0.0.1", "--port", str(PORTA),
         "-c", "4096", "-t", str(nucleos), "--no-webui"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(PASTA))
    limite = time.time() + 180
    while time.time() < limite:
        if _processo.poll() is not None:
            raise RuntimeError("llama-server encerrou ao iniciar")
        if _pronto():
            return
        time.sleep(1)
    raise RuntimeError("llama-server nao ficou pronto a tempo")


def parar():
    global _processo
    with _trava:
        if _processo and _processo.poll() is None:
            _processo.terminate()
            try:
                _processo.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _processo.kill()
        _processo = None


def vigiar_ociosidade():
    """Roda em segundo plano: derruba o modelo depois de OCIOSO_SEG sem uso."""
    while True:
        time.sleep(30)
        if _processo and _processo.poll() is None and time.time() - _ultimo_uso > OCIOSO_SEG:
            parar()


def conversar(sistema: str, mensagens: list, max_tokens: int = 350, temperatura: float = 0.3):
    """Devolve o texto da resposta, ou None se a IA nao estiver disponivel."""
    global _ultimo_uso
    if not disponivel():
        return None
    with _trava:
        try:
            _iniciar()
        except Exception:
            return None
        _ultimo_uso = time.time()
    corpo = json.dumps({
        "messages": [{"role": "system", "content": sistema}] + mensagens,
        "max_tokens": max_tokens, "temperature": temperatura,
        # modelos com "modo de raciocinio" (ex.: Qwen3) respondem direto
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode()
    req = urllib.request.Request(f"{URL}/v1/chat/completions", data=corpo,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            resposta = json.load(r)
        _ultimo_uso = time.time()
        texto = resposta["choices"][0]["message"]["content"] or ""
        # alguns modelos ainda devolvem o bloco de raciocinio; ele nao interessa ao aluno
        if "</think>" in texto:
            texto = texto.split("</think>", 1)[1]
        return texto.strip()
    except Exception:
        return None


# ------------------------------------------------------------------ papeis
SISTEMA_MENTOR = (
    "Você é um analista de SOC nível 2, experiente e paciente, orientando um analista N1 iniciante. "
    "Responda sempre em português do Brasil, em no máximo 4 frases. "
    "Você NÃO sabe a resposta do caso. Você recebe apenas uma DICA, e deve ajudar o N1 a raciocinar "
    "a partir dela, com perguntas e sugestões de onde olhar. Nunca diga se o caso é ataque ou não, "
    "nunca dê a severidade e nunca diga se deve escalar. Se o N1 pedir a resposta, recuse com gentileza "
    "e devolva uma pergunta que o ajude a pensar."
)

SISTEMA_PESSOA = (
    "Você está interpretando uma pessoa real de uma empresa, numa conversa com o analista de segurança "
    "que está investigando um incidente. Responda em português do Brasil, em até 3 frases, no tom de "
    "alguém que não é técnico e está um pouco nervoso. Use SOMENTE as informações da ficha abaixo. "
    "Se perguntarem algo que não está na ficha, diga que não lembra ou não sabe. Não invente fatos "
    "técnicos e nunca diga que é uma IA.\n\nFICHA:\n"
)

SISTEMA_COPILOTO = (
    "Você é o copiloto de IA do SOC. Resuma os eventos abaixo para o analista em português do Brasil, "
    "em até 5 linhas: o que aconteceu, em qual máquina, com qual usuário, e uma recomendação "
    "(classificação sugerida, severidade e se deve escalar)."
)
