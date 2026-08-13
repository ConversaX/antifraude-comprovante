import os
import time
import hashlib
import json
from pathlib import Path

from redis import Redis
from rq import Worker, Queue, Connection

import database
import fraud_detector
import main

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


def process(payload: dict):
    """Worker entrypoint. payload is a dict with keys: image_path, endereco, meta
    This function mirrors the analysis pipeline used in the API and saves the result to DB.
    """
    image_path = payload.get("image_path")
    endereco = payload.get("endereco", "")

    if not image_path:
        return {"error": "no image_path provided"}

    path = Path(image_path)
    if not path.exists():
        return {"error": "image not found", "path": image_path}

    try:
        content = path.read_bytes()
        hash_md5 = hashlib.md5(content).hexdigest()

        if database.imagem_ja_existe(hash_md5):
            return {"status": "skipped", "reason": "duplicate"}

        img_pil = main.Image.open(path)
        hash_visual = fraud_detector.gerar_hash_visual(img_pil)

        # check visual duplicates
        similar = database.buscar_hash_visual_similar(hash_visual, threshold=int(os.getenv("PHASH_THRESHOLD", "10")))
        if similar:
            database.salvar_analise(
                hash_imagem=hash_md5,
                hash_visual=hash_visual,
                endereco=endereco,
                score_risco=100,
                veredito="Suspeito",
                distancia_km=None,
                ocr_texto="",
            )
            return {"status": "done", "veredito": "Suspeito", "reason": "visual_duplicate"}

        # OCR
        try:
            ocr_reader = main.get_ocr_reader()
            resultados_ocr = ocr_reader.readtext(str(path))
            ocr_texto = " ".join([r[1] for r in resultados_ocr])
        except Exception:
            ocr_texto = ""

        gps_coords = main.extrair_gps_exif(str(path))
        distancia_km = None
        if gps_coords:
            coords_end = main.geocodificar_endereco(endereco)
            if coords_end:
                try:
                    from geopy.distance import geodesic

                    distancia_km = round(geodesic(gps_coords, coords_end).km, 2)
                except Exception:
                    distancia_km = None

        resultado = main.chamar_ia(str(path), ocr_texto, endereco)
        score = int(resultado.get("score_risco", 50))
        motivos = list(resultado.get("motivos", []))

        if fraud_detector.detectar_edicao_simples(str(path)):
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

        return {"status": "done", "score": score, "veredito": veredito}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Start an RQ worker connected to REDIS_URL and listen on default queue
    redis_conn = Redis.from_url(REDIS_URL)
    with Connection(redis_conn):
        q = Queue()
        worker = Worker([q], connection=redis_conn)
        worker.work()
