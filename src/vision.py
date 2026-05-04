import cv2
import numpy as np
from pathlib import Path


def calcular_orientacion_momentos(contour):
    """
    Calcula la orientación del objeto usando momentos centrales de segundo orden.

    Retorna el ángulo en grados respecto al eje X de la imagen.
    """
    M = cv2.moments(contour)

    if M["m00"] == 0:
        return None

    mu20 = M["mu20"] / M["m00"]
    mu02 = M["mu02"] / M["m00"]
    mu11 = M["mu11"] / M["m00"]

    angle_rad = 0.5 * np.arctan2(2 * mu11, mu20 - mu02)
    angle_deg = np.degrees(angle_rad)

    return angle_deg


def normalizar_angulo(angle):
    """
    Normaliza el ángulo al rango [-90, 90].
    """
    if angle is None:
        return None

    while angle > 90:
        angle -= 180

    while angle < -90:
        angle += 180

    return angle


def contar_agujeros(binary_clean, area_minima=30):
    """
    Cuenta agujeros internos en la pieza usando jerarquía de contornos.

    La imagen binary_clean debe tener:
    - pieza en blanco
    - fondo en negro
    - agujeros en negro
    """
    contours, hierarchy = cv2.findContours(
        binary_clean,
        cv2.RETR_CCOMP,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if hierarchy is None:
        return 0

    hierarchy = hierarchy[0]
    holes = 0

    for i, contour in enumerate(contours):
        parent = hierarchy[i][3]

        # Si tiene parent, es un contorno interno.
        if parent != -1:
            area = cv2.contourArea(contour)

            if area >= area_minima:
                holes += 1

    return holes


def extraer_propiedades_geometricas(main_contour, binary_clean):
    """
    Extrae propiedades geométricas útiles para discriminar figuras.
    """

    area = cv2.countNonZero(binary_clean)
    perimetro = cv2.arcLength(main_contour, True)

    x, y, w, h = cv2.boundingRect(main_contour)

    aspect_ratio = w / h if h != 0 else 0
    extent = area / (w * h) if w * h != 0 else 0

    hull = cv2.convexHull(main_contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area != 0 else 0

    circularity = 0
    if perimetro != 0:
        circularity = (4 * np.pi * area) / (perimetro ** 2)

    epsilon = 0.02 * perimetro
    approx = cv2.approxPolyDP(main_contour, epsilon, True)
    vertices = len(approx)

    numero_agujeros = contar_agujeros(binary_clean)

    return {
        "perimetro_px": float(perimetro),
        "aspect_ratio": float(aspect_ratio),
        "extent": float(extent),
        "solidity": float(solidity),
        "circularity": float(circularity),
        "vertices_aprox": int(vertices),
        "numero_agujeros": int(numero_agujeros),
    }


def clasificar_figura_geometrica(propiedades):
    """
    Clasifica la pieza usando reglas simples basadas en propiedades geométricas.

    Esta clasificación no reemplaza la etiqueta CAD.
    Sirve para demostrar discriminación geométrica automática.
    """

    vertices = propiedades["vertices_aprox"]
    holes = propiedades["numero_agujeros"]
    aspect_ratio = propiedades["aspect_ratio"]
    solidity = propiedades["solidity"]
    circularity = propiedades["circularity"]
    extent = propiedades["extent"]

    # Figuras circulares o casi circulares
    if circularity > 0.80 and vertices > 10:
        if holes >= 1:
            return "circulo_o_brida_circular"
        return "circulo"

    # Polígonos regulares o casi regulares
    if vertices == 3:
        return "triangulo"

    if vertices == 4:
        if aspect_ratio > 2.0 or aspect_ratio < 0.5:
            return "placa_alargada"
        return "cuadrilatero_rombo_rectangulo"

    if vertices == 5:
        return "pentagono"

    if vertices == 6:
        return "hexagono"

    if 7 <= vertices <= 9:
        return "octagono_o_poligono_regular"

    # Piezas dentadas: muchos vértices y baja solidez
    if vertices >= 14 and solidity < 0.85:
        if holes >= 1:
            return "engrane_o_pieza_dentada_perforada"
        return "pieza_dentada"

    # Bridas o placas con muchos agujeros
    if holes >= 4:
        return "brida_o_placa_multiples_perforaciones"

    if holes == 3:
        return "base_o_soporte_tres_perforaciones"

    if holes == 2:
        if aspect_ratio > 2.0:
            return "brazo_mecanico_o_placa_ranurada"
        if solidity < 0.80:
            return "soporte_muescado_o_irregular"
        return "pieza_dos_perforaciones"

    if holes == 1:
        if solidity < 0.70:
            return "perfil_abierto_o_irregular"
        return "pieza_una_perforacion"

    # Perfiles abiertos o irregulares sin agujeros
    if solidity < 0.70:
        return "perfil_irregular_o_abierto"

    if extent < 0.55:
        return "pieza_con_geometria_compuesta"

    return "pieza_general"


def procesar_imagen(image_path, output_path=None, mostrar=False, figura=None):
    """
    Procesa una imagen sintética y calcula:
    - centroide de la pieza completa
    - orientación por momentos de la máscara
    - contorno exterior principal
    - área
    - bounding box

    Importante:
    El centroide y la orientación se calculan sobre la máscara binaria,
    no sobre los bordes de Canny. Esto evita que OpenCV tome los agujeros
    como si fueran la pieza principal.
    """

    image_path = Path(image_path)

    img = cv2.imread(str(image_path))

    if img is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")

    original = img.copy()

    # 1. Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Binarizar.
    # Fondo blanco, pieza oscura.
    # Resultado: pieza blanca, fondo negro, agujeros negros.
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # 3. Limpieza morfológica ligera
    kernel = np.ones((3, 3), np.uint8)
    binary_clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # 4. Detectar bordes solo para visualización
    edges = cv2.Canny(binary_clean, 50, 150)

    # 5. Encontrar el contorno exterior de la pieza usando la máscara,
    # no los bordes de Canny.
    contours, _ = cv2.findContours(
        binary_clean,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        raise ValueError(f"No se encontraron contornos en: {image_path.name}")

    main_contour = max(contours, key=cv2.contourArea)

    # 6. Calcular momentos sobre la máscara completa.
    # Esto toma en cuenta la masa real de la pieza y descuenta agujeros.
    M = cv2.moments(binary_clean, binaryImage=True)

    if M["m00"] == 0:
        raise ValueError(f"La máscara no tiene área válida: {image_path.name}")

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    # 7. Calcular orientación sobre la máscara completa
    mu20 = M["mu20"] / M["m00"]
    mu02 = M["mu02"] / M["m00"]
    mu11 = M["mu11"] / M["m00"]

    angle_rad = 0.5 * np.arctan2(2 * mu11, mu20 - mu02)
    angle_moments = np.degrees(angle_rad)
    angle_moments = normalizar_angulo(angle_moments)

    # 8. Orientación alternativa con minAreaRect sobre contorno exterior
    rect = cv2.minAreaRect(main_contour)
    (rect_cx, rect_cy), (rect_w, rect_h), angle_rect = rect

    if rect_w < rect_h:
        angle_rect = angle_rect + 90

    angle_rect = normalizar_angulo(angle_rect)

    # 9. Área real de la máscara.
    # cv2.countNonZero cuenta los píxeles blancos de la pieza.
    area = cv2.countNonZero(binary_clean)

    x, y, w, h = cv2.boundingRect(main_contour)

    propiedades = extraer_propiedades_geometricas(main_contour, binary_clean)
    figura_clasificada = clasificar_figura_geometrica(propiedades)

    # 10. Dibujar resultados
    result = original.copy()

    # Contorno exterior
    cv2.drawContours(result, [main_contour], -1, (0, 255, 0), 2)

    # Centroide
    cv2.circle(result, (cx, cy), 7, (0, 0, 255), -1)
    cv2.putText(
        result,
        f"CG ({cx}, {cy})",
        (cx + 10, cy - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2
    )

    # Eje principal
    length = 140
    angle_rad = np.deg2rad(angle_moments)

    x2 = int(cx + length * np.cos(angle_rad))
    y2 = int(cy + length * np.sin(angle_rad))

    x1 = int(cx - length * np.cos(angle_rad))
    y1 = int(cy - length * np.sin(angle_rad))

    cv2.line(result, (x1, y1), (x2, y2), (255, 0, 0), 3)

    cv2.putText(
        result,
        f"Angulo: {angle_moments:.2f} deg",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 0, 0),
        2
    )

    cv2.putText(
        result,
        f"Area: {area:.1f} px2",
        (30, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2
    )

    if figura is not None:
        cv2.putText(
            result,
            f"Figura CAD: {figura}",
            (30, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2
        )

        cv2.putText(
            result,
            f"Clasificacion: {figura_clasificada}",
            (30, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2
        )

        cv2.putText(
            result,
            f"Agujeros: {propiedades['numero_agujeros']} | Vertices: {propiedades['vertices_aprox']}",
            (30, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            2
        )

    # Bounding box exterior
    cv2.rectangle(result, (x, y), (x + w, y + h), (0, 180, 255), 2)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), result)

    if mostrar:
        cv2.imshow("Original", original)
        cv2.imshow("Binaria", binary_clean)
        cv2.imshow("Bordes Canny", edges)
        cv2.imshow("Resultado", result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return {
        "imagen": image_path.name,
        "centroide_px_x": cx,
        "centroide_px_y": cy,
        "angulo_momentos_grados": float(angle_moments),
        "angulo_minAreaRect_grados": float(angle_rect),
        "area_px2": float(area),
        "bbox_x": int(x),
        "bbox_y": int(y),
        "bbox_w": int(w),
        "bbox_h": int(h),

        "figura_clasificada_python": figura_clasificada,
        "perimetro_px": propiedades["perimetro_px"],
        "aspect_ratio": propiedades["aspect_ratio"],
        "extent": propiedades["extent"],
        "solidity": propiedades["solidity"],
        "circularity": propiedades["circularity"],
        "vertices_aprox": propiedades["vertices_aprox"],
        "numero_agujeros": propiedades["numero_agujeros"],
    }