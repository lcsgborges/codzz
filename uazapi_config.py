import requests

from settings import UAZAPI_CONNECT_URL
from supabase_config import ErroApp

def get_uazapi_connect(token: str, phone: str):
    headers = {
        "Accept": "application/json",
        "token": token,
        "Content-Type": "application/json",
    }

    payload = {
        "phone": phone
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
    

def get_status_and_paircode(payload):
    connected = False

    if bool(payload.get("connected", False)):
        connected = True

    # 2) status.connected
    status = payload.get("status")
    if isinstance(status, dict) and bool(status.get("connected", False)):
        connected = True

    # 3) instance.status == "connected"
    instance = payload.get("instance")
    if isinstance(instance, dict):
        inst_status = instance.get("status")
        if isinstance(inst_status, str) and inst_status.lower() == "connected":
            connected = True

    # se conectado, paircode normalmente vem vazio mesmo
    if connected:
        return True, None

    def pegar_str(d, chave: str):
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