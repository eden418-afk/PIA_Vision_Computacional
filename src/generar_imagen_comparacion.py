from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import cv2
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
CAD_MODELOS_DIR = BASE_DIR / "cad" / "modelos"
RESULTADOS_PYTHON_DIR = BASE_DIR / "resultados" / "imagenes_resultado"
SALIDA_DIR = BASE_DIR / "resultados" / "comparaciones"
TMP_DIR = BASE_DIR / "tmp" / "comparaciones"


def extraer_thumbnail_freecad(fcstd_path: Path, output_path: Path) -> Path:
    with zipfile.ZipFile(fcstd_path, "r") as zf:
        data = zf.read("thumbnails/Thumbnail.png")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return output_path


def cargar_imagen(path: Path) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {path}")
    return image


def redimensionar_a_altura(image: np.ndarray, target_height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = target_height / h
    target_width = max(1, int(round(w * scale)))
    return cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)


def crear_lienzo_comparacion(
    cad_image: np.ndarray,
    python_image: np.ndarray,
    pieza_id: str,
) -> np.ndarray:
    target_height = 620
    cad_resized = redimensionar_a_altura(cad_image, target_height)
    python_resized = redimensionar_a_altura(python_image, target_height)

    margin = 40
    header_height = 110
    footer_height = 50
    gap = 40

    canvas_height = header_height + target_height + footer_height
    canvas_width = (
        margin
        + cad_resized.shape[1]
        + gap
        + python_resized.shape[1]
        + margin
    )

    canvas = np.full((canvas_height, canvas_width, 3), 255, dtype=np.uint8)

    x_cad = margin
    x_python = margin + cad_resized.shape[1] + gap
    y_images = header_height

    canvas[y_images:y_images + target_height, x_cad:x_cad + cad_resized.shape[1]] = cad_resized
    canvas[y_images:y_images + target_height, x_python:x_python + python_resized.shape[1]] = python_resized

    cv2.putText(
        canvas,
        f"Comparacion CAD vs Python - {pieza_id}",
        (margin, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.05,
        (20, 20, 20),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        canvas,
        "FreeCAD: pieza CAD con centroide y eje angular",
        (x_cad, 82),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 0, 0),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        canvas,
        "Python/OpenCV: resultado procesado",
        (x_python, 82),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 0, 0),
        2,
        cv2.LINE_AA,
    )

    cv2.rectangle(
        canvas,
        (x_cad - 2, y_images - 2),
        (x_cad + cad_resized.shape[1] + 2, y_images + target_height + 2),
        (90, 90, 90),
        2,
    )
    cv2.rectangle(
        canvas,
        (x_python - 2, y_images - 2),
        (x_python + python_resized.shape[1] + 2, y_images + target_height + 2),
        (90, 90, 90),
        2,
    )

    cv2.putText(
        canvas,
        "Fuente CAD: miniatura embebida en .FCStd | Fuente Python: resultados/imagenes_resultado",
        (margin, canvas_height - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.53,
        (80, 80, 80),
        1,
        cv2.LINE_AA,
    )

    return canvas


def generar_imagen_comparacion(pieza_num: int) -> Path:
    pieza_id = f"pieza_{pieza_num:02d}"
    fcstd_path = CAD_MODELOS_DIR / f"{pieza_id}.FCStd"
    resultado_python_path = RESULTADOS_PYTHON_DIR / f"resultado_{pieza_id}.png"

    if not fcstd_path.exists():
        raise FileNotFoundError(f"No existe el archivo CAD: {fcstd_path}")
    if not resultado_python_path.exists():
        raise FileNotFoundError(f"No existe la imagen de Python: {resultado_python_path}")

    thumbnail_path = TMP_DIR / f"{pieza_id}_thumbnail.png"
    extraer_thumbnail_freecad(fcstd_path, thumbnail_path)

    cad_image = cargar_imagen(thumbnail_path)
    python_image = cargar_imagen(resultado_python_path)

    comparacion = crear_lienzo_comparacion(cad_image, python_image, pieza_id)

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SALIDA_DIR / f"comparacion_{pieza_id}_cad_vs_python.png"
    cv2.imwrite(str(output_path), comparacion)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera una imagen de comparacion entre FreeCAD y Python/OpenCV."
    )
    parser.add_argument(
        "--pieza",
        type=int,
        default=5,
        help="Numero de pieza a comparar, por ejemplo 5 para pieza_05.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = generar_imagen_comparacion(args.pieza)
    print(f"Imagen de comparacion generada: {output_path}")


if __name__ == "__main__":
    main()
