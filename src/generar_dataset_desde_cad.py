import json
import math
from pathlib import Path

import cv2
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent

CAD_GEOMETRY_PATH = BASE_DIR / "resultados" / "cad_geometry.json"
DATASET_DIR = BASE_DIR / "dataset" / "originales"

IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720

TABLE_WIDTH_MM = 320
TABLE_HEIGHT_MM = 180

BACKGROUND_COLOR = (255, 255, 255)
OBJECT_COLOR = (35, 35, 35)

PX_PER_MM_X = IMAGE_WIDTH / TABLE_WIDTH_MM
PX_PER_MM_Y = IMAGE_HEIGHT / TABLE_HEIGHT_MM


def rotate_point(x, y, angle_deg):
    angle_rad = math.radians(angle_deg)

    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    xr = x * cos_a - y * sin_a
    yr = x * sin_a + y * cos_a

    return xr, yr


def cad_mm_to_pixel(x_mm, y_mm):
    """
    Convierte coordenadas CAD en mm a coordenadas de imagen en px.

    Origen CAD:
    - Centro de la mesa

    Origen imagen:
    - Esquina superior izquierda

    Eje X:
    - Positivo hacia la derecha

    Eje Y CAD:
    - Positivo hacia arriba

    Eje Y imagen:
    - Positivo hacia abajo
    """
    px = IMAGE_WIDTH / 2 + x_mm * PX_PER_MM_X
    py = IMAGE_HEIGHT / 2 - y_mm * PX_PER_MM_Y

    return int(round(px)), int(round(py))


def transform_point(point, angle_deg, tx_mm, ty_mm):
    """
    Aplica la misma transformación usada en FreeCAD:
    rotación alrededor de Z y luego traslación.
    """
    x, y = point

    xr, yr = rotate_point(x, y, angle_deg)

    return xr + tx_mm, yr + ty_mm


def draw_piece(image, spec):
    angle_deg = spec["angle_deg"]
    tx_mm = spec["tx_mm"]
    ty_mm = spec["ty_mm"]

    # Dibujar perfil exterior
    transformed_points = [
        transform_point(point, angle_deg, tx_mm, ty_mm)
        for point in spec["points"]
    ]

    polygon_px = np.array(
        [cad_mm_to_pixel(x, y) for x, y in transformed_points],
        dtype=np.int32
    )

    cv2.fillPoly(image, [polygon_px], OBJECT_COLOR)

    # Dibujar agujeros como zonas blancas
    for hole in spec.get("holes", []):
        hx, hy, radius_mm = hole

        hx_t, hy_t = transform_point((hx, hy), angle_deg, tx_mm, ty_mm)
        center_px = cad_mm_to_pixel(hx_t, hy_t)

        radius_px = int(round(radius_mm * PX_PER_MM_X))

        cv2.circle(image, center_px, radius_px, BACKGROUND_COLOR, -1)


def generar_dataset_desde_cad():
    if not CAD_GEOMETRY_PATH.exists():
        raise FileNotFoundError(f"No existe: {CAD_GEOMETRY_PATH}")

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    with open(CAD_GEOMETRY_PATH, "r", encoding="utf-8") as file:
        specs = json.load(file)

    for index, spec in enumerate(specs, start=1):
        image = np.full(
            (IMAGE_HEIGHT, IMAGE_WIDTH, 3),
            BACKGROUND_COLOR,
            dtype=np.uint8
        )

        draw_piece(image, spec)

        filename = f"pieza_{index:02d}.png"
        image_path = DATASET_DIR / filename

        cv2.imwrite(str(image_path), image)

        print(
            f"Imagen generada: {filename} | "
            f"Figura: {spec['name']} | "
            f"Ángulo CAD: {spec['angle_deg']}°"
        )

    print("")
    print("Dataset CAD limpio generado correctamente.")
    print(f"Imágenes guardadas en: {DATASET_DIR}")


if __name__ == "__main__":
    generar_dataset_desde_cad()