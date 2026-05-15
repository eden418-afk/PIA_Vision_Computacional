from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from generar_pasos_procesamiento import procesar_pieza


BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "resultados" / "pasos_procesamiento" / "pieza_03"
OUT_DIR = BASE_DIR / "resultados" / "pasos_procesamiento_color" / "pieza_03"

FONDO_COLOR = np.array([220, 235, 205], dtype=np.uint8)  # BGR, verde suave


def detectar_valor_fondo(gray: np.ndarray) -> int:
    esquinas = np.array([
        gray[0:20, 0:20].mean(),
        gray[0:20, -20:].mean(),
        gray[-20:, 0:20].mean(),
        gray[-20:, -20:].mean(),
    ])
    return int(round(float(esquinas.mean())))


def recolorear_solo_fondo(image: np.ndarray, tolerancia: int = 12) -> np.ndarray:
    if len(image.shape) == 2:
        gray = image
        out = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        out = image.copy()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    valor_fondo = detectar_valor_fondo(gray)
    mask = np.abs(gray.astype(np.int16) - valor_fondo) <= tolerancia
    out[mask] = FONDO_COLOR
    return out


def generar_pasos_color_pieza_03() -> None:
    if not SRC_DIR.exists():
        procesar_pieza(3)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in sorted(SRC_DIR.glob("*.png")):
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise FileNotFoundError(f"No se pudo cargar {path}")

        etapas_sin_recolor = {
            "02_escala_grises.png",
            "03_binarizacion_inversa.png",
            "04_limpieza_morfologica.png",
            "05_bordes_canny.png",
            "06_deteccion_contornos.png",
            "07_calculo_momentos.png",
        }

        out = img if path.name in etapas_sin_recolor else recolorear_solo_fondo(img)
        cv2.imwrite(str(OUT_DIR / path.name), out)
        print(f"Generada: {path.name}")

    print("")
    print(f"Pasos con solo fondo a color generados en: {OUT_DIR}")


if __name__ == "__main__":
    generar_pasos_color_pieza_03()
