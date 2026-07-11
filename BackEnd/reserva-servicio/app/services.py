from .database import get_connection


def crear_reserva(reserva):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO reservas(id_asiento,cliente,correo)
        VALUES(%s,%s,%s)
        RETURNING id_reserva;
    """

    cursor.execute(
        query,
        (
            reserva.id_asiento,
            reserva.cliente,
            reserva.correo
        )
    )

    reserva_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return reserva_id


def obtener_reservas():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id_reserva,
            id_asiento,
            cliente,
            correo,
            estado
        FROM reservas
        ORDER BY id_reserva;
    """)

    reservas = cursor.fetchall()

    cursor.close()
    conn.close()

    return reservas


def obtener_reserva(id_reserva):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id_reserva,
            id_asiento,
            cliente,
            correo,
            estado
        FROM reservas
        WHERE id_reserva=%s;
    """,(id_reserva,))

    reserva = cursor.fetchone()

    cursor.close()
    conn.close()

    return reserva