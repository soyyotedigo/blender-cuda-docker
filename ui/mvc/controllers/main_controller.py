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
        
        # Nuevas señales
        self.view.instances_requested.connect(self.handle_show_instances)
        self.view.destroy_requested.connect(self.handle_destroy_instance)
        self.view.ssh_requested.connect(self.handle_ssh_connect)

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

    def handle_search(self, gpu, price, disk, region, cuda):
        self.ensure_worker_stopped()
        self.view.set_loading(True)
        self.view.table.setRowCount(0)
        
        self.worker = VastWorker(
            mode='search', 
            gpu_name=gpu, 
            max_price=price, 
            disk_space=disk,
            region=region,
            cuda_vers=cuda
        )
        self.worker.data_ready.connect(self.view.populate_table)
        self.worker.log_message.connect(self.view.append_log)
        self.worker.error_occurred.connect(lambda err: self.view.append_log(f"ERROR: {err}"))
        self.worker.finished.connect(lambda: self.view.set_loading(False))
        self.worker.start()

    def handle_rent(self, machine_ids, image, disk, onstart, env_base):
        self.ensure_worker_stopped()
        self.view.set_loading(True)
        
        # Lógica de Render Distribuido
        # Parsear env_base para encontrar START_FRAME y END_FRAME si existen
        # env_base es un string tipo "-e VAR=VAL -e VAR2=VAL2"
        
        start_frame = 1
        end_frame = 1
        
        import re
        start_match = re.search(r'START_FRAME=(\d+)', env_base)
        end_match = re.search(r'END_FRAME=(\d+)', env_base)
        
        if start_match and end_match:
            start_frame = int(start_match.group(1))
            end_frame = int(end_match.group(1))
        
        num_machines = len(machine_ids)
        
        # Preparamos un diccionario de configs por máquina si hay más de una y hay rango
        instances_config = {}
        
        if num_machines > 1 and start_match and end_match:
            total_frames = end_frame - start_frame + 1
            frames_per_machine = total_frames // num_machines
            remainder = total_frames % num_machines
            
            current_start = start_frame
            
            for i, m_id in enumerate(machine_ids):
                # Distribuir el resto entre las primeras máquinas
                extra = 1 if i < remainder else 0
                count = frames_per_machine + extra
                
                current_end = current_start + count - 1
                
                # Reemplazar en el string de entorno
                # Usamos regex para reemplazar los valores originales por los calculados
                my_env = re.sub(r'START_FRAME=\d+', f'START_FRAME={current_start}', env_base)
                my_env = re.sub(r'END_FRAME=\d+', f'END_FRAME={current_end}', my_env)
                
                instances_config[m_id] = my_env
                
                self.view.append_log(f"[*] Distribución: Máquina {m_id} -> Frames {current_start} a {current_end}")
                
                current_start = current_end + 1
        else:
            # Caso simple: misma config para todos
            for m_id in machine_ids:
                instances_config[m_id] = env_base

        self.worker = VastWorker(
            mode='rent', 
            ids=machine_ids, 
            image=image, 
            disk=disk, 
            onstart=onstart,
            instances_config=instances_config # Pasamos el dict de configs
        )
        self.worker.log_message.connect(self.view.append_log)
        self.worker.error_occurred.connect(lambda err: self.view.append_log(f"ERROR ALQUILER: {err}"))
        self.worker.finished_action.connect(self.on_rent_finished)
        self.worker.finished.connect(lambda: self.view.set_loading(False))
        self.worker.start()

    def on_rent_finished(self, status):
        if status.startswith("SUCCESS"):
            count = status.split(":")[1] if ":" in status else "1"
            self.view.show_success(f"{count} Máquina(s) desplegada(s) correctamente.\nRevisa la pestaña 'Instancias Creadas'.")
            # Auto refresh instances
            self.handle_show_instances()

    def handle_show_instances(self):
        self.ensure_worker_stopped()
        self.view.append_log("[*] Actualizando lista de instancias...")
        self.worker = VastWorker(mode='show_instances')
        self.worker.data_ready.connect(self.view.populate_instances_table)
        self.worker.log_message.connect(self.view.append_log)
        self.worker.error_occurred.connect(lambda err: self.view.append_log(f"ERROR: {err}"))
        self.worker.start()

    def handle_destroy_instance(self, instance_ids):
        # instance_ids is now a list
        self.ensure_worker_stopped()
        if isinstance(instance_ids, str):
            instance_ids = [instance_ids]
            
        count = len(instance_ids)
        self.view.append_log(f"[*] Destruyendo {count} instancia(s)...")
        
        self.worker = VastWorker(mode='destroy', instance_ids=instance_ids)
        self.worker.finished_action.connect(self.on_destroy_finished)
        self.worker.log_message.connect(self.view.append_log)
        self.worker.start()

    def on_destroy_finished(self, result):
        if result.startswith("SUCCESS"):
            count = result.split(":")[1] if ":" in result else "1"
            self.view.append_log(f"[+] {count} Instancia(s) destruida(s) correctamente.")
            self.handle_show_instances() # Refresh list
        else:
            self.view.show_error("Error al destruir instancias. Revisa el log.")

    def handle_ssh_connect(self, instance_ids):
        # instance_ids is now a list
        self.ensure_worker_stopped()
        if isinstance(instance_ids, str):
            instance_ids = [instance_ids]

        self.view.append_log(f"[*] Obteniendo acceso SSH para {len(instance_ids)} instancia(s)...")
        self.worker = VastWorker(mode='ssh_url', instance_ids=instance_ids)
        self.worker.finished_action.connect(self.on_ssh_ready)
        self.worker.start()

    def on_ssh_ready(self, ssh_command):
        if ssh_command.startswith("ssh://"):
            # vastai ssh-url devuelve ssh://user@ip:port
            # Queremos convertirlo a comando ssh user@ip -p port
            # O simplemente usar vastai ssh-url output que a veces es el comando completo
            # Vamos a asumir que el worker nos devuelve el comando listo o la url.
            # Ajustaremos el worker para que devuelva el comando parseado.
            pass
        elif ssh_command.startswith("SSH_CMD:"):
            cmd = ssh_command.split(":", 1)[1]
            self.view.append_log(f"[+] Lanzando terminal SSH: {cmd}")
            import subprocess
            import sys
            
            # Lanzar nueva terminal
            if sys.platform == 'win32':
                subprocess.Popen(f'start cmd /k "{cmd}"', shell=True)
            else:
                # Linux/Mac (xterm o similar, simplificado)
                subprocess.Popen(f'xterm -e "{cmd}"', shell=True)
        else:
            self.view.append_log(f"[-] No se pudo obtener SSH: {ssh_command}")

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
