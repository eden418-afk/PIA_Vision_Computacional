import csv
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent

RESULTADOS_DIR = BASE_DIR / "resultados"
CSV_PATH = RESULTADOS_DIR / "cuadro_experimental.csv"

GRAFICAS_DIR = RESULTADOS_DIR / "graficas"
GRAFICAS_DIR.mkdir(parents=True, exist_ok=True)


def cargar_datos():
    datos = []

    with open(CSV_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            datos.append({
                "imagen": row["imagen"],
                "figura": row["figura"],
                "figura_clasificada_python": row.get("figura_clasificada_python", ""),

                "angulo_cad": float(row["angulo_cad_grados"]),
                "angulo_python": float(row["angulo_python_grados"]),
                "error_angular": float(row["error_angular_grados"]),

                "error_centroide": float(row["error_centroide_mm"]),

                "centroide_cad_x": float(row["centroide_cad_mm_x"]),
                "centroide_cad_y": float(row["centroide_cad_mm_y"]),
                "centroide_python_x": float(row["centroide_python_mm_x"]),
                "centroide_python_y": float(row["centroide_python_mm_y"]),

                "robot_x": float(row["robot_x_mm"]),
                "robot_y": float(row["robot_y_mm"]),
                "robot_z": float(row["robot_z_mm"]),

                "area": float(row["area_px2"]),
                "perimetro": float(row.get("perimetro_px", 0)),
                "aspect_ratio": float(row.get("aspect_ratio", 0)),
                "extent": float(row.get("extent", 0)),
                "solidity": float(row.get("solidity", 0)),
                "circularity": float(row.get("circularity", 0)),
                "vertices": int(float(row.get("vertices_aprox", 0))),
                "agujeros": int(float(row.get("numero_agujeros", 0))),
            })

    return datos


def guardar_grafica_error_centroide(datos):
    imagenes = [d["imagen"].replace(".png", "") for d in datos]
    errores = [d["error_centroide"] for d in datos]

    plt.figure(figsize=(14, 6))
    plt.bar(imagenes, errores)
    plt.title("Error de centroide CAD vs Python")
    plt.xlabel("Imagen")
    plt.ylabel("Error de centroide (mm)")
    plt.xticks(rotation=60, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    output_path = GRAFICAS_DIR / "grafica_error_centroide_mm.png"
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Guardada: {output_path}")


def guardar_grafica_error_angular(datos):
    imagenes = [d["imagen"].replace(".png", "") for d in datos]
    errores = [d["error_angular"] for d in datos]

    plt.figure(figsize=(14, 6))
    plt.plot(imagenes, errores, marker="o")
    plt.title("Error angular CAD vs Python")
    plt.xlabel("Imagen")
    plt.ylabel("Error angular (grados)")
    plt.xticks(rotation=60, ha="right")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    output_path = GRAFICAS_DIR / "grafica_error_angular.png"
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Guardada: {output_path}")


def guardar_grafica_comparacion_angulos(datos):
    imagenes = [d["imagen"].replace(".png", "") for d in datos]
    angulos_cad = [d["angulo_cad"] for d in datos]
    angulos_python = [d["angulo_python"] for d in datos]

    plt.figure(figsize=(14, 6))
    plt.plot(imagenes, angulos_cad, marker="o", label="Ángulo CAD")
    plt.plot(imagenes, angulos_python, marker="x", label="Ángulo Python")
    plt.title("Comparación entre ángulo CAD y ángulo calculado por Python")
    plt.xlabel("Imagen")
    plt.ylabel("Ángulo (grados)")
    plt.xticks(rotation=60, ha="right")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    output_path = GRAFICAS_DIR / "grafica_comparacion_angulos_cad_python.png"
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Guardada: {output_path}")


def guardar_grafica_centroides_mm(datos):
    cad_x = [d["centroide_cad_x"] for d in datos]
    cad_y = [d["centroide_cad_y"] for d in datos]

    python_x = [d["centroide_python_x"] for d in datos]
    python_y = [d["centroide_python_y"] for d in datos]

    plt.figure(figsize=(10, 6))
    plt.scatter(cad_x, cad_y, marker="o", label="Centroide CAD")
    plt.scatter(python_x, python_y, marker="x", label="Centroide Python")
    plt.title("Comparación de centroides CAD vs Python")
    plt.xlabel("X mesa (mm)")
    plt.ylabel("Y mesa (mm)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    output_path = GRAFICAS_DIR / "grafica_comparacion_centroides_mm.png"
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Guardada: {output_path}")


def guardar_grafica_coordenadas_robot(datos):
    robot_x = [d["robot_x"] for d in datos]
    robot_y = [d["robot_y"] for d in datos]

    plt.figure(figsize=(10, 6))
    plt.scatter(robot_x, robot_y, marker="o")
    plt.title("Posición calculada de objetos en coordenadas del robot")
    plt.xlabel("Robot X (mm)")
    plt.ylabel("Robot Y (mm)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    output_path = GRAFICAS_DIR / "grafica_coordenadas_robot_xy.png"
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Guardada: {output_path}")


def guardar_grafica_propiedades_geometricas(datos):
    imagenes = [d["imagen"].replace(".png", "") for d in datos]
    solidity = [d["solidity"] for d in datos]
    circularity = [d["circularity"] for d in datos]
    extent = [d["extent"] for d in datos]

    plt.figure(figsize=(14, 6))
    plt.plot(imagenes, solidity, marker="o", label="Solidity")
    plt.plot(imagenes, circularity, marker="x", label="Circularity")
    plt.plot(imagenes, extent, marker="s", label="Extent")
    plt.title("Propiedades geométricas por imagen")
    plt.xlabel("Imagen")
    plt.ylabel("Valor")
    plt.xticks(rotation=60, ha="right")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    output_path = GRAFICAS_DIR / "grafica_propiedades_geometricas.png"
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Guardada: {output_path}")


def guardar_grafica_agujeros_vertices(datos):
    imagenes = [d["imagen"].replace(".png", "") for d in datos]
    agujeros = [d["agujeros"] for d in datos]
    vertices = [d["vertices"] for d in datos]

    plt.figure(figsize=(14, 6))
    plt.bar(imagenes, vertices, label="Vértices aproximados")
    plt.plot(imagenes, agujeros, marker="o", label="Número de agujeros")
    plt.title("Vértices aproximados y agujeros detectados")
    plt.xlabel("Imagen")
    plt.ylabel("Cantidad")
    plt.xticks(rotation=60, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    output_path = GRAFICAS_DIR / "grafica_agujeros_vertices.png"
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Guardada: {output_path}")


def guardar_grafica_conteo_clasificacion(datos):
    conteo = {}

    for d in datos:
        clase = d["figura_clasificada_python"]
        conteo[clase] = conteo.get(clase, 0) + 1

    clases = list(conteo.keys())
    cantidades = list(conteo.values())

    plt.figure(figsize=(14, 6))
    plt.bar(clases, cantidades)
    plt.title("Conteo de clasificaciones geométricas generadas por Python")
    plt.xlabel("Clasificación Python")
    plt.ylabel("Cantidad de piezas")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    output_path = GRAFICAS_DIR / "grafica_conteo_clasificacion_python.png"
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Guardada: {output_path}")


def generar_graficas():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"No existe el archivo: {CSV_PATH}")

    datos = cargar_datos()

    if not datos:
        raise ValueError("No se encontraron datos en el CSV.")

    guardar_grafica_error_centroide(datos)
    guardar_grafica_error_angular(datos)
    guardar_grafica_comparacion_angulos(datos)
    guardar_grafica_centroides_mm(datos)
    guardar_grafica_coordenadas_robot(datos)
    guardar_grafica_propiedades_geometricas(datos)
    guardar_grafica_agujeros_vertices(datos)
    guardar_grafica_conteo_clasificacion(datos)

    print("\nGráficas generadas correctamente.")
    print(f"Carpeta: {GRAFICAS_DIR}")


if __name__ == "__main__":
    generar_graficas()