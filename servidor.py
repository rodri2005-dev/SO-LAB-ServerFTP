import socket
import threading
import os
import shutil
from datetime import datetime

class ServidorArchivos:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        
        # Usamos la carpeta actual del script para no enredarnos con rutas del Home de Windows
        self.base_dir = os.path.abspath("./servidor_archivos")
        self.entrada_dir = os.path.join(self.base_dir, "entrada")
        self.procesados_dir = os.path.join(self.base_dir, "procesados")
        self.log_file = os.path.join(self.base_dir, "logs", "registro.log")
        
        # Crear automáticamente todos los directorios si no existen
        os.makedirs(self.entrada_dir, exist_ok=True)
        os.makedirs(self.procesados_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Lock compartido para evitar condiciones de carrera en el archivo log y directorios
        self.lock = threading.Lock()
        
        # Asegurar que el archivo log exista
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("") # Inicializa el archivo vacío de forma segura

    def registrar_log(self, mensaje):
        """Registra operaciones en el log de manera thread-safe usando Locks."""
        with self.lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a") as f:
                f.write(f"[{timestamp}] {mensaje}\n")

    def listar_archivos(self):
        """Operación: Listar archivos en entrada."""
        try:
            archivos = os.listdir(self.entrada_dir)
            return ",".join(archivos) if archivos else "Directorio vacio"
        except Exception as e:
            return f"Error al listar: {str(e)}"

    def copiar_a_procesados(self, nombre_archivo):
        """Operación: Copiar archivo a procesados."""
        origen = os.path.join(self.entrada_dir, nombre_archivo)
        destino = os.path.join(self.procesados_dir, nombre_archivo)
        
        with self.lock:  # Sincronización de acceso a archivos
            if os.path.exists(origen):
                shutil.copy(origen, destino)
                self.registrar_log(f"Archivo {nombre_archivo} copiado a procesados.")
                return "OK: Archivo copiado con exito."
            return "ERROR: El archivo no existe en entrada."

    def leer_archivo(self, nombre_archivo):
        """Operación: Leer contenido de un archivo en entrada."""
        ruta = os.path.join(self.entrada_dir, nombre_archivo)
        if not os.path.exists(ruta):
            # Buscar en procesados si no está en entrada
            ruta = os.path.join(self.procesados_dir, nombre_archivo)
            
        if os.path.exists(ruta):
            with self.lock:
                with open(ruta, "r") as f:
                    return f.read()
        return "ERROR: Archivo no encontrado."

    def recibir_archivo(self, nombre_archivo, contenido):
        """Operación extra (Cliente): Subir archivo local al servidor."""
        ruta = os.path.join(self.entrada_dir, nombre_archivo)
        with self.lock:
            with open(ruta, "w") as f:
                f.write(contenido)
        self.registrar_log(f"Cliente subio el archivo: {nombre_archivo}")
        return "OK: Archivo subido correctamente."

    def leer_logs(self):
        """Operación extra (Cliente): Ver logs de operaciones."""
        with self.lock:
            with open(self.log_file, "r") as f:
                return f.read()

    def manejar_cliente(self, conn, addr):
        """Hilo dedicado a atender a un cliente específico."""
        print(f"[+] Nueva conexion establecida desde {addr}")
        self.registrar_log(f"Conexion aceptada desde {addr}")
        
        try:
            while True:
                data = conn.recv(4096).decode('utf-8')
                if not data:
                    break
                
                partes = data.split("|", 2)
                comando = partes[0]
                
                respuesta = "ERROR: Comando desconocido."
                
                if comando == "LISTAR":
                    respuesta = self.listar_archivos()
                elif comando == "COPIAR":
                    respuesta = self.copy_to_processed(partes[1]) if len(partes) > 1 else "ERROR: Falta parametro."
                    if len(partes) > 1: respuesta = self.copiar_a_procesados(partes[1])
                elif comando == "LEER":
                    if len(partes) > 1: respuesta = self.leer_archivo(partes[1])
                elif comando == "SUBIR":
                    if len(partes) > 2: respuesta = self.recibir_archivo(partes[1], partes[2])
                elif comando == "DESCARGAR":
                    if len(partes) > 1: respuesta = self.leer_archivo(partes[1])
                elif comando == "VER_LOGS":
                    respuesta = self.leer_logs()
                
                conn.sendall(respuesta.encode('utf-8'))
        except Exception as e:
            print(f"[-] Error manejando al cliente {addr}: {e}")
        finally:
            conn.close()
            print(f"[-] Conexion cerrada con {addr}")

    def iniciar(self):
        """Bucle principal del servidor que acepta conexiones entrantes."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"[*] Servidor escuchando en {self.host}:{self.port}...")
        
        try:
            while True:
                conn, addr = server_socket.accept()
                # Crear e iniciar un hilo por cada cliente concurrente
                hilo = threading.Thread(target=self.manejar_cliente, args=(conn, addr))
                hilo.daemon = True
                hilo.start()
        except KeyboardInterrupt:
            print("\n[*] Apagando el servidor de manera ordenada.")

if __name__ == "__main__":
    servidor = ServidorArchivos()
    servidor.iniciar()