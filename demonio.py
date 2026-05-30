import os
import sys
import time
import threading
import shutil
from datetime import datetime

class DemonioProcesamiento:
    def __init__(self):
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
        self.archivos_procesados_exito = []

    def registrar_log(self, mensaje, es_bloque_final=False):
        """
        Escribe en el registro.log garantizando la exclusión mutua.
        Si es el bloque final, se encarga de formatear cada línea individualmente
        para no romper la estructura de marcas de tiempo del demonio.
        """
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                if es_bloque_final:
                    # Desglosamos el bloque para mantener el formato limpio solicitado
                    lineas = mensaje.strip().split('\n')
                    f.write(f"[{timestamp}] {lineas[0]}\n")
                    for linea in lineas[1:]:
                        f.write(f"{linea}\n")
                else:
                    f.write(f"[{timestamp}] {mensaje}\n")
            # Forzamos el vaciado del descriptor de archivos a nivel de sistema operativo
            try:
                os.sync()
            except AttributeError:
                pass

    def procesar_archivo_hilo(self, nombre_archivo):
        origen = os.path.join(self.entrada_dir, nombre_archivo)
        destino = os.path.join(self.procesados_dir, nombre_archivo)
        
        time.sleep(0.1)
        
        if os.path.exists(origen):
            try:
                if os.path.exists(destino):
                    os.remove(destino)
                    
                shutil.move(origen, destino)
                
                with self.lock:
                    print(f"[Demonio - Thread] Procesado de forma automatica: {nombre_archivo}", flush=True)
                    sys.stdout.flush()
                    self.archivos_procesados_exito.append(nombre_archivo)
                
                # Registramos el log individual fuera de un doble lock innecesario
                self.registrar_log(f"DEMONIO: Procesado de forma automatica y movido: {nombre_archivo}")
                
            except Exception as e:
                with self.lock:
                    print(f"[-] Error al mover archivo: {e}", flush=True)
                    sys.stdout.flush()
                self.registrar_log(f"DEMONIO: Error critico procesando {nombre_archivo}: {str(e)}")
        
        # Eliminación segura del set de control de la RAM
        with self.lock:
            if nombre_archivo in self.archivos_en_proceso:
                self.archivos_en_proceso.remove(nombre_archivo)

    def monitorear(self):
        print("[*] Demonio de monitoreo iniciado. Analizando directorio de entrada...", flush=True)
        sys.stdout.flush()
        
        try:
            if os.path.exists(self.entrada_dir):
                archivos_iniciales = [f for f in os.listdir(self.entrada_dir) if os.path.isfile(os.path.join(self.entrada_dir, f))]
                
                if not archivos_iniciales:
                    print("[*] Directorio de entrada vacio. No hay tareas pendientes.", flush=True)
                    print("[-] Finalizando ejecucion del Demonio de forma limpia.", flush=True)
                    sys.stdout.flush()
                    self.registrar_log("DEMONIO: Se ejecuto proceso demonio, pero el directorio de entrada estaba vacio.")
                    os._exit(0)

                cant_archivos = len(archivos_iniciales)
                self.registrar_log(f"DEMONIO: Iniciando procesamiento por lote. Detectados {cant_archivos} archivo(s) nuevo(s).")

                # 1. Registro síncrono en la RAM antes de disparar la concurrencia
                for archivo in archivos_iniciales:
                    with self.lock:
                        self.archivos_en_proceso.add(archivo)
                    
                    print(f"[*] Demonio detecto nuevo archivo: {archivo}. Lanzando hilo de procesamiento...", flush=True)
                    sys.stdout.flush()
                    
                    hilo = threading.Thread(target=self.procesar_archivo_hilo, args=(archivo,))
                    hilo.daemon = True
                    hilo.start()

                # 2. ESPERA DINÁMICA EN RAM: Monitoreo seguro de la estructura de datos
                while True:
                    with self.lock:
                        if not self.archivos_en_proceso:
                            break
                    time.sleep(0.05) # Balance óptimo para la CPU (50ms)

            # 3. Cierre y purga total de buffers
            print("[*] Todos los archivos de la rafaga fueron procesados exitosamente.", flush=True)
            print("[-] Finalizando ejecucion del Demonio de forma limpia.", flush=True)
            sys.stdout.flush() 
            
            # Construcción segura de variables fuera de zonas críticas complejas
            with self.lock:
                lista_detallada = ", ".join(self.archivos_procesados_exito) if self.archivos_procesados_exito else "Ninguno"
            
            # Formateo estricto según requerimientos
            bloque_reporte = (
                f"DEMONIO: Procesamiento por lote finalizado con exito.\n"
                f"    -> Total procesados: {cant_archivos}\n"
                f"    -> Detalle de archivos: [{lista_detallada}]"
            )
            
            self.registrar_log(bloque_reporte, es_bloque_final=True)
            
            # Purga física del búfer de stdout del sistema operativo antes de matar el proceso
            sys.stdout.flush()
            time.sleep(0.1) # Ventana de tiempo crítica para que WSL transfiera los bytes finales a PowerShell
            
            os._exit(0)
            
        except KeyboardInterrupt:
            print("\n[-] Deteniendo el Demonio de procesamiento.", flush=True)
            sys.stdout.flush()
            os._exit(0)

if __name__ == "__main__":
    demonio = DemonioProcesamiento()
    demonio.monitorear()
