from __future__ import annotations

from pathlib import Path
import re

import cv2
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
ORIG_DIR = BASE_DIR / "dataset" / "originales"
RES_DIR = BASE_DIR / "resultados" / "imagenes_resultado"

OUT_ORIG_DIR = BASE_DIR / "dataset" / "originales_color"
OUT_RES_DIR = BASE_DIR / "resultados" / "imagenes_resultado_color"


# Colores en formato BGR para OpenCV.
PALETA = [
    (210, 235, 255),  # azul muy claro
    (220, 250, 220),  # verde muy claro
    (235, 225, 255),  # lila claro
    (200, 245, 245),  # cian claro
    (205, 225, 255),  # durazno claro
    (230, 240, 210),  # lima clara
    (245, 220, 220),  # rosa claro
    (215, 235, 235),  # gris azulado
    (225, 245, 255),  # celeste claro
    (210, 255, 240),  # menta clara
]


def recolorear_fondo(image: np.ndarray, color_bgr: tuple[int, int, int], threshold: int = 245) -> np.ndarray:
    out = image.copy()
    fondo_mask = np.all(image >= threshold, axis=2)
    out[fondo_mask] = color_bgr
    return out


def generar_variantes() -> None:
    OUT_ORIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_RES_DIR.mkdir(parents=True, exist_ok=True)

    patron_original = re.compile(r"^pieza_\d{2}\.png$")
    patron_resultado = re.compile(r"^resultado_pieza_\d{2}\.png$")

    originales = sorted(p for p in ORIG_DIR.glob("*.png") if patron_original.match(p.name))
    resultados = sorted(p for p in RES_DIR.glob("*.png") if patron_resultado.match(p.name))

    if len(originales) != 20:
        raise ValueError(f"Se esperaban 20 imagenes originales y se encontraron {len(originales)}")
    if len(resultados) != 20:
        raise ValueError(f"Se esperaban 20 imagenes de resultado y se encontraron {len(resultados)}")

    for i, img_path in enumerate(originales):
        color = PALETA[i % len(PALETA)]
        image = cv2.imread(str(img_path))
        if image is None:
            raise FileNotFoundError(f"No se pudo cargar {img_path}")

        variante = recolorear_fondo(image, color)
        out_path = OUT_ORIG_DIR / img_path.name
        cv2.imwrite(str(out_path), variante)
        print(f"Original color generada: {out_path.name}")

    for i, img_path in enumerate(resultados):
        color = PALETA[i % len(PALETA)]
        image = cv2.imread(str(img_path))
        if image is None:
            raise FileNotFoundError(f"No se pudo cargar {img_path}")

        variante = recolorear_fondo(image, color)
        out_path = OUT_RES_DIR / img_path.name
        cv2.imwrite(str(out_path), variante)
        print(f"Resultado color generado: {out_path.name}")

    print("")
    print(f"Originales nuevas guardadas en: {OUT_ORIG_DIR}")
    print(f"Resultados nuevos guardados en: {OUT_RES_DIR}")
    print("Las carpetas originales permanecen intactas.")


if __name__ == "__main__":
    generar_variantes()
