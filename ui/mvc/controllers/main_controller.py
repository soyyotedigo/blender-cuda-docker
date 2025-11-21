from PySide2.QtCore import QObject
from ..views.main_window import VastGui
from ..models.vast_service import VastWorker

class MainController(QObject):
    def __init__(self):
        super().__init__()
        self.view = VastGui()
        self.worker = None

        # Conectar señales de la vista
        self.view.search_requested.connect(self.handle_search)
        self.view.rent_requested.connect(self.handle_rent)

    def show(self):
        self.view.show()

    def handle_search(self, gpu, price, disk):
        self.view.set_loading(True)
        self.view.table.setRowCount(0)
        
        self.worker = VastWorker(mode='search', gpu_name=gpu, max_price=price, disk_space=disk)
        self.worker.data_ready.connect(self.view.populate_table)
        self.worker.log_message.connect(self.view.append_log)
        self.worker.error_occurred.connect(lambda err: self.view.append_log(f"ERROR: {err}"))
        self.worker.finished.connect(lambda: self.view.set_loading(False))
        self.worker.start()

    def handle_rent(self, machine_id, image, disk, onstart):
        self.view.set_loading(True)
        
        self.worker = VastWorker(
            mode='rent', 
            id=machine_id, 
            image=image, 
            disk=disk, 
            onstart=onstart
        )
        self.worker.log_message.connect(self.view.append_log)
        self.worker.error_occurred.connect(lambda err: self.view.append_log(f"ERROR ALQUILER: {err}"))
        self.worker.finished_action.connect(self.on_rent_finished)
        self.worker.finished.connect(lambda: self.view.set_loading(False))
        self.worker.start()

    def on_rent_finished(self, status):
        if status in ["SUCCESS", "MOCK_SUCCESS"]:
            self.view.show_success(f"Máquina desplegada correctamente.\nRevisa la consola o el dashboard web.")
