from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QComboBox, QTextEdit, QGroupBox, QFormLayout,
                               QMessageBox, QProgressBar)
from PySide2.QtCore import Signal
from PySide2.QtGui import QIcon
from datetime import datetime
from .styles import DARK_STYLESHEET

class VastGui(QMainWindow):
    # Signals to Controller
    search_requested = Signal(str, float, float) # gpu, price, disk
    rent_requested = Signal(str, str, float, str) # id, image, disk, onstart

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vast.ai Render Manager (MVC)")
        self.resize(1200, 800)
        self.setStyleSheet(DARK_STYLESHEET)
        
        self.selected_machine_id = None
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
        self.search_btn.clicked.connect(self.on_search_clicked)
        
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
        self.rent_btn.clicked.connect(self.on_rent_clicked)

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

    def append_log(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_console.append(f"[{timestamp}] {text}")
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

    def on_search_clicked(self):
        gpu = self.gpu_combo.currentText()
        try:
            price = float(self.price_input.text())
            disk = float(self.disk_input.text())
            self.search_requested.emit(gpu, price, disk)
        except ValueError:
            QMessageBox.warning(self, "Error", "El precio y el disco deben ser números válidos.")

    def on_rent_clicked(self):
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
        
        if confirm == QMessageBox.Yes:
            try:
                disk = float(self.disk_input.text())
            except: 
                disk = 10.0
            self.rent_requested.emit(self.selected_machine_id, image, disk, self.onstart_input.text())

    def set_loading(self, loading):
        if loading:
            self.search_btn.setEnabled(False)
            self.rent_btn.setEnabled(False)
            self.progress.setRange(0, 0)
            self.progress.show()
        else:
            self.search_btn.setEnabled(True)
            if self.selected_machine_id:
                self.rent_btn.setEnabled(True)
            self.progress.hide()

    def populate_table(self, data):
        self.table.setRowCount(len(data))
        for row_idx, machine in enumerate(data):
            m_id = str(machine.get('id', 'N/A'))
            m_gpu = str(machine.get('gpu_name', 'Unknown'))
            m_count = str(machine.get('num_gpus', 1))
            m_price = f"{machine.get('dph_total', 0.0):.3f}"
            m_dlperf = str(machine.get('dlperf', 0))
            rel = machine.get('reliability2', 0)
            m_rel = f"{rel*100:.1f}%" if rel else "N/A"

            self.table.setItem(row_idx, 0, QTableWidgetItem(m_id))
            self.table.setItem(row_idx, 1, QTableWidgetItem(m_gpu))
            self.table.setItem(row_idx, 2, QTableWidgetItem(m_count))
            self.table.setItem(row_idx, 3, QTableWidgetItem(m_price))
            self.table.setItem(row_idx, 4, QTableWidgetItem(m_dlperf))
            self.table.setItem(row_idx, 5, QTableWidgetItem(m_rel))

    def show_success(self, message):
        QMessageBox.information(self, "Éxito", message)

    def show_error(self, message):
        QMessageBox.warning(self, "Error", message)
