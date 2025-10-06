# main.py

import sys
# Aseguramos que QApplication esté disponible para el type hint
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMessageBox 
from PySide6.QtCore import QCoreApplication 
from gui.app_unificada import UnifiedPunchApp 
from models.fichaje import init_db 
import os 
from typing import Optional 

# CORRECCIÓN: El tipo de 'app' es QApplication, ya que setStyleSheet NO está en QCoreApplication.
def load_stylesheet(app: QApplication, path: str) -> bool:
    """
    Carga un archivo QSS y lo aplica. Imprime la ruta usada o el error.
    Retorna True si la carga fue exitosa.
    """
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                app.setStyleSheet(f.read())
            print(f"✅ Estilos QSS aplicados correctamente desde: {path}", file=sys.stdout)
            return True
        except Exception as e:
            print(f"❌ ERROR: Fallo al leer o aplicar estilos QSS desde {path}: {e}", file=sys.stderr) 
            return False
    else:
        # No imprime si el archivo no existe, para que pueda intentar otra ruta
        return False

class FichajeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Punch App")
        
        try:
            # Asumiendo que init_db usa el nuevo connect_db
            init_db() 
        except Exception as e:
            QMessageBox.critical(self, "Fatal DB Error", 
                                 f"No se pudo inicializar la base de datos. La aplicación se cerrará.\nError: {e}")
            sys.exit(1)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.app_unificada = UnifiedPunchApp()
        layout.addWidget(self.app_unificada)
        
        self.resize(1000, 700)
        self.showMaximized() 


if __name__ == "__main__":
    
    # Lógica robusta para inicializar la aplicación GUI
    app_instance = QCoreApplication.instance()
    if not isinstance(app_instance, QApplication):
        app = QApplication(sys.argv)
    else:
        app = app_instance
    
    if not isinstance(app, QApplication):
         print("Fatal Error: Could not start QApplication.", file=sys.stderr)
         sys.exit(1)

    # --- Lógica de Búsqueda de Archivo QSS ---
    base_dir = os.path.dirname(os.path.abspath(__file__)) # Usamos abspath para mayor seguridad
    
    # Definimos las rutas comunes donde podría estar el archivo QSS:
    # 1. En la subcarpeta 'gui' con el nombre 'estilos.qss'
    qss_path_1 = os.path.join(base_dir, "gui", "estilos.qss")
    # 2. En la subcarpeta 'gui' con el nombre 'styles.qss'
    qss_path_2 = os.path.join(base_dir, "gui", "styles.qss")
    # 3. Directamente en la raíz del proyecto (junto a main.py) con el nombre 'estilos.qss'
    qss_path_3 = os.path.join(base_dir, "estilos.qss") 
    # 4. Directamente en la raíz del proyecto (junto a main.py) con el nombre 'styles.qss'
    qss_path_4 = os.path.join(base_dir, "styles.qss") 
    
    paths_to_try = [qss_path_1, qss_path_2, qss_path_3, qss_path_4]
    
    styles_loaded = False
    for path in paths_to_try:
        if load_stylesheet(app, path):
            styles_loaded = True
            break
            
    if not styles_loaded:
        print("ADVERTENCIA: No se pudo encontrar ningún archivo QSS. Verifique que 'estilos.qss' o 'styles.qss' esté en la carpeta 'gui' o en la raíz.", file=sys.stderr)

    main_window = FichajeApp()
    
    sys.exit(app.exec())