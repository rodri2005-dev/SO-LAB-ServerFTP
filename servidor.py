import json
import socket
import threading
import shutil
from datetime import datetime

from ruta_compartida import bloqueo_interprocesos, preparar_entorno

class ServidorArchivos:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        rutas = preparar_entorno()

        self.base_dir = rutas["base"]
        self.entrada_dir = rutas["entrada"]
        self.procesados_dir = rutas["procesados"]
        self.logs_dir = rutas["logs"]
        self.log_file = rutas["registro"]
        self.lock_fs = rutas["lock_fs"]
        self.lock_log = rutas["lock_log"]
        self.lock = threading.RLock()

    def _recibir_todo(self, conn):
        fragmentos = []
        while True:
            bloque = conn.recv(4096)
            if not bloque:
                break
            fragmentos.append(bloque)
        return b"".join(fragmentos)

    def _responder(self, conn, payload):
        conn.sendall(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def registrar_log(self, mensaje):
        with self.lock, bloqueo_interprocesos(self.lock_log):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {mensaje}\n")

    def listar_archivos(self):
        try:
            with bloqueo_interprocesos(self.lock_fs):
                archivos = sorted(
                    archivo.name for archivo in self.entrada_dir.iterdir() if archivo.is_file()
                )
            return archivos
        except Exception as e:
            return {"error": f"Error al listar: {str(e)}"}

    def copiar_a_procesados(self, nombre_archivo):
        origen = self.entrada_dir / nombre_archivo
        destino = self.procesados_dir / nombre_archivo

        try:
            with self.lock, bloqueo_interprocesos(self.lock_fs):
                if not origen.exists():
                    return {"status": "error", "message": "El archivo no existe en entrada."}

                shutil.copy2(origen, destino)

            self.registrar_log(f"Archivo {nombre_archivo} copiado a procesados.")
            return {"status": "ok", "message": "Archivo copiado con exito."}
        except Exception as e:
            return {"status": "error", "message": f"No se pudo copiar: {str(e)}"}

    def leer_archivo(self, nombre_archivo):
        ruta = self.entrada_dir / nombre_archivo
        if not ruta.exists():
            ruta = self.procesados_dir / nombre_archivo

        try:
            with self.lock, bloqueo_interprocesos(self.lock_fs):
                if ruta.exists():
                    contenido = ruta.read_text(encoding="utf-8", errors="replace")
                    return {"status": "ok", "content": contenido, "filename": ruta.name}
        except Exception as e:
            return {"status": "error", "message": f"No se pudo leer: {str(e)}"}

        return {"status": "error", "message": "Archivo no encontrado."}

    def recibir_archivo(self, nombre_archivo, contenido):
        ruta = self.entrada_dir / nombre_archivo

        try:
            with self.lock, bloqueo_interprocesos(self.lock_fs):
                ruta.write_text(contenido, encoding="utf-8")
            self.registrar_log(f"Cliente subio el archivo: {nombre_archivo}")
            return {"status": "ok", "message": "Archivo subido correctamente."}
        except Exception as e:
            return {"status": "error", "message": f"No se pudo subir el archivo: {str(e)}"}

    def leer_logs(self):
        try:
            with self.lock, bloqueo_interprocesos(self.lock_log):
                contenido = self.log_file.read_text(encoding="utf-8")
            return {"status": "ok", "content": contenido, "filename": self.log_file.name}
        except Exception as e:
            return {"status": "error", "message": f"No se pudo leer el log: {str(e)}"}

    def manejar_cliente(self, conn, addr):
        print(f"[+] Nueva conexion establecida desde {addr}")
        self.registrar_log(f"Conexion aceptada desde {addr}")
        
        try:
            datos = self._recibir_todo(conn)
            if not datos:
                return

            solicitud = json.loads(datos.decode("utf-8"))
            comando = solicitud.get("cmd", "").upper()
            nombre_archivo = solicitud.get("filename", "")
            contenido = solicitud.get("content", "")

            if comando == "LISTAR":
                respuesta = {"status": "ok", "files": self.listar_archivos()}
            elif comando == "LEER":
                respuesta = self.leer_archivo(nombre_archivo)
            elif comando == "COPIAR":
                respuesta = self.copiar_a_procesados(nombre_archivo)
            elif comando == "SUBIR":
                respuesta = self.recibir_archivo(nombre_archivo, contenido)
            elif comando == "DESCARGAR":
                respuesta = self.leer_archivo(nombre_archivo)
            elif comando in {"LOGS", "VER_LOGS"}:
                respuesta = self.leer_logs()
            else:
                respuesta = {"status": "error", "message": "Comando desconocido."}

            self._responder(conn, respuesta)
        except Exception as e:
            print(f"[-] Error manejando al cliente {addr}: {e}")
            try:
                self._responder(conn, {"status": "error", "message": f"Error interno: {str(e)}"})
            except Exception:
                pass
        finally:
            conn.close()
            print(f"[-] Conexion cerrada con {addr}")

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
