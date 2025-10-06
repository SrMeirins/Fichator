# 🚀 App Fichaje Unificada: Control Horario Eficaz

Aplicación de escritorio multiplataforma (Python + PySide6) diseñada para simplificar la gestión del tiempo laboral diario y semanal. Registra, visualiza y gestiona tu horario con una interfaz moderna.

## ✨ Características Destacadas

| Característica | Descripción |
| :--- | :--- |
| **Control en Tiempo Real** | Botones de fichaje con lógica de estado para asegurar un flujo de trabajo correcto: **Entrada**, **Pausa** (Comida), y **Fin de jornada**. |
| **Gestión Semanal** | Historial detallado en tabla (`Lunes` a `Viernes`) con funcionalidad de **edición manual** de fichajes. |
| **Visualización Gráfica** | Gráficos de **Matplotlib** para análisis de horas diarias y una **Barra de Progreso** para monitorear el objetivo de horas semanales. |
| **Almacenamiento Local** | Utiliza una base de datos **SQLite (`fichajes.db`)** para almacenar todos los registros de forma segura en tu máquina. |

-----

## 💻 Instalación y Ejecución Rápida

Sigue estos pasos para poner la aplicación en marcha en tu entorno local.

### 1\. Requisitos Previos

Necesitas tener **Python 3.8+** instalado en tu sistema.

### 2\. Preparación del Código Fuente

Clona el repositorio en tu máquina y navega al directorio del proyecto.

```bash
git clone https://github.com/SrMeirins/Fichator.git 
cd Fichator
```

### 3\. Configuración del Entorno Virtual (Recomendado)

Es altamente recomendable usar un entorno virtual para aislar las dependencias de la aplicación.

```bash
# 3.1 Crear el entorno virtual
python3 -m venv venv

# 3.2 Activar el entorno
# 🍏 Linux / macOS:
source venv/bin/activate
# 🪟 Windows (CMD/PowerShell):
.\venv\Scripts\activate
```

### 4\. Instalación de Dependencias

Instala todas las librerías necesarias (incluyendo PySide6 y Matplotlib) desde el archivo `requirements.txt`.

```bash
(venv) pip install -r requirements.txt
```
### 5\. Iniciar la Aplicación

Ejecuta el archivo principal para iniciar la interfaz gráfica.

```bash
(venv) python3 main.py
```

La aplicación se abrirá en modo maximizado y creará la base de datos `fichajes.db` automáticamente al iniciar si no existe.

