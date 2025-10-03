import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMessageBox
from gui.app_unificada import AppUnificada # <--- NUEVO NOMBRE
from models.fichaje import init_db 
import os 

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
        
        # Al iniciar, la ventana principal será maximizada (o un buen tamaño inicial)
        self.resize(1000, 700)
        self.showMaximized() # <--- MEJORA: Maximizar al inicio


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    qss_path = os.path.join(os.path.dirname(__file__), "gui", "estilos.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    ventana = FichajeApp()
    ventana.show()
    sys.exit(app.exec())