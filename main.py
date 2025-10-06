import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMessageBox
from gui.app_unificada import AppUnificada # Asume que esta es la ruta correcta
from models.fichaje import init_db 
import os 
from pathlib import Path

# --- RUTA CORREGIDA PARA ENTORNO DE DESARROLLO ---
# Esto funciona cuando se ejecuta 'python3 main.py' desde la raíz del proyecto.
BASE_DIR = Path(__file__).resolve().parent

class FichajeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App de Fichaje")
        
        # Inicializar la base de datos y manejar errores críticos
        try:
            init_db() 
        except Exception as e:
            QMessageBox.critical(self, "Error Fatal de DB", 
                                 f"No se pudo inicializar la base de datos. La aplicación se cerrará.\nError: {e}")
            sys.exit(1)

        # Crear el layout y añadir el widget unificado
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Usamos la nueva clase que contiene toda la funcionalidad
        self.app_unificada = AppUnificada()
        layout.addWidget(self.app_unificada)
        
        # Al iniciar, la ventana principal será maximizada
        self.resize(1000, 700)
        self.showMaximized()


def main():
    """Función de entrada principal para ejecución directa."""
    app = QApplication(sys.argv)
    
    # Lógica de carga de estilos desde la carpeta 'gui'
    qss_path = BASE_DIR / "gui" / "estilos.qss"
    
    if qss_path.exists():
        try:
            with open(qss_path, "r") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            # Mensaje de advertencia en caso de fallo al cargar el estilo
            print(f"Advertencia: No se pudo cargar estilos.qss. Error: {e}", file=sys.stderr)
            
    window = FichajeApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
