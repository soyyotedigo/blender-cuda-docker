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
        self.view.set_api_key_requested.connect(self.handle_set_api_key)

        # Verificar conexión al inicio
        self.check_connection()

    def show(self):
        self.view.show()
        # Hook close event to stop worker
        self.view.closeEvent = self.on_close

    def on_close(self, event):
        self.ensure_worker_stopped()
        event.accept()

    def ensure_worker_stopped(self):
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        self.worker = None

    def handle_search(self, gpu, price, disk):
        self.ensure_worker_stopped()
        self.view.set_loading(True)
        self.view.table.setRowCount(0)
        
        self.worker = VastWorker(mode='search', gpu_name=gpu, max_price=price, disk_space=disk)
        self.worker.data_ready.connect(self.view.populate_table)
        self.worker.log_message.connect(self.view.append_log)
        self.worker.error_occurred.connect(lambda err: self.view.append_log(f"ERROR: {err}"))
        self.worker.finished.connect(lambda: self.view.set_loading(False))
        self.worker.start()

    def handle_rent(self, machine_ids, image, disk, onstart, env):
        self.ensure_worker_stopped()
        self.view.set_loading(True)
        
        self.worker = VastWorker(
            mode='rent', 
            ids=machine_ids, 
            image=image, 
            disk=disk, 
            onstart=onstart,
            env=env
        )
        self.worker.log_message.connect(self.view.append_log)
        self.worker.error_occurred.connect(lambda err: self.view.append_log(f"ERROR ALQUILER: {err}"))
        self.worker.finished_action.connect(self.on_rent_finished)
        self.worker.finished.connect(lambda: self.view.set_loading(False))
        self.worker.start()

    def on_rent_finished(self, status):
        if status.startswith("SUCCESS"):
            count = status.split(":")[1] if ":" in status else "1"
            self.view.show_success(f"{count} Máquina(s) desplegada(s) correctamente.\nRevisa la consola o el dashboard web.")

    def check_connection(self):
        self.ensure_worker_stopped()
        self.worker = VastWorker(mode='check_connection')
        self.worker.finished_action.connect(self.on_connection_checked)
        self.worker.start()

    def on_connection_checked(self, result):
        if result.startswith("CONNECTED"):
            _, email, balance = result.split(":")
            self.view.update_status(True, email, float(balance))
        else:
            self.view.update_status(False)

    def handle_set_api_key(self, api_key):
        self.ensure_worker_stopped()
        self.view.append_log("[*] Configurando API Key...")
        self.worker = VastWorker(mode='set_api_key', api_key=api_key)
        self.worker.finished_action.connect(self.on_api_key_set)
        self.worker.start()

    def on_api_key_set(self, result):
        if result == "SUCCESS":
            self.view.append_log("[+] API Key configurada. Verificando conexión...")
            self.check_connection()
        else:
            self.view.append_log(f"[-] Error configurando API Key: {result}")
            self.view.show_error("No se pudo configurar la API Key. Revisa el log.")
