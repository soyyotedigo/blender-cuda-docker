import sys
import os

# Asegurar que podemos importar los módulos hermanos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide2.QtWidgets import QApplication
from mvc.controllers.main_controller import MainController
from PySide2.QtWidgets import QMainWindow

def main():
    app = QApplication(sys.argv)
    
    # Configurar fusión para que se vea bien en todos los OS
    app.setStyle("Fusion")
    
    controller = MainController()
    controller.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
