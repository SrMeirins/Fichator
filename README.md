# App Fichaje Unificada

Aplicación de escritorio multiplataforma (Python + PySide6) para registrar y gestionar el horario laboral diario y semanal.

## Características Principales

* **Fichaje Rápido:** Botones funcionales para Entrada, Pausa (Comida) y Fin de jornada, con lógica de estado para habilitar/deshabilitar botones.
* **Gestión Semanal:** Historial en tabla de Lunes a Viernes con edición manual de fichajes.
* **Visualización:** Gráfico de Matplotlib para horas trabajadas por día y barra de progreso del objetivo semanal.
* **Almacenamiento:** Utiliza una base de datos SQLite (`fichajes.db`) para almacenar los registros de fichaje de forma local.

## Cómo Instalar y Ejecutar (Entorno de Desarrollo)

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://www.youtube.com/watch?v=eQMcIGVc8N0](https://www.youtube.com/watch?v=eQMcIGVc8N0)
    cd [nombre-del-repositorio]
    ```

2.  **Crear y activar un entorno virtual (Recomendado):**
    ```bash
    python -m venv venv
    # En Linux/macOS
    source venv/bin/activate
    # En Windows
    venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecutar la aplicación:**
    ```bash
    python main.py
    ```