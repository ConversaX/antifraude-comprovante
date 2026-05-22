import cv2
import numpy as np
import imagehash
from PIL import Image


def gerar_hash_visual(image_pil: Image.Image) -> str:
    return str(imagehash.phash(image_pil))


def detectar_edicao_simples(image_path: str) -> bool:
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False
    edges = cv2.Canny(img, 100, 200)
    edge_density = np.sum(edges > 0) / edges.size
    return edge_density > 0.15
