import cv2
import numpy as np
import csv
from pathlib import Path


# ==========================
# Configuración general
# ==========================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset" / "originales"
RESULTADOS_DIR = BASE_DIR / "resultados"

IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720

TABLE_WIDTH_MM = 320
TABLE_HEIGHT_MM = 180

BACKGROUND_COLOR = (255, 255, 255)
OBJECT_COLOR = (35, 35, 35)

DATASET_DIR.mkdir(parents=True, exist_ok=True)
RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)


def rotate_points(points, angle_deg, center):
    angle_rad = np.deg2rad(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)

    rotated = []
    cx, cy = center

    for x, y in points:
        x_shift = x - cx
        y_shift = y - cy

        x_rot = x_shift * cos_a - y_shift * sin_a + cx
        y_rot = x_shift * sin_a + y_shift * cos_a + cy

        rotated.append([int(round(x_rot)), int(round(y_rot))])

    return np.array(rotated, dtype=np.int32)


def draw_rotated_polygon(image, points, angle_deg, center):
    contour = rotate_points(points, angle_deg, center)
    cv2.fillPoly(image, [contour], OBJECT_COLOR)
    return contour


def draw_rotated_hole(image, center, offset, radius, angle_deg):
    """
    Dibuja un agujero circular rotado junto con la pieza.
    Se dibuja en blanco para simular perforación.
    """
    cx, cy = center
    ox, oy = offset

    point = rotate_points([[cx + ox, cy + oy]], angle_deg, center)[0]
    cv2.circle(image, tuple(point), radius, BACKGROUND_COLOR, -1)


def create_slotted_plate(image, center, angle_deg):
    """
    Placa rectangular con dos agujeros.
    """
    cx, cy = center

    points = [
        [cx - 170, cy - 55],
        [cx + 170, cy - 55],
        [cx + 170, cy + 55],
        [cx - 170, cy + 55],
    ]

    contour = draw_rotated_polygon(image, points, angle_deg, center)

    draw_rotated_hole(image, center, (-95, 0), 24, angle_deg)
    draw_rotated_hole(image, center, (95, 0), 24, angle_deg)

    return contour


def create_stepped_bracket(image, center, angle_deg):
    """
    Perfil escalonado tipo soporte mecánico.
    """
    cx, cy = center

    points = [
        [cx - 170, cy - 80],
        [cx - 40, cy - 80],
        [cx - 40, cy - 35],
        [cx + 60, cy - 35],
        [cx + 60, cy - 80],
        [cx + 170, cy - 80],
        [cx + 170, cy + 80],
        [cx + 60, cy + 80],
        [cx + 60, cy + 35],
        [cx - 40, cy + 35],
        [cx - 40, cy + 80],
        [cx - 170, cy + 80],
    ]

    contour = draw_rotated_polygon(image, points, angle_deg, center)

    draw_rotated_hole(image, center, (-105, 0), 22, angle_deg)
    draw_rotated_hole(image, center, (115, 0), 22, angle_deg)

    return contour


def create_l_bracket(image, center, angle_deg):
    """
    Pieza tipo L con agujero.
    """
    cx, cy = center

    points = [
        [cx - 140, cy - 120],
        [cx - 20, cy - 120],
        [cx - 20, cy - 30],
        [cx + 140, cy - 30],
        [cx + 140, cy + 90],
        [cx - 140, cy + 90],
    ]

    contour = draw_rotated_polygon(image, points, angle_deg, center)

    draw_rotated_hole(image, center, (-80, 35), 22, angle_deg)
    draw_rotated_hole(image, center, (75, 35), 20, angle_deg)

    return contour


def create_u_profile(image, center, angle_deg):
    """
    Perfil tipo U o canal.
    """
    cx, cy = center

    points = [
        [cx - 170, cy - 90],
        [cx + 170, cy - 90],
        [cx + 170, cy - 35],
        [cx - 85, cy - 35],
        [cx - 85, cy + 35],
        [cx + 170, cy + 35],
        [cx + 170, cy + 90],
        [cx - 170, cy + 90],
    ]

    contour = draw_rotated_polygon(image, points, angle_deg, center)

    draw_rotated_hole(image, center, (-125, 0), 22, angle_deg)

    return contour


