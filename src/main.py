import csv
from pathlib import Path

from vision import procesar_imagen
from robot_transform import (
    pixel_to_table_mm,
    table_point_to_robot,
    calculate_tcp_orientation
)


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "dataset" / "originales"
RESULTADOS_DIR = BASE_DIR / "resultados"
IMAGENES_RESULTADO_DIR = RESULTADOS_DIR / "imagenes_resultado"

GROUND_TRUTH_PATH = RESULTADOS_DIR / "cad_ground_truth.csv"
OUTPUT_CSV_PATH = RESULTADOS_DIR / "cuadro_experimental.csv"


def cargar_ground_truth():
    """
    Carga el archivo cad_ground_truth.csv generado por la macro de FreeCAD.
    Este archivo contiene la referencia CAD: centroide e inclinación de diseño.
    """

    ground_truth = {}

    with open(GROUND_TRUTH_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            ground_truth[row["imagen"]] = row

    return ground_truth


def calcular_error_centroide_mm(x_calc, y_calc, x_cad, y_cad):
    """
    Calcula el error euclidiano entre el centroide calculado por Python/OpenCV
    y el centroide de referencia obtenido en CAD.
    """

    dx = float(x_calc) - float(x_cad)
    dy = float(y_calc) - float(y_cad)

    return (dx ** 2 + dy ** 2) ** 0.5


def normalizar_error_angular(angle_calc, angle_cad):
    """
    Calcula diferencia angular considerando equivalencia de ejes.

    Para piezas donde el eje principal no tiene dirección única,
    0° y 180° representan el mismo eje. Por eso se normaliza
    la diferencia al rango [-90, 90].
    """

    diff = float(angle_calc) - float(angle_cad)

    while diff > 90:
        diff -= 180

    while diff < -90:
        diff += 180

    return abs(diff)


def procesar_dataset():
    ground_truth = cargar_ground_truth()

    image_paths = sorted(DATASET_DIR.glob("*.png"))

    if not image_paths:
        raise FileNotFoundError(f"No se encontraron imágenes en: {DATASET_DIR}")

    IMAGENES_RESULTADO_DIR.mkdir(parents=True, exist_ok=True)

    filas = []

    for image_path in image_paths:
        if image_path.name not in ground_truth:
            print(f"Advertencia: {image_path.name} no existe en cad_ground_truth.csv. Se omite.")
            continue

        output_image_path = IMAGENES_RESULTADO_DIR / f"resultado_{image_path.name}"

        gt = ground_truth[image_path.name]

        resultado_vision = procesar_imagen(
            image_path=image_path,
            output_path=output_image_path,
            mostrar=False,
            figura=gt["figura"]
        )


        # Resultados de visión en píxeles
        cx_python_px = resultado_vision["centroide_px_x"]
        cy_python_px = resultado_vision["centroide_px_y"]
        angulo_python = resultado_vision["angulo_momentos_grados"]

        # Convertir centroide detectado por Python/OpenCV a mm en el plano de la mesa
        x_python_mm, y_python_mm = pixel_to_table_mm(
            cx_python_px,
            cy_python_px
        )

        # Referencia CAD
        x_cad_mm = float(gt["centroide_cad_mm_x"])
        y_cad_mm = float(gt["centroide_cad_mm_y"])
        z_cad_mm = float(gt["centroide_cad_mm_z"])
        angulo_cad = float(gt["angulo_cad_grados"])

        # Errores CAD vs Python
        error_centroide_mm = calcular_error_centroide_mm(
            x_python_mm,
            y_python_mm,
            x_cad_mm,
            y_cad_mm
        )

        error_angular_deg = normalizar_error_angular(
            angulo_python,
            angulo_cad
        )

        # Transformación al sistema de coordenadas del robot
        # Usamos el centroide calculado por Python, porque representa lo que detectaría la cámara.
        x_robot_mm, y_robot_mm, z_robot_mm = table_point_to_robot(
            x_python_mm,
            y_python_mm,
            z_table_mm=0.0
        )

        # Orientación conceptual del TCP
        tcp_theta, tcp_phi, tcp_psi = calculate_tcp_orientation(
            angulo_python
        )

        fila = {
            "imagen": image_path.name,
            "modelo_cad": gt["modelo_cad"],
            "figura": gt["figura"],

            "angulo_cad_grados": round(angulo_cad, 4),
            "angulo_python_grados": round(angulo_python, 4),
            "error_angular_grados": round(error_angular_deg, 4),

            "centroide_cad_mm_x": round(x_cad_mm, 4),
            "centroide_cad_mm_y": round(y_cad_mm, 4),
            "centroide_cad_mm_z": round(z_cad_mm, 4),

            "centroide_python_px_x": round(cx_python_px, 4),
            "centroide_python_px_y": round(cy_python_px, 4),

            "centroide_python_mm_x": round(x_python_mm, 4),
            "centroide_python_mm_y": round(y_python_mm, 4),

            "error_centroide_mm": round(error_centroide_mm, 4),

            "robot_x_mm": round(x_robot_mm, 4),
            "robot_y_mm": round(y_robot_mm, 4),
            "robot_z_mm": round(z_robot_mm, 4),

            "tcp_theta_deg": round(tcp_theta, 4),
            "tcp_phi_deg": round(tcp_phi, 4),
            "tcp_psi_deg": round(tcp_psi, 4),

            "area_px2": round(resultado_vision["area_px2"], 4),
            "bbox_x": resultado_vision["bbox_x"],
            "bbox_y": resultado_vision["bbox_y"],
            "bbox_w": resultado_vision["bbox_w"],
            "bbox_h": resultado_vision["bbox_h"],

            "figura_clasificada_python": resultado_vision["figura_clasificada_python"],

            "perimetro_px": round(resultado_vision["perimetro_px"], 4),
            "aspect_ratio": round(resultado_vision["aspect_ratio"], 4),
            "extent": round(resultado_vision["extent"], 4),
            "solidity": round(resultado_vision["solidity"], 4),
            "circularity": round(resultado_vision["circularity"], 4),
            "vertices_aprox": resultado_vision["vertices_aprox"],
            "numero_agujeros": resultado_vision["numero_agujeros"],
        }

        filas.append(fila)

        print(
            f"{image_path.name} | "
            f"CAD=({x_cad_mm:.2f}, {y_cad_mm:.2f}) mm | "
            f"Python=({x_python_mm:.2f}, {y_python_mm:.2f}) mm | "
            f"Error CG={error_centroide_mm:.4f} mm | "
            f"Angulo CAD={angulo_cad:.2f}° | "
            f"Angulo Python={angulo_python:.2f}° | "
            f"Robot=({x_robot_mm:.2f}, {y_robot_mm:.2f}, {z_robot_mm:.2f})"
        )

    guardar_csv(filas)

    print("\nProcesamiento completo.")
    print(f"Tabla experimental guardada en: {OUTPUT_CSV_PATH}")
    print(f"Imágenes procesadas guardadas en: {IMAGENES_RESULTADO_DIR}")


def guardar_csv(filas):
    if not filas:
        print("No se generaron filas para guardar.")
        return

    fieldnames = list(filas[0].keys())

    with open(OUTPUT_CSV_PATH, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for fila in filas:
            writer.writerow(fila)


if __name__ == "__main__":
    procesar_dataset()