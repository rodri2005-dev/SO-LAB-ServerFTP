import os
import time
import threading
import shutil
from datetime import datetime

class DemonioProcesamiento:
    def __init__(self):
        # Mapea dinámicamente la ruta absoluta donde está el script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(script_dir, "servidor_archivos")
        
        self.entrada_dir = os.path.join(self.base_dir, "entrada")
        self.procesados_dir = os.path.join(self.base_dir, "procesados")
        self.log_file = os.path.join(self.base_dir, "logs", "registro.log")
        
        os.makedirs(self.entrada_dir, exist_ok=True)
        os.makedirs(self.procesados_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        self.lock = threading.Lock()
        self.archivos_en_proceso = set()

    def procesar_archivo_hilo(self, nombre_archivo):
        origen = os.path.join(self.entrada_dir, nombre_archivo)
        destino = os.path.join(self.procesados_dir, nombre_archivo)
        
        time.sleep(1) # Simulación de procesamiento
        
        with self.lock:
            if os.path.exists(origen):
                try:
                    if os.path.exists(destino):
                        os.remove(destino)
                        
                    shutil.move(origen, destino)
                    print(f"[Demonio - Thread] Procesado de forma automatica: {nombre_archivo}", flush=True)
                    self.registrar_log(f"Procesado de forma automatica y movido: {nombre_archivo}")
                except Exception as e:
                    print(f"[-] Error al mover archivo: {e}", flush=True)
                    self.registrar_log(f"Error procesando {nombre_archivo}: {str(e)}")
            
            if nombre_archivo in self.archivos_en_proceso:
                self.archivos_en_proceso.remove(nombre_archivo)

    def monitorear(self):
        print("[*] Demonio de monitoreo iniciado. Escaneando cada 10 segundos...", flush=True)
        try:
            while True:
                if os.path.exists(self.entrada_dir):
                    archivos = [f for f in os.listdir(self.entrada_dir) if os.path.isfile(os.path.join(self.entrada_dir, f))]
                    
                    for archivo in archivos:
                        if archivo not in self.archivos_en_proceso:
                            self.archivos_en_proceso.add(archivo)
                            print(f"[*] Demonio detecto nuevo archivo: {archivo}. Lanzando hilo de procesamiento...", flush=True)
                            
                            hilo = threading.Thread(target=self.procesar_archivo_hilo, args=(archivo,))
                            hilo.start()
                        
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[-] Deteniendo el Demonio de procesamiento.", flush=True)

if __name__ == "__main__":
    demonio = DemonioProcesamiento()
    demonio.monitorear()
