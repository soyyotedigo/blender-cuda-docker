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
        self.use_mock = False

    def run(self):
        if self.mode == 'search':
            self.search_offers()
        elif self.mode == 'rent':
            self.rent_instance()
        elif self.mode == 'check_connection':
            self.check_connection_status()

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
            # shell=True para Windows
            cmd = f"vastai search offers \"{query}\" --raw"
            self.log_message.emit(f"[*] Ejecutando: {cmd}")
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            data = json.loads(result)
            self.data_ready.emit(data)
            self.log_message.emit(f"[+] Búsqueda completada (DATOS REALES). {len(data)} máquinas encontradas.")
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
            # Comando: vastai create instance <id> --image <image> --disk <disk> --onstart <cmd> --env <env>
            # Usamos string command con shell=True para evitar problemas de parsing de argumentos en Windows
            cmd_str = f"vastai create instance {instance_id} --image {image} --disk {disk}"
            
            env_vars = self.kwargs.get('env')
            if env_vars:
                # Asumimos que el usuario ya pone las comillas si son necesarias, o lo envolvemos
                # El usuario dijo: --env "-e VAR=VAL ..."
                # Si el usuario escribe: -e VAR=VAL
                # Nosotros deberíamos poner: --env "-e VAR=VAL"
                cmd_str += f" --env \"{env_vars}\""

            if onstart:
                cmd_str += f" --onstart \"{onstart}\""

            self.log_message.emit(f"[*] Ejecutando: {cmd_str}")
            result = subprocess.check_output(cmd_str, shell=True).decode('utf-8')
            
            if "success" in result.lower() or "id" in result.lower():
                self.log_message.emit(f"[+] Instancia creada. Respuesta: {result}")
                self.finished_action.emit("SUCCESS")
            else:
                self.error_occurred.emit(f"Respuesta inesperada: {result}")
                
        except Exception as e:
            self.error_occurred.emit(f"Error al alquilar: {str(e)}")

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
