import socket
import threading
import os
import shutil
from datetime import datetime

class ServidorArchivos:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(script_dir, "servidor_archivos")
        
        self.entrada_dir = os.path.join(self.base_dir, "entrada")
        self.procesados_dir = os.path.join(self.base_dir, "procesados")
        self.log_file = os.path.join(self.base_dir, "logs", "registro.log")
        
        os.makedirs(self.entrada_dir, exist_ok=True)
        os.makedirs(self.procesados_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # SOLUCIÓN: Cambiar Lock por RLock para evitar el auto-bloqueo (Deadlock)
        self.lock = threading.RLock() 
        
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("")

    def registrar_log(self, mensaje):
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {mensaje}\n")

    def listar_archivos(self):
        try:
            archivos = os.listdir(self.entrada_dir)
            return ",".join(archivos) if archivos else "Directorio vacio"
        except Exception as e:
            return f"Error al listar: {str(e)}"

    def copiar_a_procesados(self, nombre_archivo):
        origen = os.path.join(self.entrada_dir, nombre_archivo)
        destino = os.path.join(self.procesados_dir, nombre_archivo)
        
        with self.lock:
            if os.path.exists(origen):
                shutil.copy(origen, destino)
                # Ahora que es RLock, llamar a registrar_log aquí ya no causará un Deadlock
                self.registrar_log(f"Archivo {nombre_archivo} copiado a procesados.")
                return "OK: Archivo copiado con exito."
            return "ERROR: El archivo no existe en entrada."

    def leer_archivo(self, nombre_archivo):
        ruta = os.path.join(self.entrada_dir, nombre_archivo)
        if not os.path.exists(ruta):
            path_procesados = os.path.join(self.procesados_dir, nombre_archivo)
            if os.path.exists(path_procesados):
                ruta = path_procesados
            
        with self.lock:
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    return f.read()
        return "ERROR: Archivo no encontrado."

    def recibir_archivo(self, nombre_archivo, contenido):
        ruta = os.path.join(self.entrada_dir, nombre_archivo)
        with self.lock:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
        self.registrar_log(f"Cliente subio el archivo: {nombre_archivo}")
        return "OK: Archivo subido correctamente."

    def leer_logs(self):
        with self.lock:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.read()
    
    def manejar_cliente(self, conn, addr):
        print(f"[+] Nueva conexion establecida desde {addr}")
        self.registrar_log(f"Conexion aceptada desde {addr}")
        
        try:
            data = conn.recv(65536).decode('utf-8')
            if data:
                partes = data.split("|", 2)
                comando = partes[0]
                respuesta = "ERROR: Comando desconocido."
                
                if comando == "LISTAR":
                    self.registrar_log(f"Cliente {addr} solicito LISTAR archivos de entrada.")
                    respuesta = self.listar_archivos()
                    
                elif comando == "COPIAR":
                    if len(partes) > 1: 
                        self.registrar_log(f"Cliente {addr} solicito COPIA remota de: {partes[1]}")
                        respuesta = self.copiar_a_procesados(partes[1])
                    else:
                        respuesta = "ERROR: Falta parametro."
                        
                elif comando == "LEER":
                    if len(partes) > 1: 
                        self.registrar_log(f"Cliente {addr} solicito LEER el archivo: {partes[1]}")
                        respuesta = self.leer_archivo(partes[1])
                        
                elif comando == "SUBIR":
                    if len(partes) > 2: 
                        respuesta = self.recibir_archivo(partes[1], partes[2])
                        
                elif comando == "DESCARGAR":
                    if len(partes) > 1: 
                        self.registrar_log(f"Cliente {addr} DESCARGO el archivo: {partes[1]}")
                        respuesta = self.leer_archivo(partes[1])
                        
                elif comando == "VER_LOGS":
                    self.registrar_log(f"Cliente {addr} consulto el HISTORIAL DE LOGS.")
                    respuesta = self.leer_logs()
                
                conn.sendall(respuesta.encode('utf-8'))
        except Exception as e:
            print(f"[-] Error manejando al cliente {addr}: {e}")
            self.registrar_log(f"ERROR critico manejando cliente {addr}: {str(e)}")
        finally:
            conn.close()
            print(f"[-] Conexion cerrada con {addr}")
            self.registrar_log(f"Conexion cerrada con {addr}\n")

    def iniciar(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"[*] Servidor escuchando en {self.host}:{self.port}...")
        
        try:
            while True:
                conn, addr = server_socket.accept()
                hilo = threading.Thread(target=self.manejar_cliente, args=(conn, addr))
                hilo.daemon = True
                hilo.start()
        except KeyboardInterrupt:
            print("\n[*] Apagando el servidor de manera ordenada.")

if __name__ == "__main__":
    servidor = ServidorArchivos()
    servidor.iniciar()
