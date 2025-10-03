from datetime import datetime, timedelta
# Asegúrate de que 'db' es el módulo correcto que contiene la función 'conectar'
from db import conectar 
import sqlite3

# --- CONSTANTES CENTRALIZADAS ---
TIPOS_FICHAJE = ["Entrada", "Ir a comer", "Salida comida", "Fin jornada"]
# ---------------------------------

def init_db():
    """Crea la tabla de fichajes si no existe."""
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fichajes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    hora TEXT NOT NULL
                )
            """)
            conn.commit()
    except sqlite3.Error as e:
        # Relanza una excepción para que main.py pueda manejarla
        raise RuntimeError(f"Error al inicializar la base de datos: {e}")

def registrar_fichaje(tipo: str):
    """Registra un fichaje con la hora actual, aplicando la lógica de flujo estricta."""
    ahora = datetime.now()
    fecha = ahora.strftime("%Y-%m-%d")
    hora = ahora.strftime("%H:%M:%S")
    
    fichajes_existentes = {t for t, _ in obtener_fichajes_del_dia(fecha)}

    # --- Lógica de Flujo Estricta (Mantenida) ---
    if tipo == "Entrada":
        if "Entrada" in fichajes_existentes:
            raise Exception("Ya existe una Entrada registrada.")
        if fichajes_existentes:
            # Esta validación es clave para evitar dobles fichajes después de un Fin jornada
            raise Exception("No se puede registrar Entrada. Ya existen otros fichajes.") 

    elif tipo == "Ir a comer":
        if "Ir a comer" in fichajes_existentes:
            raise Exception("Ya se ha registrado 'Ir a comer'.")
        if "Entrada" not in fichajes_existentes:
            raise Exception("No puedes registrar 'Ir a comer' sin haber fichado la Entrada.")
        if "Fin jornada" in fichajes_existentes:
            raise Exception("La jornada ha finalizado. No se puede fichar 'Ir a comer'.")

    elif tipo == "Salida comida":
        if "Salida comida" in fichajes_existentes:
            raise Exception("Ya se ha registrado 'Salida comida'.")
        if "Ir a comer" not in fichajes_existentes:
            raise Exception("No puedes registrar 'Salida comida' sin haber fichado 'Ir a comer'.")
        if "Fin jornada" in fichajes_existentes:
            raise Exception("La jornada ha finalizado.")

    elif tipo == "Fin jornada":
        if "Fin jornada" in fichajes_existentes:
            raise Exception("Ya se ha registrado 'Fin jornada'.")
        if "Entrada" not in fichajes_existentes:
            raise Exception("No puedes registrar 'Fin jornada' sin haber fichado la Entrada.")
        if "Ir a comer" in fichajes_existentes and "Salida comida" not in fichajes_existentes:
             # Este control es vital: no se puede salir si el descanso sigue abierto
             raise Exception("Debes registrar 'Salida comida' para cerrar el descanso antes de 'Fin jornada'.")
    
    else:
        raise ValueError(f"Tipo de fichaje desconocido: {tipo}")

    # --- Registro en DB ---
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO fichajes (fecha, tipo, hora) VALUES (?, ?, ?)",
                (fecha, tipo, hora)
            )
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error de base de datos al registrar {tipo}: {e}")


def registrar_fichaje_manual(fecha: str, tipo: str, hora_str: str):
    """Guarda o actualiza un fichaje manual, aplicando la lógica de flujo solo para INSERCIONES."""
    if not hora_str or len(hora_str) != 5:
        raise ValueError("La hora debe tener el formato HH:MM.")
        
    hora_db = hora_str + ":00"

    try:
        with conectar() as conn:
            cursor = conn.cursor()
            
            # 1. Chequear si el registro ya existe (para UPDATE vs INSERT)
            cursor.execute("SELECT id FROM fichajes WHERE fecha=? AND tipo=?", (fecha, tipo))
            result = cursor.fetchone()
            
            # Si NO es una actualización, aplicamos la validación estricta de flujo
            if not result: 
                fichajes_existentes = {t for t, _ in obtener_fichajes_del_dia(fecha)}
                
                # --- Lógica de Flujo Estricta para INSERT manual ---
                # Esta validación es la misma que en registrar_fichaje, pero solo para INSERTS
                if tipo == "Entrada" and "Entrada" in fichajes_existentes:
                    raise Exception("Ya existe una Entrada. Usa la tabla para actualizar la hora.")
                elif tipo == "Ir a comer" and "Entrada" not in fichajes_existentes:
                    raise Exception("No puedes registrar 'Ir a comer' sin haber fichado la Entrada.")
                elif tipo == "Salida comida" and "Ir a comer" not in fichajes_existentes:
                    raise Exception("No puedes registrar 'Salida comida' sin haber fichado 'Ir a comer'.")
                # Permitimos Fin jornada sin Salida Comida en manual para flexibilidad.

            # --- Inserción/Actualización ---
            if result:
                # Actualizar
                cursor.execute("UPDATE fichajes SET hora=? WHERE id=?", (hora_db, result[0]))
            else:
                # Insertar
                cursor.execute("INSERT INTO fichajes (fecha, tipo, hora) VALUES (?, ?, ?)", 
                               (fecha, tipo, hora_db))
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error de base de datos al registrar manualmente {tipo}: {e}")

def obtener_fichajes_del_dia(fecha: str):
    """Devuelve los fichajes de un día específico, ordenados por hora."""
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT tipo, hora FROM fichajes WHERE fecha = ? ORDER BY hora",
                (fecha,)
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error de base de datos al obtener fichajes: {e}")


def calcular_horas_trabajadas(fecha: str):
    """
    Calcula las horas trabajadas en un día. 
    (Mejorado: Usa datetime.combine para cálculos de timedelta más robustos)
    """
    fichajes = obtener_fichajes_del_dia(fecha)
    
    # Crear una fecha base arbitraria (la fecha del fichaje) para poder usar objetos datetime y restar.
    try:
        fecha_base = datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        return 0.0 # Fecha inválida

    tiempos = {}
    
    for tipo, hora_str in fichajes:
        try:
            # Parsear la hora y combinarla con la fecha base
            hora_dt = datetime.strptime(hora_str, "%H:%M:%S").time()
            tiempos[tipo] = datetime.combine(fecha_base, hora_dt) 
        except ValueError:
            # Si el formato es solo HH:MM (no debería pasar si se registra con :00)
            try:
                hora_dt = datetime.strptime(hora_str[:5], "%H:%M").time()
                tiempos[tipo] = datetime.combine(fecha_base, hora_dt) 
            except ValueError:
                continue

    horas = timedelta()

    # Cálculo Total de Horas Trabajadas
    if "Entrada" in tiempos and "Fin jornada" in tiempos:
        
        total_jornada = tiempos["Fin jornada"] - tiempos["Entrada"]
        tiempo_comida = timedelta()
        
        # Calcular el descanso si hay fichajes de comida válidos
        if "Ir a comer" in tiempos and "Salida comida" in tiempos:
            # Se asume que Salida comida debe ser posterior a Ir a comer
            if tiempos["Salida comida"] > tiempos["Ir a comer"]:
                tiempo_comida = tiempos["Salida comida"] - tiempos["Ir a comer"]
        
        # Horas trabajadas = Total - Descanso
        horas = total_jornada - tiempo_comida
    
    # Asegurar que no devolvemos un tiempo negativo (por si hay fichajes cruzados)
    if horas.total_seconds() < 0:
        return 0.0

    return round(horas.total_seconds() / 3600, 2)