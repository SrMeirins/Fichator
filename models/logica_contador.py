# models/logica_contador.py

from datetime import datetime, timedelta

def calcular_tiempo_acumulado_y_estado(fichajes):
    """
    Calcula el tiempo acumulado de trabajo y determina si el contador debe estar activo.

    Args:
        fichajes (list): Lista de tuplas (tipo, hora_str) del día actual.

    Returns:
        tuple: (total_segundos_acumulados, esta_activo, hora_inicio_actividad_dt)
    """
    
    # Convierte los fichajes de string a objetos datetime
    fichajes_dt = []
    for tipo, hora_str in fichajes:
        try:
            # Asumimos que la fecha es la de hoy
            hoy = datetime.now().date()
            hora = datetime.strptime(hora_str, "%H:%M:%S").time()
            dt = datetime.combine(hoy, hora)
            fichajes_dt.append((tipo, dt))
        except ValueError:
            # Si el formato es solo H:M
            try:
                hoy = datetime.now().date()
                hora = datetime.strptime(hora_str[:5], "%H:%M").time()
                dt = datetime.combine(hoy, hora)
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

        if tipo_actual == "Entrada":
            
            # Buscar el siguiente evento: Ir a comer o Fin jornada
            j = i + 1
            while j < len(fichajes_dt) and fichajes_dt[j][0] not in ["Ir a comer", "Fin jornada"]:
                j += 1
                
            if j < len(fichajes_dt):
                tipo_siguiente, dt_siguiente = fichajes_dt[j]

                if tipo_siguiente == "Ir a comer":
                    # Sumar tiempo hasta la comida
                    total_segundos_acumulados += (dt_siguiente - dt_actual).total_seconds()
                    
                    # Ahora buscar el siguiente evento: Salida comida
                    k = j + 1
                    while k < len(fichajes_dt) and fichajes_dt[k][0] != "Salida comida":
                        k += 1

                    if k < len(fichajes_dt):
                        # Se encontró Salida comida. El ciclo debe continuar desde aquí.
                        i = k 
                        continue 
                    else:
                        # Ha fichado Ir a comer, pero no Salida comida. Está en pausa.
                        esta_activo = False
                        i = len(fichajes_dt) # Terminar
                        break 
                        
                elif tipo_siguiente == "Fin jornada":
                    # Sumar tiempo hasta el final
                    total_segundos_acumulados += (dt_siguiente - dt_actual).total_seconds()
                    esta_activo = False
                    i = len(fichajes_dt) # Terminar
                    break 
                    
            else:
                # Entrada es el último fichaje relevante. El contador debe estar activo.
                esta_activo = True
                hora_inicio_actividad_dt = dt_actual
                i = len(fichajes_dt) # Terminar
                break 

        elif tipo_actual == "Salida comida":
            # Buscar el siguiente evento: Fin jornada
            j = i + 1
            while j < len(fichajes_dt) and fichajes_dt[j][0] != "Fin jornada":
                j += 1
                
            if j < len(fichajes_dt):
                tipo_siguiente, dt_siguiente = fichajes_dt[j]
                
                # Sumar tiempo desde la vuelta de comer hasta el final
                total_segundos_acumulados += (dt_siguiente - dt_actual).total_seconds()
                esta_activo = False
                i = len(fichajes_dt) # Terminar
                break 
            else:
                # Salida comida es el último fichaje. El contador debe estar activo.
                esta_activo = True
                hora_inicio_actividad_dt = dt_actual
                i = len(fichajes_dt) # Terminar
                break
                
        i += 1
        
    # Si el contador está activo, el tiempo acumulado real debe calcularse desde el último fichaje relevante
    if esta_activo and hora_inicio_actividad_dt:
        tiempo_actual = datetime.now()
        tiempo_desde_inicio = (tiempo_actual - hora_inicio_actividad_dt).total_seconds()
        total_segundos_acumulados += tiempo_desde_inicio
        
    return total_segundos_acumulados, esta_activo, hora_inicio_actividad_dt