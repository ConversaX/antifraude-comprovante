import uuid
from typing import Optional
from pydantic import BaseModel, conint, ValidationError


class IAResponse(BaseModel):
    score_risco: conint(ge=0, le=100)
    veredito: str
    motivos: Optional[list[str]] = []


# Example usage: validate parsed JSON

def validar_resposta_ia(raw: dict) -> IAResponse:
    try:
        return IAResponse(**raw)
    except ValidationError as e:
        # fallback: produce a safe, indeterminate response
        return IAResponse(score_risco=50, veredito="Indeterminado", motivos=["Resposta da IA inválida"])


# Safe filename generator

def gerar_nome_seguro(filename: str) -> str:
    ext = filename.split('.')[-1].lower()
    allowed = {"jpg", "jpeg", "png", "webp", "gif"}
    if ext not in allowed:
        ext = "jpg"
    return f"{uuid.uuid4().hex}.{ext}
"
