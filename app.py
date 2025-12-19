# app.py
import os
from typing import Optional, Tuple, Any, Dict

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request
from supabase import Client, create_client

load_dotenv()

app = Flask(__name__)

# =========================
# CONFIGURAÇÕES SUPABASE
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    or os.getenv("SUPABASE_ANON_KEY", "")
).strip().strip('"').strip("'")

# TABELA E CAMPOS
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "configs")
SUPABASE_EMAIL_FIELD = os.getenv("SUPABASE_EMAIL_FIELD", "client_email")

# NOMES REAIS NA TABELA
SUPABASE_TOKEN_COL = "token_uazapi"
SUPABASE_PHONE_COL = "agent_phone"

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL não configurado")
if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY ou SUPABASE_ANON_KEY não configurado")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# CONFIGURAÇÕES UAZAPI
# =========================
UAZAPI_CONNECT_URL = os.getenv(
    "UAZAPI_CONNECT_URL",
    "https://bornmakeai.uazapi.com/instance/connect",
).rstrip("/")


class ErroApp(Exception):
    pass


def buscar_token_e_phone_por_email(email: str) -> Tuple[str, str]:
    """
    Busca pelo email (ex: client_email) e retorna:
    - token_uazapi
    - agent_phone
    """
    email = email.strip()

    try:
        res = (
            supabase.table(SUPABASE_TABLE)
            .select(f"{SUPABASE_TOKEN_COL},{SUPABASE_PHONE_COL}")
            .eq(SUPABASE_EMAIL_FIELD, email)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise ErroApp(f"Falha ao consultar Supabase: {exc}") from exc

    dados = res.data or []
    if not dados:
        raise ErroApp("Email não encontrado no sistema")

    linha = dados[0]
    token = (linha.get(SUPABASE_TOKEN_COL) or "").strip()
    phone = (linha.get(SUPABASE_PHONE_COL) or "").strip()

    if not token:
        raise ErroApp("Token da UAZAPI não encontrado para este email")
    if not phone:
        raise ErroApp("Número (agent_phone) não encontrado para este email")

    return token, phone


def chamar_uazapi_connect(token: str, phone: str) -> Dict[str, Any]:
    """
    POST /instance/connect com header:
    token: <token_uazapi>

    E body JSON com o número vindo do banco.
    Ajuste a chave do payload se sua UAZAPI exigir outro nome.
    """
    headers = {
        "Accept": "application/json",
        "token": token,
        "Content-Type": "application/json",
    }

    payload = {
        "phone": phone  # se a UAZAPI usar outro campo, troque aqui (ex: "number", "agent_phone", etc.)
    }

    try:
        resp = requests.post(
            UAZAPI_CONNECT_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ErroApp(f"Erro de rede ao chamar UAZAPI: {exc}") from exc

    if resp.status_code >= 400:
        raise ErroApp(f"Erro na UAZAPI ({resp.status_code}): {resp.text}")

    try:
        return resp.json()
    except ValueError as exc:
        raise ErroApp("Resposta da UAZAPI não é JSON") from exc


def extrair_status_e_paircode(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Interpreta o retorno da UAZAPI com segurança.

    - Se estiver conectado (connected=true em qualquer lugar relevante),
      retorna (True, None).
    - Se não estiver conectado, tenta extrair paircode de vários lugares.
    """
    conectado = False

    # 1) top-level
    if bool(payload.get("connected", False)):
        conectado = True

    # 2) status.connected
    status = payload.get("status")
    if isinstance(status, dict) and bool(status.get("connected", False)):
        conectado = True

    # 3) instance.status == "connected"
    instance = payload.get("instance")
    if isinstance(instance, dict):
        inst_status = instance.get("status")
        if isinstance(inst_status, str) and inst_status.lower() == "connected":
            conectado = True

    # se conectado, paircode normalmente vem vazio mesmo
    if conectado:
        return True, None

    def pegar_str(d: Dict[str, Any], chave: str) -> Optional[str]:
        val = d.get(chave)
        if isinstance(val, str):
            val = val.strip()
            return val if val else None
        return None

    # tenta achar paircode no instance primeiro
    if isinstance(instance, dict):
        for chave in ("paircode", "pair_code", "pairCode"):
            pc = pegar_str(instance, chave)
            if pc:
                return False, pc

    # tenta achar paircode no topo
    for chave in ("paircode", "pair_code", "pairCode"):
        pc = pegar_str(payload, chave)
        if pc:
            return False, pc

    return False, None


@app.route("/", methods=["GET", "POST"])
def index():
    mensagem: Optional[str] = None
    pair_code: Optional[str] = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()

        if not email:
            mensagem = "Informe um email válido."
        else:
            try:
                token, _phone = buscar_token_e_phone_por_email(email)

                payload = chamar_uazapi_connect(token, _phone)
                conectado, paircode = extrair_status_e_paircode(payload)

                if conectado:
                    mensagem = "Este WhatsApp já está conectado. Nenhuma ação é necessária."
                else:
                    if not paircode:
                        raise ErroApp("Pair code não foi retornado pela UAZAPI (a instância ainda não gerou um código).")
                    pair_code = paircode

            except ErroApp as exc:
                mensagem = str(exc)

    return render_template("index.html", mensagem=mensagem, pair_code=pair_code)


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