def create_cross_plate(image, center, angle_deg):
    """
    Placa tipo cruz o unión mecánica.
    """
    cx, cy = center

    points = [
        [cx - 65, cy - 155],
        [cx + 65, cy - 155],
        [cx + 65, cy - 65],
        [cx + 155, cy - 65],
        [cx + 155, cy + 65],
        [cx + 65, cy + 65],
        [cx + 65, cy + 155],
        [cx - 65, cy + 155],
        [cx - 65, cy + 65],
        [cx - 155, cy + 65],
        [cx - 155, cy - 65],
        [cx - 65, cy - 65],
    ]

    contour = draw_rotated_polygon(image, points, angle_deg, center)

    draw_rotated_hole(image, center, (0, 0), 24, angle_deg)

    return contour


def create_link_arm(image, center, angle_deg):
    """
    Brazo mecánico alargado con extremos redondeados simulados mediante círculos.
    """
    cx, cy = center

    # Cuerpo rectangular
    points = [
        [cx - 145, cy - 45],
        [cx + 145, cy - 45],
        [cx + 145, cy + 45],
        [cx - 145, cy + 45],
    ]

    contour = draw_rotated_polygon(image, points, angle_deg, center)

    # Extremos redondeados, rotados junto con la pieza
    left_center = rotate_points([[cx - 145, cy]], angle_deg, center)[0]
    right_center = rotate_points([[cx + 145, cy]], angle_deg, center)[0]

    cv2.circle(image, tuple(left_center), 45, OBJECT_COLOR, -1)
    cv2.circle(image, tuple(right_center), 45, OBJECT_COLOR, -1)

    # Agujeros
    draw_rotated_hole(image, center, (-145, 0), 22, angle_deg)
    draw_rotated_hole(image, center, (145, 0), 22, angle_deg)

    return contour


def create_flange_plate(image, center, angle_deg):
    """
    Placa tipo brida con cuerpo central y cuatro agujeros.
    """
    cx, cy = center

    points = [
        [cx - 130, cy - 95],
        [cx + 130, cy - 95],
        [cx + 160, cy - 45],
        [cx + 160, cy + 45],
        [cx + 130, cy + 95],
        [cx - 130, cy + 95],
        [cx - 160, cy + 45],
        [cx - 160, cy - 45],
    ]

    contour = draw_rotated_polygon(image, points, angle_deg, center)

    draw_rotated_hole(image, center, (-90, -45), 18, angle_deg)
    draw_rotated_hole(image, center, (90, -45), 18, angle_deg)
    draw_rotated_hole(image, center, (-90, 45), 18, angle_deg)
    draw_rotated_hole(image, center, (90, 45), 18, angle_deg)

    return contour


def create_irregular_mount(image, center, angle_deg):
    """
    Perfil irregular tipo base de montaje.
    """
    cx, cy = center

    points = [
        [cx - 165, cy - 70],
        [cx - 70, cy - 70],
        [cx - 45, cy - 115],
        [cx + 45, cy - 115],
        [cx + 70, cy - 70],
        [cx + 165, cy - 70],
        [cx + 165, cy + 45],
        [cx + 95, cy + 45],
        [cx + 70, cy + 95],
        [cx - 70, cy + 95],
        [cx - 95, cy + 45],
        [cx - 165, cy + 45],
    ]

    contour = draw_rotated_polygon(image, points, angle_deg, center)

    draw_rotated_hole(image, center, (0, -35), 24, angle_deg)
    draw_rotated_hole(image, center, (-110, 10), 18, angle_deg)
    draw_rotated_hole(image, center, (110, 10), 18, angle_deg)

    return contour


