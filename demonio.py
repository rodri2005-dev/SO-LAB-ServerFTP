import shutil
import threading
import time
from datetime import datetime

from ruta_compartida import bloqueo_interprocesos, preparar_entorno

class DemonioProcesamiento:
    def __init__(self):
        rutas = preparar_entorno()
        self.base_dir = rutas["base"]
        self.entrada_dir = rutas["entrada"]
        self.procesados_dir = rutas["procesados"]
        self.log_file = rutas["registro"]
        self.lock_fs = rutas["lock_fs"]
        self.lock_log = rutas["lock_log"]
        self.lock = threading.RLock()
        self.archivos_en_proceso = set()

    def registrar_log(self, mensaje):
        with self.lock, bloqueo_interprocesos(self.lock_log):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [DEMONIO] {mensaje}\n")

    def procesar_archivo_hilo(self, nombre_archivo):
        origen = self.entrada_dir / nombre_archivo
        destino = self.procesados_dir / nombre_archivo
        
        time.sleep(1)  # Simulación de procesamiento
        
        try:
            with self.lock, bloqueo_interprocesos(self.lock_fs):
                if origen.exists():
                    if destino.exists():
                        destino.unlink()

                    shutil.move(str(origen), str(destino))
                    mensaje_log = f"Procesado de forma automatica y movido: {nombre_archivo}"
                    mensaje_consola = f"[Demonio - Thread] Procesado de forma automatica: {nombre_archivo}"
                else:
                    mensaje_log = f"El archivo ya no existia al procesarlo: {nombre_archivo}"
                    mensaje_consola = f"[-] El archivo ya no existia: {nombre_archivo}"

            print(mensaje_consola, flush=True)
            self.registrar_log(mensaje_log)
        except Exception as e:
            print(f"[-] Error al mover archivo: {e}", flush=True)
            self.registrar_log(f"Error procesando {nombre_archivo}: {str(e)}")
        finally:
            with self.lock:
                self.archivos_en_proceso.discard(nombre_archivo)

    def monitorear(self):
        print("[*] Demonio de monitoreo iniciado. Escaneando cada 10 segundos...", flush=True)
        try:
            while True:
                if self.entrada_dir.exists():
                    with self.lock, bloqueo_interprocesos(self.lock_fs):
                        archivos = [
                            archivo.name
                            for archivo in self.entrada_dir.iterdir()
                            if archivo.is_file()
                        ]

                        nuevos = [archivo for archivo in archivos if archivo not in self.archivos_en_proceso]

                        for archivo in nuevos:
                            self.archivos_en_proceso.add(archivo)
                            print(f"[*] Demonio detecto nuevo archivo: {archivo}. Lanzando hilo de procesamiento...", flush=True)

                            hilo = threading.Thread(target=self.procesar_archivo_hilo, args=(archivo,), daemon=True)
                            hilo.start()

                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[-] Deteniendo el Demonio de procesamiento.", flush=True)

if __name__ == "__main__":
    demonio = DemonioProcesamiento()
    demonio.monitorear()