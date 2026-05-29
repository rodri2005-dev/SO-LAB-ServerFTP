import json
import socket
from pathlib import Path

class ClienteArchivos:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port

    def enviar_comando(self, mensaje_comando):
        """Establece conexion, envia una solicitud JSON y retorna la respuesta JSON."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            client_socket.sendall(json.dumps(mensaje_comando, ensure_ascii=False).encode('utf-8'))
            client_socket.shutdown(socket.SHUT_WR)

            fragmentos = []
            while True:
                parte = client_socket.recv(4096)
                if not parte:
                    break
                fragmentos.append(parte)

            respuesta = json.loads(b''.join(fragmentos).decode('utf-8'))
            client_socket.close()
            return respuesta
        except ConnectionRefusedError:
            return {"status": "error", "message": "No se pudo conectar al servidor. ¿Está encendido?"}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Respuesta inválida del servidor."}
        except Exception as e:
            return {"status": "error", "message": f"Error de cliente: {str(e)}"}

    def mostrar_respuesta(self, respuesta):
        if respuesta.get("status") == "ok":
            if "files" in respuesta:
                archivos = respuesta["files"]
                if archivos:
                    print("\n[Servidor] Archivos en entrada:")
                    for archivo in archivos:
                        print(f"- {archivo}")
                else:
                    print("\n[Servidor] No hay archivos en entrada.")
            elif "content" in respuesta:
                print(f"\n[Servidor] Contenido de {respuesta.get('filename', 'archivo')}:\n")
                print(respuesta["content"])
            else:
                print(f"\n[Servidor] {respuesta.get('message', 'Operacion exitosa.')}")
        else:
            print(f"\n[Servidor] {respuesta.get('message', 'Error desconocido.')}")

    def menu(self):
        while True:
            print("\n--- MENU CLIENTE INTERACTIVO ---")
            print("1. Listar archivos remotos en 'entrada'")
            print("2. Leer un archivo remoto")
            print("3. Copiar un archivo remoto a 'procesados'")
            print("4. Subir un archivo local al servidor")
            print("5. Descargar un archivo del servidor")
            print("6. Ver logs de operaciones del servidor")
            print("7. Salir")
            
            opcion = input("Seleccione una opcion: ")
            
            if opcion == "1":
                res = self.enviar_comando({"cmd": "LISTAR"})
                self.mostrar_respuesta(res)
                
            elif opcion == "2":
                nombre = input("Nombre del archivo a leer: ")
                res = self.enviar_comando({"cmd": "LEER", "filename": nombre})
                self.mostrar_respuesta(res)
                
            elif opcion == "3":
                nombre = input("Nombre del archivo a copiar a procesados: ")
                res = self.enviar_comando({"cmd": "COPIAR", "filename": nombre})
                self.mostrar_respuesta(res)

            elif opcion == "4":
                ruta_local = input("Ingrese la ruta del archivo local a subir (ej: test.txt): ")
                ruta = Path(ruta_local)
                if ruta.exists():
                    contenido = ruta.read_text(encoding="utf-8", errors="replace")
                    res = self.enviar_comando({"cmd": "SUBIR", "filename": ruta.name, "content": contenido})
                    self.mostrar_respuesta(res)
                else:
                    print("El archivo local no existe.")
                
            elif opcion == "5":
                nombre = input("Nombre del archivo a descargar: ")
                res = self.enviar_comando({"cmd": "DESCARGAR", "filename": nombre})
                self.mostrar_respuesta(res)
                
            elif opcion == "6":
                res = self.enviar_comando({"cmd": "LOGS"})
                self.mostrar_respuesta(res)

            elif opcion == "7":
                print("Saliendo del cliente...")
                break
            else:
                print("Opcion invalida.")

if __name__ == "__main__":
    cliente = ClienteArchivos()
    cliente.menu()