def draw_shape(image, shape_type, center, angle_deg):
    if shape_type == "placa_ranurada":
        return create_slotted_plate(image, center, angle_deg)

    if shape_type == "soporte_escalonado":
        return create_stepped_bracket(image, center, angle_deg)

    if shape_type == "soporte_L":
        return create_l_bracket(image, center, angle_deg)

    if shape_type == "perfil_U":
        return create_u_profile(image, center, angle_deg)

    if shape_type == "placa_cruz":
        return create_cross_plate(image, center, angle_deg)

    if shape_type == "brazo_mecanico":
        return create_link_arm(image, center, angle_deg)

    if shape_type == "placa_brida":
        return create_flange_plate(image, center, angle_deg)

    if shape_type == "base_irregular":
        return create_irregular_mount(image, center, angle_deg)

    raise ValueError(f"Tipo de figura no reconocido: {shape_type}")


def pixel_to_table_mm(px, py):
    x_mm = (px - IMAGE_WIDTH / 2) * (TABLE_WIDTH_MM / IMAGE_WIDTH)
    y_mm = -(py - IMAGE_HEIGHT / 2) * (TABLE_HEIGHT_MM / IMAGE_HEIGHT)

    return x_mm, y_mm


def generate_dataset():
    metadata_path = RESULTADOS_DIR / "dataset_ground_truth.csv"

    shapes = [
        "placa_ranurada",
        "placa_ranurada",
        "soporte_escalonado",
        "soporte_escalonado",
        "soporte_L",
        "soporte_L",
        "perfil_U",
        "perfil_U",
        "placa_cruz",
        "placa_cruz",
        "brazo_mecanico",
        "brazo_mecanico",
        "placa_brida",
        "placa_brida",
        "base_irregular",
        "base_irregular",
        "soporte_escalonado",
        "perfil_U",
        "brazo_mecanico",
        "base_irregular",
    ]

    angles = [
        0, 15, 25, 40, 55,
        70, 85, 100, 115, 130,
        145, -15, -30, -45, -60,
        -75, -90, -110, -130, -150
    ]

    centers = [
        (640, 360),
        (620, 350),
        (660, 370),
        (600, 340),
        (680, 380),
        (640, 360),
        (620, 360),
        (660, 360),
        (640, 340),
        (640, 380),
        (600, 360),
        (680, 360),
        (640, 360),
        (620, 350),
        (660, 370),
        (600, 340),
        (680, 380),
        (640, 360),
        (620, 360),
        (660, 360),
    ]

    with open(metadata_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([
            "imagen",
            "figura",
            "angulo_real_grados",
            "centroide_real_px_x",
            "centroide_real_px_y",
            "centroide_real_mm_x",
            "centroide_real_mm_y",
            "ancho_imagen_px",
            "alto_imagen_px",
            "ancho_mesa_mm",
            "alto_mesa_mm",
        ])

        for i in range(20):
            image = np.full(
                (IMAGE_HEIGHT, IMAGE_WIDTH, 3),
                BACKGROUND_COLOR,
                dtype=np.uint8
            )

            shape_type = shapes[i]
            angle = angles[i]
            center = centers[i]

            draw_shape(image, shape_type, center, angle)

            filename = f"pieza_{i + 1:02d}.png"
            image_path = DATASET_DIR / filename

            cv2.imwrite(str(image_path), image)

            cx_px, cy_px = center
            cx_mm, cy_mm = pixel_to_table_mm(cx_px, cy_px)

            writer.writerow([
                filename,
                shape_type,
                angle,
                cx_px,
                cy_px,
                round(cx_mm, 4),
                round(cy_mm, 4),
                IMAGE_WIDTH,
                IMAGE_HEIGHT,
                TABLE_WIDTH_MM,
                TABLE_HEIGHT_MM,
            ])

            print(
                f"Generada: {filename} | "
                f"Figura: {shape_type} | "
                f"Ángulo: {angle}° | "
                f"Centro: {center}"
            )

    print("\nDataset generado correctamente.")
    print(f"Imágenes guardadas en: {DATASET_DIR}")
    print(f"Ground truth guardado en: {metadata_path}")


if __name__ == "__main__":
    generate_dataset()