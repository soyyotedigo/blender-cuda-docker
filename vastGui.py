import sys
import json
import subprocess
import random
from datetime import datetime

try:
    from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                   QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                   QTableWidget, QTableWidgetItem, QHeaderView, 
                                   QComboBox, QTextEdit, QGroupBox, QFormLayout,
                                   QMessageBox, QSplitter, QProgressBar)
    from PySide2.QtCore import Qt, QThread, Signal, QTimer
    from PySide2.QtGui import QColor, QFont, QIcon, QPalette
except ImportError:
    print("Error: PySide2 no está instalado. Ejecuta 'pip install PySide2'")
    sys.exit(1)

# --- Estilos CSS (QSS) para Tema Oscuro ---
DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}
QWidget {
    background-color: #1e1e1e;
    color: #f0f0f0;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
}
QGroupBox {
    border: 1px solid #3d3d3d;
    border-radius: 5px;
    margin-top: 1.5em;
    font-weight: bold;
    color: #4CAF50;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}
QLineEdit, QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    padding: 5px;
    color: #ffffff;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #4CAF50;
}
QPushButton {
    background-color: #0D47A1;
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 4px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1565C0;
}
QPushButton:pressed {
    background-color: #0D47A1;
}
QPushButton#rentButton {
    background-color: #2E7D32;
    font-size: 16px;
    padding: 10px;
}
QPushButton#rentButton:hover {
    background-color: #388E3C;
}
QTableWidget {
    background-color: #252526;
    gridline-color: #3d3d3d;
    border: 1px solid #3d3d3d;
}
QTableWidget::item:selected {
    background-color: #0D47A1;
}
QHeaderView::section {
    background-color: #333333;
    padding: 5px;
    border: 1px solid #3d3d3d;
    font-weight: bold;
}
QTextEdit {
    background-color: #121212;
    color: #00ff00;
    font-family: 'Consolas', 'Courier New', monospace;
    border: 1px solid #3d3d3d;
}
QProgressBar {
    border: 1px solid #3d3d3d;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #4CAF50;
}
"""

# --- Lógica de Vast.ai (Wrapper) ---

class VastWorker(QThread):
    """Hilo secundario para ejecutar comandos de vastai sin congelar la UI"""
    data_ready = Signal(list)
    log_message = Signal(str)
    error_occurred = Signal(str)
    finished_action = Signal(str)

    def __init__(self, mode, **kwargs):
        super().__init__()
        self.mode = mode  # 'search' o 'rent'
        self.kwargs = kwargs
        self.use_mock = False

    def run(self):
        if self.mode == 'search':
            self.search_offers()
        elif self.mode == 'rent':
            self.rent_instance()

    def check_vast_installed(self):
        """Verifica si vastai está en el PATH"""
        try:
            subprocess.check_call(["vastai", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def search_offers(self):
        gpu_name = self.kwargs.get('gpu_name', '')
        max_price = self.kwargs.get('max_price', 10.0)
        disk_space = self.kwargs.get('disk_space', 10)

        # Construir query para vastai
        query = f"dph < {max_price} verified=true disk_space > {disk_space}"
        if gpu_name and gpu_name != "Cualquiera":
            query += f" gpu_name={gpu_name}"

        self.log_message.emit(f"[*] Buscando ofertas con query: {query}")

        if not self.check_vast_installed():
            self.log_message.emit("[!] Vast.ai CLI no detectada o no configurada. Usando MOCK DATA.")
            self.use_mock = True
        
        if self.use_mock:
            # Generar datos falsos para demostración
            self.msleep(1000) # Simular delay de red
            mock_results = []
            gpu_types = [gpu_name] if gpu_name != "Cualquiera" else ["RTX 4090", "RTX 3090", "A100", "A6000"]
            for i in range(15):
                g = random.choice(gpu_types)
                price = round(random.uniform(0.2, 2.5), 3)
                mock_results.append({
                    "id": random.randint(1000000, 9999999),
                    "gpu_name": g,
                    "num_gpus": random.randint(1, 4),
                    "dph_total": price,
                    "dlperf": round(random.uniform(15, 100), 1),
                    "reliability2": round(random.uniform(0.8, 1.0), 2),
                    "inet_down": round(random.uniform(100, 1000), 1)
                })
            self.data_ready.emit(mock_results)
            self.log_message.emit(f"[+] Búsqueda completada (Mock). {len(mock_results)} máquinas encontradas.")
            return

        # Ejecución Real
        try:
            cmd = ["vastai", "search", "offers", query, "--raw"]
            result = subprocess.check_output(cmd).decode('utf-8')
            data = json.loads(result)
            self.data_ready.emit(data)
            self.log_message.emit(f"[+] Búsqueda completada. {len(data)} máquinas encontradas.")
        except Exception as e:
            self.error_occurred.emit(f"Error ejecutando vastai search: {str(e)}")

    def rent_instance(self):
        instance_id = self.kwargs.get('id')
        image = self.kwargs.get('image')
        disk = self.kwargs.get('disk')
        onstart = self.kwargs.get('onstart')

        self.log_message.emit(f"[*] Intentando alquilar ID: {instance_id} con imagen: {image}...")

        if self.use_mock or not self.check_vast_installed():
            self.msleep(2000)
            self.log_message.emit(f"[MOCK] Instancia {instance_id} alquilada exitosamente.")
            self.log_message.emit(f"[MOCK] Ejecutando script on-start: {onstart}")
            self.finished_action.emit("MOCK_SUCCESS")
            return

        # Ejecución Real
        try:
            # Comando: vastai create instance <id> --image <image> --disk <disk> --onstart <cmd>
            cmd = ["vastai", "create", "instance", str(instance_id), "--image", image, "--disk", str(disk)]
            
            if onstart:
                # Nota: pasar scripts complejos por CLI puede ser delicado con las comillas
                cmd.extend(["--onstart", onstart])

            result = subprocess.check_output(cmd).decode('utf-8')
            
            if "success" in result.lower() or "id" in result.lower():
                self.log_message.emit(f"[+] Instancia creada. Respuesta: {result}")
                self.finished_action.emit("SUCCESS")
            else:
                self.error_occurred.emit(f"Respuesta inesperada: {result}")
                
        except Exception as e:
            self.error_occurred.emit(f"Error al alquilar: {str(e)}")


# --- Interfaz Gráfica Principal ---

class VastGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vast.ai Render Manager (PySide2)")
        self.resize(1200, 800)
        self.setStyleSheet(DARK_STYLESHEET)
        
        # Variables de estado
        self.selected_machine_id = None
        self.worker = None

        self.init_ui()
        self.append_log("Sistema iniciado. Listo para buscar máquinas.")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # === Panel Izquierdo (Controles y Logs) ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(400)

        # 1. Filtros de Búsqueda
        filter_group = QGroupBox("1. Configuración de Búsqueda")
        filter_layout = QFormLayout()

        self.gpu_combo = QComboBox()
        self.gpu_combo.addItems(["Cualquiera", "RTX 4090", "RTX 3090", "A6000", "A100", "A40", "RTX A5000"])
        
        self.price_input = QLineEdit("2.5")
        self.price_input.setPlaceholderText("USD/Hora Máx")
        
        self.disk_input = QLineEdit("20")
        self.disk_input.setPlaceholderText("GB Espacio")

        filter_layout.addRow("GPU Modelo:", self.gpu_combo)
        filter_layout.addRow("Precio Máx ($/hr):", self.price_input)
        filter_layout.addRow("Espacio Disco (GB):", self.disk_input)

        self.search_btn = QPushButton("Buscar Disponibles")
        self.search_btn.setIcon(QIcon.fromTheme("system-search"))
        self.search_btn.clicked.connect(self.start_search)
        
        filter_layout.addRow(self.search_btn)
        filter_group.setLayout(filter_layout)

        # 2. Configuración de Render
        render_group = QGroupBox("3. Configuración del Render")
        render_layout = QFormLayout()

        self.image_input = QLineEdit("pytorch/pytorch")
        self.image_input.setPlaceholderText("Ej: blender/blender:latest")
        self.image_input.setToolTip("Imagen Docker a utilizar")

        self.onstart_input = QLineEdit("touch /root/started")
        self.onstart_input.setPlaceholderText("Bash script on-start")
        
        self.args_input = QLineEdit("-p 8080:8080")
        self.args_input.setPlaceholderText("Argumentos docker run")

        render_layout.addRow("Docker Image:", self.image_input)
        render_layout.addRow("On-Start Cmd:", self.onstart_input)
        render_layout.addRow("Launch Args:", self.args_input)

        self.rent_btn = QPushButton("ALQUILAR Y RENDERIZAR")
        self.rent_btn.setObjectName("rentButton")
        self.rent_btn.setEnabled(False)
        self.rent_btn.clicked.connect(self.start_rent)

        render_layout.addRow(self.rent_btn)
        render_group.setLayout(render_layout)

        # 3. Consola de Logs
        log_group = QGroupBox("Logs del Sistema")
        log_layout = QVBoxLayout()
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        log_layout.addWidget(self.log_console)
        log_group.setLayout(log_layout)

        # Agregar widgets al layout izquierdo
        left_layout.addWidget(filter_group)
        left_layout.addWidget(render_group)
        left_layout.addWidget(log_group)

        # === Panel Derecho (Resultados) ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.result_label = QLabel("2. Selecciona una máquina de la lista:")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        
        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "GPU", "Cant.", "Precio/Hr", "DLPerf", "Fiabilidad"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        right_layout.addWidget(self.result_label)
        right_layout.addWidget(self.table)

        # Barra de progreso (indeterminada)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        right_layout.addWidget(self.progress)

        # Unir paneles
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    # --- Funciones de UI ---

    def append_log(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_console.append(f"[{timestamp}] {text}")
        # Auto scroll
        sb = self.log_console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_selection_changed(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            machine_id = self.table.item(row, 0).text()
            gpu = self.table.item(row, 1).text()
            price = self.table.item(row, 3).text()
            
            self.selected_machine_id = machine_id
            self.result_label.setText(f"Seleccionado: ID {machine_id} ({gpu} a ${price}/hr)")
            self.rent_btn.setEnabled(True)
            self.rent_btn.setText(f"ALQUILAR ID {machine_id}")
        else:
            self.selected_machine_id = None
            self.rent_btn.setEnabled(False)
            self.rent_btn.setText("ALQUILAR Y RENDERIZAR")

    # --- Lógica de Negocio ---

    def start_search(self):
        self.table.setRowCount(0)
        self.rent_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.progress.setRange(0, 0) # Modo indeterminado
        self.progress.show()

        gpu = self.gpu_combo.currentText()
        try:
            price = float(self.price_input.text())
            disk = float(self.disk_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "El precio y el disco deben ser números válidos.")
            self.search_btn.setEnabled(True)
            self.progress.hide()
            return

        # Crear e iniciar hilo
        self.worker = VastWorker(mode='search', gpu_name=gpu, max_price=price, disk_space=disk)
        self.worker.data_ready.connect(self.populate_table)
        self.worker.log_message.connect(self.append_log)
        self.worker.error_occurred.connect(lambda err: self.append_log(f"ERROR: {err}"))
        self.worker.finished.connect(self.search_finished)
        self.worker.start()

    def populate_table(self, data):
        self.table.setRowCount(len(data))
        for row_idx, machine in enumerate(data):
            # Parsear datos (depende de la estructura de vastai)
            m_id = str(machine.get('id', 'N/A'))
            m_gpu = str(machine.get('gpu_name', 'Unknown'))
            m_count = str(machine.get('num_gpus', 1))
            m_price = f"{machine.get('dph_total', 0.0):.3f}"
            m_dlperf = str(machine.get('dlperf', 0))
            
            # Fiabilidad (formatear porcentaje)
            rel = machine.get('reliability2', 0)
            m_rel = f"{rel*100:.1f}%" if rel else "N/A"

            self.table.setItem(row_idx, 0, QTableWidgetItem(m_id))
            self.table.setItem(row_idx, 1, QTableWidgetItem(m_gpu))
            self.table.setItem(row_idx, 2, QTableWidgetItem(m_count))
            self.table.setItem(row_idx, 3, QTableWidgetItem(m_price))
            self.table.setItem(row_idx, 4, QTableWidgetItem(m_dlperf))
            self.table.setItem(row_idx, 5, QTableWidgetItem(m_rel))

    def search_finished(self):
        self.search_btn.setEnabled(True)
        self.progress.hide()

    def start_rent(self):
        if not self.selected_machine_id:
            return

        image = self.image_input.text()
        if not image:
            QMessageBox.warning(self, "Falta Imagen", "Debes especificar una imagen de Docker.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar Alquiler", 
            f"¿Estás seguro de alquilar la máquina {self.selected_machine_id}?\nEsto comenzará a cobrar créditos de tu cuenta Vast.ai.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.No:
            return

        self.rent_btn.setEnabled(False)
        self.progress.setRange(0, 0)
        self.progress.show()

        try:
            disk = float(self.disk_input.text())
        except: 
            disk = 10.0

        self.worker = VastWorker(
            mode='rent', 
            id=self.selected_machine_id, 
            image=image, 
            disk=disk, 
            onstart=self.onstart_input.text()
        )
        self.worker.log_message.connect(self.append_log)
        self.worker.error_occurred.connect(lambda err: self.append_log(f"ERROR ALQUILER: {err}"))
        self.worker.finished_action.connect(self.rent_finished)
        self.worker.finished.connect(lambda: self.progress.hide())
        self.worker.start()

    def rent_finished(self, status):
        self.rent_btn.setEnabled(True)
        if status in ["SUCCESS", "MOCK_SUCCESS"]:
            QMessageBox.information(self, "Éxito", f"Máquina desplegada correctamente.\nRevisa la consola o el dashboard web.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configurar fusión para que se vea bien en todos los OS
    app.setStyle("Fusion")
    
    window = VastGui()
    window.show()
    
    sys.exit(app.exec_())