import os
import hashlib
import json
import re
import base64
from contextlib import asynccontextmanager
from pathlib import Path

import anthropic
from fastapi import FastAPI, File, UploadFile, Form
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

load_dotenv()

_claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

_ocr_reader = None


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


def geocodificar_endereco(endereco: str):
    if not GOOGLE_MAPS_API_KEY:
        return None
    try:
        params = urllib.parse.urlencode({
            "address": endereco,
            "key": GOOGLE_MAPS_API_KEY,
            "language": "pt-BR",
            "region": "BR",
        })
        url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
        return None
    except Exception:
        return None


def chamar_ia(image_path: str, ocr_texto: str, endereco: str) -> dict:
    try:
        ext = Path(image_path).suffix.lower().lstrip(".")
        media_type = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp", "gif": "image/gif",
        }.get(ext, "image/jpeg")

        with open(image_path, "rb") as f:
            img_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

        prompt = f"""Você é um especialista em detecção de fraudes em comprovantes de entrega logística, como os usados por Lalamove, 99, Uber Flash e transportadoras.

Analise a imagem e retorne APENAS um JSON válido, sem markdown, sem texto adicional.

Contexto:
- Endereço de entrega informado: {endereco}
- Texto extraído por OCR: {ocr_texto[:500] if ocr_texto else "Não disponível"}

=== CRITÉRIOS OBRIGATÓRIOS PARA APROVAÇÃO ===
A imagem DEVE conter pelo menos um destes elementos para ser considerada válida:
1. Pacote/caixa/encomenda VISÍVEL no local de entrega (porta, portão, calçada, recepção)
2. Pessoa recebendo ou assinando o comprovante
3. Documento físico de entrega com dados do destinatário
4. Screenshot de app de entrega mostrando status "entregue" com foto do local

=== MOTIVOS AUTOMÁTICOS DE REPROVAÇÃO (score >= 80) ===
Reprove com score alto se a imagem mostrar:
- Apenas o veículo do entregador (moto, carro, baú, compartimento de carga)
- Interior ou exterior do veículo sem evidência de entrega
- Foto genérica de rua sem local de entrega identificável
- Selfie do entregador sem o local/pacote
- Imagem fora de contexto logístico (paisagem, objeto aleatório)
- Imagem claramente reutilizada ou copiada da internet
- Manipulação digital evidente (textos sobrepostos, bordas irregulares, inconsistências de cor)

=== AVALIAÇÃO ===
Analise rigorosamente:
1. A foto prova que a entrega foi realizada no endereço informado?
2. O local visível é compatível com: {endereco}?
3. Há pacote/encomenda depositada ou sendo recebida?
4. A imagem parece autêntica (não editada, não reutilizada)?

Retorne SOMENTE este JSON:
{{
    "score_risco": <inteiro 0-100, onde 0=entrega confirmada sem dúvidas, 100=fraude certa>,
    "veredito": "<Aprovado ou Suspeito>",
    "motivos": ["<motivo específico 1>", "<motivo específico 2>", "<motivo específico 3>"]
}}"""

        response = _claude.messages.create(
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
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        return json.loads(text.strip())
    except Exception:
        return {
            "score_risco": 50,
            "veredito": "Indeterminado",
            "motivos": ["Erro na análise da IA"],
        }


@app.post("/analisar")
async def analisar(
    file: UploadFile = File(...),
    endereco: str = Form(...),
    horario_limite: str = Form(default=""),
):
    content = await file.read()
    temp_path = UPLOAD_DIR / f"temp_{file.filename}"
    temp_path.write_bytes(content)

    hash_md5 = hashlib.md5(content).hexdigest()

    if database.imagem_ja_existe(hash_md5):
        os.remove(temp_path)
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
        endereco=endereco,
        score_risco=score,
        veredito=veredito,
        distancia_km=distancia_km,
        ocr_texto=ocr_texto,
    )

    os.remove(temp_path)

    return {
        "score_risco": score,
        "veredito": veredito,
        "motivos": motivos,
        "distancia_km": distancia_km,
        "ocr": ocr_texto,
        "hash_imagem": hash_md5,
        "hash_visual": hash_visual,
    }


@app.get("/historico")
def historico():
    return database.buscar_historico()


@app.get("/health")
def health():
    return {"status": "ok"}
