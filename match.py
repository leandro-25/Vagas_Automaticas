"""Match CV x vaga via Groq (OpenAI-compatible), com rotacao de modelos,
minimo de tokens e respeito a limite por minuto. Nao loga a chave."""
import os
import re
import time
import json
import random
import itertools
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE, "groq_key.txt")
PERFIL_FILE = os.path.join(BASE, "perfil_cv.txt")
CV_FILE = os.path.join(BASE, "cv_text.txt")

# Rodizio: uma analise por modelo, em ciclo (poupa cota de cada um).
# Validados em 2026-09-22: so a familia gpt-oss responde nesta chave.
MODELOS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-safeguard-20b",
]
GAP_SEG = 5          # intervalo minimo entre chamadas (limite por minuto)
MAX_TOKENS = 512     # teto (modelo para cedo; resposta real ~100 tokens)
TIMEOUT = 40

_cycle = itertools.cycle(MODELOS)
_ultima_chamada = 0.0


def get_key():
    k = os.environ.get("GROQ_API_KEY", "").strip()
    if k:
        return k
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, encoding="utf-8") as f:
            return f.read().strip()
    return ""


def _esperar_gap():
    global _ultima_chamada
    agora = time.monotonic()
    falta = GAP_SEG - (agora - _ultima_chamada)
    if falta > 0:
        time.sleep(falta)
    _ultima_chamada = time.monotonic()


def _chat(modelo, system, user, usar_json=True):
    key = get_key()
    if not key:
        raise RuntimeError("Sem chave Groq (env GROQ_API_KEY ou groq_key.txt).")
    payload = {"model": modelo, "messages": [{"role": "system", "content": system},
                                             {"role": "user", "content": user}],
               "temperature": 0, "max_tokens": MAX_TOKENS}
    if usar_json:
        payload["response_format"] = {"type": "json_object"}
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json=payload,
        timeout=TIMEOUT,
    )
    if r.status_code == 429:
        raise RuntimeError("429 rate-limit")
    if r.status_code in (400, 404):
        raise RuntimeError(f"{r.status_code} modelo invalido/desligado")
    r.raise_for_status()
    conteudo = (r.json()["choices"][0]["message"].get("content") or "").strip()
    if not conteudo:
        raise RuntimeError("resposta vazia")
    return conteudo


def _chamar_com_rotacao(system, user, tentativas=6, usar_json=True):
    """Tenta modelos em rotacao; em 429 espera e troca de modelo."""
    erros = []
    for _ in range(tentativas):
        modelo = next(_cycle)
        try:
            _esperar_gap()
            return _chat(modelo, system, user, usar_json), modelo
        except Exception as e:
            erros.append(f"{modelo}: {e}")
            if "429" in str(e):
                time.sleep(10)
            continue
    raise RuntimeError("Todos os modelos falharam: " + " | ".join(erros[-3:]))


def _limpa(txt, limite):
    txt = re.sub(r"\s+", " ", (txt or "")).strip()
    return txt[:limite]


def gerar_perfil(cv_texto, forcar=False):
    """Condensa o CV em ~60 palavras UMA vez (cache em perfil_cv.txt)."""
    if os.path.exists(PERFIL_FILE) and not forcar:
        with open(PERFIL_FILE, encoding="utf-8") as f:
            return f.read().strip()
    system = ('Responda SOMENTE JSON {"resumo":"..."} com ate 60 palavras: cargo atual, '
              'anos de experiencia, skills tecnicas, senioridade, idiomas, cidade.')
    raw, _ = _chamar_com_rotacao(system, _limpa(cv_texto, 6000), usar_json=True)
    m = re.search(r"\{.*\}", raw, re.S)
    perfil = json.loads(m.group(0)).get("resumo", "") if m else raw
    perfil = _limpa(perfil, 1200)
    with open(PERFIL_FILE, "w", encoding="utf-8") as f:
        f.write(perfil)
    return perfil


def analisar(titulo, empresa, local, descricao, cv_texto):
    """Retorna dict {score, tem[], falta[], motivo}. Tokens minimos."""
    perfil = gerar_perfil(cv_texto)
    system = ('Voce avalia aderencia candidato-vaga. Responda SOMENTE JSON: '
              '{"score":0-100,"tem":["skill",...max 4],"falta":["skill",...max 4],'
              '"motivo":"frase curta em pt-BR"}. Sem markdown, sem explicacao extra.')
    user = (f"PERFIL: {_limpa(perfil, 800)}\n"
            f"VAGA: {_limpa(titulo, 150)} | {_limpa(empresa, 100)} | {_limpa(local, 80)}\n"
            f"DESC: {_limpa(descricao, 1200)}")
    raw, modelo = _chamar_com_rotacao(system, user)
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise RuntimeError("Resposta sem JSON: " + raw[:120])
    d = json.loads(m.group(0))
    return {"score": max(0, min(100, int(d.get("score", 0)))),
            "tem": list(d.get("tem", []))[:4],
            "falta": list(d.get("falta", []))[:4],
            "motivo": str(d.get("motivo", ""))[:220],
            "modelo": modelo}
