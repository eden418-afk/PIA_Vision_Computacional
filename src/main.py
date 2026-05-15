from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def normalizar_angulo(angulo: float) -> float:
    while angulo > 90:
        angulo -= 180
    while angulo < -90:
        angulo += 180
    return angulo


def contar_agujeros(mask: np.ndarray, area_min: int = 30) -> int:
    contornos, jerarquia = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if jerarquia is None:
        return 0
    return sum(
        1
        for i, c in enumerate(contornos)
        if jerarquia[0][i][3] != -1 and cv2.contourArea(c) >= area_min
    )


def clasificar(prop: dict) -> str:
    v = prop["vertices_aprox"]
    h = prop["numero_agujeros"]
    ar = prop["aspect_ratio"]
    s = prop["solidity"]
    c = prop["circularity"]
    e = prop["extent"]

    if c > 0.80 and v > 10:
        return "circulo_o_brida_circular" if h >= 1 else "circulo"
    if v == 3:
        return "triangulo"
    if v == 4:
        return "placa_alargada" if ar > 2.0 or ar < 0.5 else "cuadrilatero_rombo_rectangulo"
    if v == 5:
        return "pentagono"
    if v == 6:
        return "hexagono"
    if 7 <= v <= 9:
        return "octagono_o_poligono_regular"
    if v >= 14 and s < 0.85:
        return "engrane_o_pieza_dentada_perforada" if h >= 1 else "pieza_dentada"
    if h >= 4:
        return "brida_o_placa_multiples_perforaciones"
    if h == 3:
        return "base_o_soporte_tres_perforaciones"
    if h == 2:
        if ar > 2.0:
            return "brazo_mecanico_o_placa_ranurada"
        if s < 0.80:
            return "soporte_muescado_o_irregular"
        return "pieza_dos_perforaciones"
    if h == 1:
        return "perfil_abierto_o_irregular" if s < 0.70 else "pieza_una_perforacion"
    if s < 0.70:
        return "perfil_irregular_o_abierto"
    if e < 0.55:
        return "pieza_con_geometria_compuesta"
    return "pieza_general"


def detectar_pieza(image_path: str | Path, output_path: str | Path | None = None, figura: str | None = None) -> dict:
    image_path = Path(image_path)
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    edges = cv2.Canny(mask, 50, 150)

    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        raise ValueError(f"No se encontraron contornos en {image_path.name}")

    contorno = max(contornos, key=cv2.contourArea)
    M = cv2.moments(mask, binaryImage=True)
    if M["m00"] == 0:
        raise ValueError(f"La mascara no tiene area valida en {image_path.name}")

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    mu20 = M["mu20"] / M["m00"]
    mu02 = M["mu02"] / M["m00"]
    mu11 = M["mu11"] / M["m00"]
    angulo = normalizar_angulo(float(np.degrees(0.5 * np.arctan2(2 * mu11, mu20 - mu02))))

    area = float(cv2.countNonZero(mask))
    perimetro = float(cv2.arcLength(contorno, True))
    x, y, w, h = cv2.boundingRect(contorno)
    hull = cv2.convexHull(contorno)
    hull_area = cv2.contourArea(hull)
    approx = cv2.approxPolyDP(contorno, 0.02 * perimetro, True)

    prop = {
        "perimetro_px": perimetro,
        "aspect_ratio": w / h if h else 0.0,
        "extent": area / (w * h) if w * h else 0.0,
        "solidity": area / hull_area if hull_area else 0.0,
        "circularity": (4 * np.pi * area) / (perimetro ** 2) if perimetro else 0.0,
        "vertices_aprox": int(len(approx)),
        "numero_agujeros": int(contar_agujeros(mask)),
    }
    clase = clasificar(prop)

    out = img.copy()
    cv2.drawContours(out, [contorno], -1, (0, 255, 0), 2)
    cv2.circle(out, (cx, cy), 7, (0, 0, 255), -1)
    cv2.rectangle(out, (x, y), (x + w, y + h), (0, 180, 255), 2)

    largo = 140
    xr = int(cx + largo * np.cos(np.deg2rad(angulo)))
    yr = int(cy + largo * np.sin(np.deg2rad(angulo)))
    xl = int(cx - largo * np.cos(np.deg2rad(angulo)))
    yl = int(cy - largo * np.sin(np.deg2rad(angulo)))
    cv2.line(out, (xl, yl), (xr, yr), (255, 0, 0), 3)

    lineas = [
        f"CG ({cx}, {cy})",
        f"Angulo: {angulo:.2f} deg",
        f"Area: {area:.1f} px2",
        f"Figura CAD: {figura}" if figura else None,
        f"Clasificacion: {clase}",
        f"Agujeros: {prop['numero_agujeros']} | Vertices: {prop['vertices_aprox']}",
    ]
    y0 = 40
    for linea in [l for l in lineas if l]:
        cv2.putText(out, linea, (30, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0) if "Angulo" not in linea else (255, 0, 0), 2)
        y0 += 40

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), out)

    return {
        "imagen": image_path.name,
        "centroide_px_x": cx,
        "centroide_px_y": cy,
        "angulo_momentos_grados": angulo,
        "area_px2": area,
        "bbox_x": x,
        "bbox_y": y,
        "bbox_w": w,
        "bbox_h": h,
        "figura_clasificada_python": clase,
        **prop,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Detector compacto de piezas en imagen.")
    parser.add_argument("imagen", help="Ruta de la imagen a procesar.")
    parser.add_argument("--salida", help="Ruta de la imagen anotada de salida.")
    parser.add_argument("--figura", help="Etiqueta CAD opcional.", default=None)
    args = parser.parse_args()

    resultado = detectar_pieza(args.imagen, args.salida, args.figura)
    for k, v in resultado.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
