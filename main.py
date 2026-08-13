import os
import hashlib
import json
import re
import base64
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import easyocr
import urllib.parse
import urllib.request
from geopy.distance import geodesic

import database
import fraud_detector
from utils_safety import validar_resposta_ia, gerar_nome_seguro

load_dotenv()

# Config
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
API_KEY = os.getenv("API_KEY", "")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "20"))  # requests
RATE_PERIOD = int(os.getenv("RATE_PERIOD", "60"))  # seconds
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
PHASH_THRESHOLD = int(os.getenv("PHASH_THRESHOLD", "10"))

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

_ocr_reader = None

# Simple in-memory rate limiter: {api_key: [timestamps...]}
_rate_store = {}


def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(["pt", "en"], gpu=False)
    return _ocr_reader


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.criar_tabelas()
    yield


app = FastAPI(title="Anti-Fraude de Comprovantes", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if API_KEY:
        if not x_api_key or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


async def rate_limit(request: Request, x_api_key: Optional[str] = Depends(verify_api_key)):
    key = x_api_key or request.client.host
    now = time.time()
    window = _rate_store.get(key, [])
    # remove old
    window = [t for t in window if t > now - RATE_PERIOD]
    if len(window) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests")
    window.append(now)
    _rate_store[key] = window


def _rational_to_float(val):
    if isinstance(val, tuple) and len(val) == 2:
        return val[0] / val[1] if val[1] != 0 else 0.0
    return float(val)


def extrair_gps_exif(image_path: str):
    try:
        img = Image.open(image_path)
        exif_raw = img._getexif()
        if not exif_raw:
            return None

        gps_info = {}
        for tag_id, value in exif_raw.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == "GPSInfo":
                for gps_tag_id, gps_value in value.items():
                    gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag_name] = gps_value

        if not gps_info:
            return None

        lat_dms = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef")
        lon_dms = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef")

        if not all([lat_dms, lat_ref, lon_dms, lon_ref]):
            return None

        def dms_to_decimal(dms, ref):
            d = _rational_to_float(dms[0])
            m = _rational_to_float(dms[1])
            s = _rational_to_float(dms[2])
            dec = d + m / 60 + s / 3600
            return -dec if ref in ("S", "W") else dec

        return (dms_to_decimal(lat_dms, lat_ref), dms_to_decimal(lon_dms, lon_ref))
    except Exception:
        return None


def geocodificar_endereco(endereco: str, retries: int = 2, timeout: int = 10):
    if not GOOGLE_MAPS_API_KEY:
        return None
    for attempt in range(retries + 1):
        try:
            params = urllib.parse.urlencode({
                "address": endereco,
                "key": GOOGLE_MAPS_API_KEY,
                "language": "pt-BR",
                "region": "BR",
            })
            url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            if data.get("status") == "OK" and data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                return (loc["lat"], loc["lng"])
            return None
        except Exception:
            if attempt < retries:
                time.sleep(1 + attempt * 2)
                continue
            return None


def chamar_ia(image_path: str, ocr_texto: str, endereco: str, retries: int = 1, timeout: int = 30) -> dict:
    if not ANTHROPIC_API_KEY:
        return {
            "score_risco": 50,
            "veredito": "Indeterminado",
            "motivos": ["Anthropic API key não configurada"],
        }
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    ext = Path(image_path).suffix.lower().lstrip(".")
    media_type = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "webp": "image/webp", "gif": "image/gif",
    }.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        img_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    prompt = f"""Você é um especialista em detecção de fraudes em comprovantes de entrega logística.

Analise a imagem e retorne APENAS um JSON válido, sem markdown, sem texto adicional.

Contexto:
- Endereço de entrega informado: {endereco}
- Texto extraído por OCR: {ocr_texto[:500] if ocr_texto else "Não disponível"}

Retorne SOMENTE este JSON:
{{
    "score_risco": <inteiro 0-100>,
    "veredito": "<Aprovado ou Suspeito>",
    "motivos": ["<motivo 1>", "<motivo 2>"]
}}"""

    for attempt in range(retries + 1):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                        {"type": "text", "text": prompt},
                    ],
                }],
            )
            text = response.content[0].text.strip()
            # sanitize model output: strip markdown fences and non-json
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*", "", text)
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                raise ValueError("Resposta da IA sem JSON detectável")
            payload = m.group(0)
            parsed = json.loads(payload)
            validated = validar_resposta_ia(parsed)
            return validated.dict()
        except Exception as e:
            if attempt < retries:
                time.sleep(1 + attempt * 2)
                continue
            return {
                "score_risco": 50,
                "veredito": "Indeterminado",
                "motivos": [f"Erro na análise da IA: {str(e)}"],
            }


