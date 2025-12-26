from supabase import create_client, Client
from settings import (
    SUPABASE_URL, 
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_TABLE,
    SUPABASE_PHONE_FIELD,
    SUPABASE_EMAIL_FIELD,
    SUPABASE_TOKEN_FIELD
)


supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class ErroApp(Exception):
    pass

def get_token_and_phone_by_email(email: str):

    email = email.strip()

    try:
        response = supabase.table(SUPABASE_TABLE).select(f"{SUPABASE_TOKEN_FIELD},{SUPABASE_PHONE_FIELD}").eq(SUPABASE_EMAIL_FIELD, email).limit(1).execute()
    except:
        raise ErroApp(f'Falha ao consultar banco de dados')

    data = response.data or []
    if not data:
        raise ErroApp("Email não encontrado no sistema")
    
    token = (data[0].get(SUPABASE_TOKEN_FIELD) or "").strip()
    phone = (data[0].get(SUPABASE_PHONE_FIELD) or "").strip()

    if not token:
        raise ErroApp("Token não encontrado para este email")
    if not phone:
        raise ErroApp("Número não encontrado para este email")

    return token, phone