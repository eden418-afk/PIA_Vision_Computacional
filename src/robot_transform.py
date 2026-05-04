import numpy as np


# ==========================
# Configuración de la mesa
# ==========================

TABLE_WIDTH_MM = 320
TABLE_HEIGHT_MM = 180

IMAGE_WIDTH_PX = 1280
IMAGE_HEIGHT_PX = 720

# Caso base del enunciado / figura de referencia.
# El programa queda parametrizable.
TABLE_TRANSLATION_MM = np.array([200.0, -50.0, 400.0])
TABLE_ROTATION_DEG = np.array([0.0, -30.0, 0.0])


def pixel_to_table_mm(px, py):
    """
    Convierte coordenadas de píxel a coordenadas locales de la mesa en mm.

    Se asume:
    - La imagen completa representa la mesa.
    - El origen local de la mesa está en el centro de la imagen.
    - X positivo hacia la derecha de la imagen.
    - Y positivo hacia arriba de la imagen.
    """

    x_mm = (px - IMAGE_WIDTH_PX / 2) * (TABLE_WIDTH_MM / IMAGE_WIDTH_PX)
    y_mm = -(py - IMAGE_HEIGHT_PX / 2) * (TABLE_HEIGHT_MM / IMAGE_HEIGHT_PX)

    return float(x_mm), float(y_mm)


def rotation_matrix_x(angle_deg):
    angle_rad = np.deg2rad(angle_deg)

    c = np.cos(angle_rad)
    s = np.sin(angle_rad)

    return np.array([
        [1, 0, 0],
        [0, c, -s],
        [0, s, c]
    ])


def rotation_matrix_y(angle_deg):
    angle_rad = np.deg2rad(angle_deg)

    c = np.cos(angle_rad)
    s = np.sin(angle_rad)

    return np.array([
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c]
    ])


def rotation_matrix_z(angle_deg):
    angle_rad = np.deg2rad(angle_deg)

    c = np.cos(angle_rad)
    s = np.sin(angle_rad)

    return np.array([
        [c, -s, 0],
        [s, c, 0],
        [0, 0, 1]
    ])


def build_table_transform(translation_mm, rotation_deg):
    """
    Construye la matriz homogénea de transformación de la mesa
    respecto al sistema universal del robot.

    Se usa la convención:
    R = Rz(psi) * Ry(phi) * Rx(theta)

    Donde:
    rotation_deg = (theta, phi, psi)
    """

    theta, phi, psi = rotation_deg

    Rx = rotation_matrix_x(theta)
    Ry = rotation_matrix_y(phi)
    Rz = rotation_matrix_z(psi)

    R = Rz @ Ry @ Rx

    T = np.eye(4)
    T[0:3, 0:3] = R
    T[0:3, 3] = translation_mm

    return T


def table_point_to_robot(x_table_mm, y_table_mm, z_table_mm=0.0):
    """
    Transforma un punto local de la mesa al sistema de coordenadas del robot.
    """

    T_table_robot = build_table_transform(
        TABLE_TRANSLATION_MM,
        TABLE_ROTATION_DEG
    )

    p_table = np.array([
        x_table_mm,
        y_table_mm,
        z_table_mm,
        1.0
    ])

    p_robot = T_table_robot @ p_table

    return float(p_robot[0]), float(p_robot[1]), float(p_robot[2])


def calculate_tcp_orientation(object_angle_deg):
    """
    Calcula una orientación simplificada para el TCP del robot.

    La mesa tiene una inclinación propia y la pieza tiene un ángulo dentro
    del plano de la mesa. Para este PIA se reporta una orientación conceptual:

    - theta: inclinación X de la mesa
    - phi: inclinación Y de la mesa
    - psi: rotación alrededor de Z ajustada al ángulo de la pieza
    """

    theta, phi, psi = TABLE_ROTATION_DEG

    tcp_theta = theta
    tcp_phi = phi
    tcp_psi = psi + object_angle_deg

    return float(tcp_theta), float(tcp_phi), float(tcp_psi)