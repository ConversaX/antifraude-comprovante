from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from pathlib import Path
import hashlib

from worker.tasks import enqueue_analysis
from utils_safety import gerar_nome_seguro
import database

app = FastAPI(title="Anti-Fraude API (worker mode)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_KEY", "")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "20"))
RATE_PERIOD = int(os.getenv("RATE_PERIOD", "60"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

_rate_store = {}


def verify_api_key(x_api_key: str | None = None):
    if API_KEY:
        if not x_api_key or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


def rate_limit(request: Request, x_api_key: str | None = None):
    key = x_api_key or request.client.host
    now = time.time()
    window = _rate_store.get(key, [])
    window = [t for t in window if t > now - RATE_PERIOD]
    if len(window) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests")
    window.append(now)
    _rate_store[key] = window


@app.post("/analisar_async")
async def analisar_async(
    file: UploadFile = File(...),
    endereco: str = Form(...),
    x_api_key: str | None = Depends(verify_api_key),
    _rl=Depends(rate_limit),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo inválido")

    filename_safe = gerar_nome_seguro(file.filename)
    ext = filename_safe.split('.')[-1].lower()
    allowed = {"jpg", "jpeg", "png", "webp", "gif"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Extensão não permitida")

    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo muito grande")

    temp_path = UPLOAD_DIR / filename_safe
    try:
        temp_path.write_bytes(content)
        # Enqueue the analysis job
        enqueue_analysis(str(temp_path), endereco, {})
        return {"enqueued": True, "path": str(temp_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historico")
def historico():
    return database.buscar_historico()


@app.get("/health")
def health():
    return {"status": "ok"}
