# models/logica_contador.py

from datetime import datetime, timedelta, date, time # CORREGIDO: Añadido date, time para tipado (Errores 13, 14)
from typing import List, Tuple, Optional

def calculate_accumulated_time_and_state(punches: List[Tuple[str, str]]) -> Tuple[float, bool, Optional[datetime]]:
    """
    Calcula el tiempo acumulado de trabajo y determina si el contador debe estar activo.

    Args:
        punches (list): Lista de tuplas (tipo, hora_str) del día actual.

    Returns:
        tuple: (total_segundos_acumulados, esta_activo, hora_inicio_actividad_dt)
    """
    
    # Convierte los fichajes de string a objetos datetime
    fichajes_dt = []
    for tipo, hora_str in punches:
        try:
            # Uso explícito de 'date' y 'time' (Pylance fix)
            today: date = datetime.now().date()
            hora: time = datetime.strptime(hora_str, "%H:%M:%S").time()
            dt = datetime.combine(today, hora)
            fichajes_dt.append((tipo, dt))
        except ValueError:
            try:
                # Uso explícito de 'date' y 'time' (Pylance fix)
                today: date = datetime.now().date()
                hora: time = datetime.strptime(hora_str[:5], "%H:%M").time()
                dt = datetime.combine(today, hora)
                fichajes_dt.append((tipo, dt))
            except ValueError:
                continue

    fichajes_dt.sort(key=lambda x: x[1])
    
    total_segundos_acumulados = 0
    esta_activo = False
    hora_inicio_actividad_dt = None

    i = 0
    while i < len(fichajes_dt):
        tipo_actual, dt_actual = fichajes_dt[i]

        # 1. Entrada
        if tipo_actual == "Entrada":
            j = i + 1
            while j < len(fichajes_dt) and fichajes_dt[j][0] not in ["Ir a comer", "Fin jornada"]:
                j += 1
                
            if j < len(fichajes_dt):
                tipo_siguiente, dt_siguiente = fichajes_dt[j]
                total_segundos_acumulados += (dt_siguiente - dt_actual).total_seconds()
                esta_activo = False
                i = j
            else:
                esta_activo = True
                hora_inicio_actividad_dt = dt_actual
                i = len(fichajes_dt)
                break 

        # 2. Ir a comer
        elif tipo_actual == "Ir a comer":
            j = i + 1
            while j < len(fichajes_dt) and fichajes_dt[j][0] != "Salida comida":
                j += 1
                
            if j < len(fichajes_dt):
                tipo_siguiente, dt_siguiente = fichajes_dt[j]
                esta_activo = False
                i = j
            else:
                esta_activo = False
                i = len(fichajes_dt)
                break 

        # 3. Salida comida
        elif tipo_actual == "Salida comida":
            j = i + 1
            while j < len(fichajes_dt) and fichajes_dt[j][0] != "Fin jornada":
                j += 1
                
            if j < len(fichajes_dt):
                tipo_siguiente, dt_siguiente = fichajes_dt[j]
                total_segundos_acumulados += (dt_siguiente - dt_actual).total_seconds()
                esta_activo = False
                i = len(fichajes_dt)
                break 
            else:
                esta_activo = True
                hora_inicio_actividad_dt = dt_actual
                i = len(fichajes_dt)
                break
                
        i += 1
        
    # Si el contador está activo, calcular el tiempo hasta ahora
    if esta_activo and hora_inicio_actividad_dt:
        tiempo_actual = datetime.now()
        tiempo_desde_inicio = (tiempo_actual - hora_inicio_actividad_dt).total_seconds()
        total_segundos_acumulados += tiempo_desde_inicio
        
    return total_segundos_acumulados, esta_activo, hora_inicio_actividad_dt