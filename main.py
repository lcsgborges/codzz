from typing import Optional
import os

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from supabase_config import get_token_and_phone_by_email, ErroApp   
from uazapi_config import get_status_and_paircode, get_uazapi_connect

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index_get(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "mensagem": None,
            "pair_code": None,
            "email": "",
        },
    )

@app.post("/", response_class=HTMLResponse)
async def index_post(request: Request, email: str = Form(default="")):
    mensagem: Optional[str] = None
    pair_code: Optional[str] = None

    email = (email or "").strip()

    if not email:
        mensagem = "Informe um email válido."
    else:
        try:
            token, phone = get_token_and_phone_by_email(email)

            payload = get_uazapi_connect(token, phone)
            conectado, paircode = get_status_and_paircode(payload)

            if conectado:
                mensagem = "Este WhatsApp já está conectado. Nenhuma ação é necessária."
            else:
                if not paircode:
                    raise ErroApp(
                        "Pair code não foi retornado pela UAZAPI (a instância ainda não gerou um código)."
                    )
                pair_code = paircode

        except ErroApp as exc:
            mensagem = str(exc)
        except Exception:
            # Evita vazar erro interno pra tela
            mensagem = "Erro interno. Tente novamente mais tarde."

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "mensagem": mensagem,
            "pair_code": pair_code,
            "email": email,
        },
    )

# uvicorn main:app --reload --host 0.0.0.0 --port 8000
