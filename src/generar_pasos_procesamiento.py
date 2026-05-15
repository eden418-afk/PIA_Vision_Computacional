from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from vision import (
    clasificar_figura_geometrica,
    extraer_propiedades_geometricas,
    normalizar_angulo,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset" / "originales"
OUTPUT_BASE_DIR = BASE_DIR / "resultados" / "pasos_procesamiento"


def guardar(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


def texto_multilinea(
    image: np.ndarray,
    lineas: list[str],
    x: int = 25,
    y: int = 40,
    dy: int = 34,
) -> np.ndarray:
    out = image.copy()
    for i, linea in enumerate(lineas):
        cv2.putText(
            out,
            linea,
            (x, y + i * dy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
    return out


def procesar_pieza(pieza_num: int) -> Path:
    pieza_id = f"pieza_{pieza_num:02d}"
    image_path = DATASET_DIR / f"{pieza_id}.png"
    output_dir = OUTPUT_BASE_DIR / pieza_id

    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")

    # 5.7.1 Imagen RGB
    guardar(output_dir / "01_imagen_rgb.png", img)

    # 5.7.2 Escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    guardar(output_dir / "02_escala_grises.png", gray)

    # 5.7.3 Binarizacion inversa
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    guardar(output_dir / "03_binarizacion_inversa.png", binary)

    # 5.7.4 Limpieza morfologica
    kernel = np.ones((3, 3), np.uint8)
    binary_clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    guardar(output_dir / "04_limpieza_morfologica.png", binary_clean)

    # 5.7.5 Canny
    edges = cv2.Canny(binary_clean, 50, 150)
    guardar(output_dir / "05_bordes_canny.png", edges)

    # 5.7.6 Contornos
    contours, _ = cv2.findContours(binary_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError(f"No se encontraron contornos para {pieza_id}")
    main_contour = max(contours, key=cv2.contourArea)

    contornos_img = img.copy()
    cv2.drawContours(contornos_img, [main_contour], -1, (0, 255, 0), 3)
    guardar(output_dir / "06_deteccion_contornos.png", contornos_img)

    # 5.7.7 Momentos
    M = cv2.moments(binary_clean, binaryImage=True)
    if M["m00"] == 0:
        raise ValueError(f"La mascara no tiene area valida para {pieza_id}")

    area_px = cv2.countNonZero(binary_clean)
    moments_img = cv2.cvtColor(binary_clean, cv2.COLOR_GRAY2BGR)
    moments_img = texto_multilinea(
        moments_img,
        [
            "Momentos de imagen",
            f"M00 = {M['m00']:.2f}",
            f"M10 = {M['m10']:.2f}",
            f"M01 = {M['m01']:.2f}",
            f"Area = {area_px:.2f} px2",
        ],
    )
    guardar(output_dir / "07_calculo_momentos.png", moments_img)

    # 5.7.8 Centroide
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    centroide_img = contornos_img.copy()
    cv2.circle(centroide_img, (cx, cy), 8, (0, 0, 255), -1)
    cv2.putText(
        centroide_img,
        f"Centroide ({cx}, {cy})",
        (cx + 12, cy - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )
    guardar(output_dir / "08_calculo_centroide.png", centroide_img)

    # 5.7.9 Orientacion
    mu20 = M["mu20"] / M["m00"]
    mu02 = M["mu02"] / M["m00"]
    mu11 = M["mu11"] / M["m00"]
    angle_rad = 0.5 * np.arctan2(2 * mu11, mu20 - mu02)
    angle_deg = normalizar_angulo(float(np.degrees(angle_rad)))

    orientacion_img = centroide_img.copy()
    length = 150
    x2 = int(cx + length * np.cos(np.deg2rad(angle_deg)))
    y2 = int(cy + length * np.sin(np.deg2rad(angle_deg)))
    x1 = int(cx - length * np.cos(np.deg2rad(angle_deg)))
    y1 = int(cy - length * np.sin(np.deg2rad(angle_deg)))
    cv2.line(orientacion_img, (x1, y1), (x2, y2), (255, 0, 0), 3)
    cv2.putText(
        orientacion_img,
        f"Angulo = {angle_deg:.2f} deg",
        (25, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 0, 0),
        2,
        cv2.LINE_AA,
    )
    guardar(output_dir / "09_calculo_orientacion.png", orientacion_img)

    # 5.7.10 Propiedades geometricas
    propiedades = extraer_propiedades_geometricas(main_contour, binary_clean)
    propiedades_img = img.copy()
    propiedades_img = texto_multilinea(
        propiedades_img,
        [
            "Propiedades geometricas",
            f"Perimetro = {propiedades['perimetro_px']:.2f} px",
            f"Circularidad = {propiedades['circularity']:.4f}",
            f"Aspect ratio = {propiedades['aspect_ratio']:.4f}",
            f"Vertices = {propiedades['vertices_aprox']}",
            f"Agujeros = {propiedades['numero_agujeros']}",
        ],
    )
    guardar(output_dir / "10_propiedades_geometricas.png", propiedades_img)

    # 5.7.11 Clasificacion
    clase = clasificar_figura_geometrica(propiedades)
    clasificacion_img = propiedades_img.copy()
    cv2.putText(
        clasificacion_img,
        f"Clasificacion = {clase}",
        (25, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 0, 180),
        2,
        cv2.LINE_AA,
    )
    guardar(output_dir / "11_clasificacion_geometrica.png", clasificacion_img)

    # 5.7.12 Imagen anotada final
    final_img = orientacion_img.copy()
    x, y, w, h = cv2.boundingRect(main_contour)
    cv2.rectangle(final_img, (x, y), (x + w, y + h), (0, 180, 255), 2)
    final_img = texto_multilinea(
        final_img,
        [
            f"Area = {area_px:.1f} px2",
            f"Clase = {clase}",
            f"Agujeros = {propiedades['numero_agujeros']}",
            f"Vertices = {propiedades['vertices_aprox']}",
        ],
        x=25,
        y=85,
        dy=32,
    )
    guardar(output_dir / "12_imagen_anotada_final.png", final_img)

    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera una carpeta con imagenes de cada paso del procesamiento."
    )
    parser.add_argument(
        "--pieza",
        type=int,
        default=3,
        help="Numero de pieza a procesar. Ejemplo: 3 para pieza_03.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = procesar_pieza(args.pieza)
    print(f"Pasos de procesamiento generados en: {output_dir}")


if __name__ == "__main__":
    main()
