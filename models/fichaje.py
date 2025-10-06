from datetime import datetime, timedelta, date, time # CORREGIDO: Añadido date, time para tipado (Error 12)
from db import connect_db # CORREGIDO: 'conectar' -> 'connect_db' (Error 11)
import sqlite3
from typing import List, Tuple, Optional

# --- CENTRALIZED CONSTANTS --- 
PUNCH_TYPES = ["Entrada", "Ir a comer", "Salida comida", "Fin jornada"]
# ---------------------------------

def init_db():
    """Crea la tabla de fichajes si no existe."""
    try:
        with connect_db() as conn: # Usar connect_db
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
        raise RuntimeError(f"Error al inicializar la base de datos: {e}")

def register_punch(punch_type: str):
    """Registra un fichaje con la hora actual, aplicando la lógica de flujo estricta."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    hour_str = now.strftime("%H:%M:%S")
    
    existing_punches = {t for t, _ in get_daily_punches(date_str)}

    # --- Lógica de Flujo Estricta (Mantenida) ---
    if punch_type == "Entrada":
        if "Entrada" in existing_punches:
            raise Exception("Ya existe una Entrada registrada.")
        if existing_punches:
            raise Exception("Debe ser el primer fichaje del día.")
    
    elif punch_type == "Ir a comer":
        if "Entrada" not in existing_punches:
            raise Exception("Debe fichar Entrada primero.")
        if "Ir a comer" in existing_punches:
            raise Exception("Ya ha fichado Ir a comer.")
        if "Salida comida" in existing_punches:
            raise Exception("Ya ha terminado su descanso.")
        if "Fin jornada" in existing_punches:
            raise Exception("La jornada ya ha terminado.")

    elif punch_type == "Salida comida":
        if "Ir a comer" not in existing_punches:
            raise Exception("Debe fichar Ir a comer primero.")
        if "Salida comida" in existing_punches:
            raise Exception("Ya ha fichado Salida comida.")
        if "Fin jornada" in existing_punches:
            raise Exception("La jornada ya ha terminado.")
            
    elif punch_type == "Fin jornada":
        if "Entrada" not in existing_punches:
            raise Exception("Debe fichar Entrada primero.")
        if "Fin jornada" in existing_punches:
            raise Exception("La jornada ya ha finalizado.")
        if "Ir a comer" in existing_punches and "Salida comida" not in existing_punches:
             raise Exception("Debe fichar Salida comida antes de finalizar la jornada.")

    # --- DB Registration ---
    try:
        with connect_db() as conn: # Usar connect_db
            cursor = conn.cursor()
            cursor.execute("INSERT INTO fichajes (fecha, tipo, hora) VALUES (?, ?, ?)", 
                           (date_str, punch_type, hour_str))
            conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Error al registrar fichaje en DB: {e}")

def get_daily_punches(date_str: str) -> List[Tuple[str, str]]:
    """Retrieves all punches for a specific date (type, hour)."""
    punches = []
    try:
        with connect_db() as conn: # Usar connect_db
            cursor = conn.cursor()
            cursor.execute("SELECT tipo, hora FROM fichajes WHERE fecha=? ORDER BY hora", (date_str,))
            punches = cursor.fetchall()
    except sqlite3.Error:
        return []
    return punches

def register_manual_punch(date_str: str, punch_type: str, hour_str: str):
    """Registers a manual punch for a specific date and time, without flow logic."""
    try:
        with connect_db() as conn: # Usar connect_db
            cursor = conn.cursor()
            if len(hour_str) == 5:
                hour_str += ":00"
                
            cursor.execute("SELECT id FROM fichajes WHERE fecha=? AND tipo=?", (date_str, punch_type))
            if cursor.fetchone():
                raise Exception(f"Ya existe un fichaje de tipo '{punch_type}' para la fecha {date_str}. Elimínelo primero.")

            cursor.execute("INSERT INTO fichajes (fecha, tipo, hora) VALUES (?, ?, ?)", 
                           (date_str, punch_type, hour_str))
            conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Error al registrar fichaje manual: {e}")

def calculate_worked_hours(fichajes: List[Tuple[str, str]]) -> timedelta:
    """Calculates the total worked time based on a list of punches."""
    if not fichajes:
        return timedelta()
        
    try:
        fecha_base: date = datetime.strptime(fichajes[0][0], "%Y-%m-%d").date()
    except ValueError:
        fecha_base: date = datetime.now().date()

    tiempos = {}
    
    for tipo, hora_str in fichajes:
        try:
            # Uso explícito de 'time' (Pylance fix)
            hora_dt: time = datetime.strptime(hora_str, "%H:%M:%S").time() 
            tiempos[tipo] = datetime.combine(fecha_base, hora_dt) 
        except ValueError:
            try:
                # Uso explícito de 'time' (Pylance fix)
                hora_dt: time = datetime.strptime(hora_str[:5], "%H:%M").time() 
                tiempos[tipo] = datetime.combine(fecha_base, hora_dt) 
            except ValueError:
                continue

    hours = timedelta()

    # Total Worked Hours Calculation
    if "Entrada" in tiempos and "Fin jornada" in tiempos:
        
        total_jornada = tiempos["Fin jornada"] - tiempos["Entrada"]
        tiempo_comida = timedelta()
        
        if "Ir a comer" in tiempos and "Salida comida" in tiempos:
            if tiempos["Salida comida"] > tiempos["Ir a comer"]:
                tiempo_comida = tiempos["Salida comida"] - tiempos["Ir a comer"]
        
        hours = total_jornada - tiempo_comida
    
    if hours.total_seconds() < 0:
        return timedelta()

    return hours
    
def delete_punch_by_date_type(date_str: str, punch_type: str):
    """Deletes a specific punch by date and type."""
    try:
        with connect_db() as conn: # Usar connect_db
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fichajes WHERE fecha=? AND tipo=? ORDER BY hora DESC LIMIT 1", 
                           (date_str, punch_type))
            conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Error al eliminar fichaje de DB: {e}")