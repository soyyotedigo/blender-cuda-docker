import subprocess
import json
import random
from PySide2.QtCore import QThread, Signal

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

    def run(self):
        if self.mode == 'search':
            self.search_offers()
        elif self.mode == 'rent':
            self.rent_instance()
        elif self.mode == 'check_connection':
            self.check_connection_status()
        elif self.mode == 'set_api_key':
            self.set_api_key()

    def set_api_key(self):
        api_key = self.kwargs.get('api_key')
        if not api_key:
            self.finished_action.emit("FAILED: No API Key provided")
            return

        try:
            # vastai set api-key <key>
            cmd = f"vastai set api-key {api_key}"
            # No usamos check_output porque no devuelve JSON, solo éxito/error
            subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.finished_action.emit("SUCCESS")
        except subprocess.CalledProcessError:
            self.finished_action.emit("FAILED: Command execution failed")
        except Exception as e:
            self.finished_action.emit(f"FAILED: {str(e)}")

    def check_vast_installed(self):
        """Verifica si vastai está en el PATH"""
        try:
            # shell=True es necesario en Windows si vastai es un .bat/.cmd
            subprocess.check_call(["vastai", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
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
            self.log_message.emit("[!] Vast.ai CLI no detectada. Por favor instala vastai.")
            self.error_occurred.emit("Vast.ai CLI no encontrada")
            return
        
        # Ejecución Real
        try:
            # shell=True para Windows
            cmd = f"vastai search offers \"{query}\" --raw"
            self.log_message.emit(f"[*] Ejecutando: {cmd}")
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            data = json.loads(result)
            self.data_ready.emit(data)
            self.log_message.emit(f"[+] Búsqueda completada. {len(data)} máquinas encontradas.")
        except Exception as e:
            self.error_occurred.emit(f"Error ejecutando vastai search: {str(e)}")

    def rent_instance(self):
        # Ahora esperamos una lista de IDs
        instance_ids = self.kwargs.get('ids', [])
        if not isinstance(instance_ids, list):
             instance_ids = [instance_ids]

        image = self.kwargs.get('image')
        disk = self.kwargs.get('disk')
        onstart = self.kwargs.get('onstart')
        env_vars = self.kwargs.get('env')

        if not self.check_vast_installed():
            self.error_occurred.emit("Vast.ai CLI no encontrada")
            return

        success_count = 0
        
        for instance_id in instance_ids:
            self.log_message.emit(f"[*] Intentando alquilar ID: {instance_id} con imagen: {image}...")

            try:
                # Comando: vastai create instance <id> --image <image> --disk <disk> --onstart <cmd> --env <env>
                cmd_str = f"vastai create instance {instance_id} --image {image} --disk {disk}"
                
                if env_vars:
                    cmd_str += f" --env \"{env_vars}\""

                if onstart:
                    cmd_str += f" --onstart \"{onstart}\""

                self.log_message.emit(f"[*] Ejecutando: {cmd_str}")
                result = subprocess.check_output(cmd_str, shell=True).decode('utf-8')
                
                if "success" in result.lower() or "id" in result.lower():
                    self.log_message.emit(f"[+] Instancia {instance_id} creada. Respuesta: {result}")
                    success_count += 1
                else:
                    self.error_occurred.emit(f"Respuesta inesperada para {instance_id}: {result}")
                    
            except Exception as e:
                self.error_occurred.emit(f"Error al alquilar {instance_id}: {str(e)}")
        
        if success_count > 0:
            self.finished_action.emit(f"SUCCESS:{success_count}")
        else:
            self.finished_action.emit("FAILED")

    def check_connection_status(self):
        if not self.check_vast_installed():
            self.finished_action.emit("CONNECTION_FAILED")
            return

        try:
            # vastai show user --raw devuelve JSON con info del usuario
            cmd = "vastai show user --raw"
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            data = json.loads(result)
            
            # Si hay un email, asumimos éxito
            if "email" in data:
                email = data.get("email", "Unknown")
                balance = data.get("credit", 0.0)
                self.finished_action.emit(f"CONNECTED:{email}:{balance}")
            else:
                self.finished_action.emit("CONNECTION_FAILED")
        except Exception as e:
            self.log_message.emit(f"Error verificando conexión: {str(e)}")
            self.finished_action.emit("CONNECTION_FAILED")