@app.post("/analisar")
async def analisar(
    file: UploadFile = File(...),
    endereco: str = Form(...),
    horario_limite: str = Form(default=""),
    request: Request = None,
    x_api_key: Optional[str] = Depends(verify_api_key),
    _rl=Depends(rate_limit),
):
    # basic validations
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

        hash_md5 = hashlib.md5(content).hexdigest()

        if database.imagem_ja_existe(hash_md5):
            return {
                "score_risco": 100,
                "veredito": "Suspeito",
                "motivos": ["Imagem duplicada — já analisada anteriormente no sistema"],
                "distancia_km": None,
                "ocr": "N/A",
                "hash_imagem": hash_md5,
                "hash_visual": None,
            }

        img_pil = Image.open(temp_path)
        hash_visual = fraud_detector.gerar_hash_visual(img_pil)

        # check visual duplicates
        similar = database.buscar_hash_visual_similar(hash_visual, threshold=PHASH_THRESHOLD)
        if similar:
            # treat as suspicious
            database.salvar_analise(
                hash_imagem=hash_md5,
                hash_visual=hash_visual,
                endereco=endereco,
                score_risco=100,
                veredito="Suspeito",
                distancia_km=None,
                ocr_texto="",
            )
            return {
                "score_risco": 100,
                "veredito": "Suspeito",
                "motivos": ["Imagem visualmente semelhante a outra já analisada"],
                "distancia_km": None,
                "ocr": "N/A",
                "hash_imagem": hash_md5,
                "hash_visual": hash_visual,
            }

        try:
            ocr_reader = get_ocr_reader()
            resultados_ocr = ocr_reader.readtext(str(temp_path))
            ocr_texto = " ".join([r[1] for r in resultados_ocr])
        except Exception:
            ocr_texto = ""

        gps_coords = extrair_gps_exif(str(temp_path))
        distancia_km = None
        if gps_coords:
            coords_end = geocodificar_endereco(endereco)
            if coords_end:
                distancia_km = round(geodesic(gps_coords, coords_end).km, 2)

        resultado = chamar_ia(str(temp_path), ocr_texto, endereco)
        score = int(resultado.get("score_risco", 50))
        motivos = list(resultado.get("motivos", []))

        if fraud_detector.detectar_edicao_simples(str(temp_path)):
            score += 25
            motivos.append("Possível edição detectada por análise de bordas (OpenCV Canny)")

        if distancia_km is not None and distancia_km > 2:
            score += 40
            motivos.append(f"Localização GPS suspeita: {distancia_km} km do endereço informado")

        score = min(score, 100)
        veredito = "Suspeito" if score > 70 else "Aprovado"

        database.salvar_analise(
            hash_imagem=hash_md5,
            hash_visual=hash_visual,
            endereco=endereco,
            score_risco=score,
            veredito=veredito,
            distancia_km=distancia_km,
            ocr_texto=ocr_texto,
        )

        return {
            "score_risco": score,
            "veredito": veredito,
            "motivos": motivos,
            "distancia_km": distancia_km,
            "ocr": ocr_texto,
            "hash_imagem": hash_md5,
            "hash_visual": hash_visual,
        }
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


@app.get("/historico")
def historico(x_api_key: Optional[str] = Depends(verify_api_key)):
    return database.buscar_historico()


@app.get("/health")
def health():
    return {"status": "ok"}
