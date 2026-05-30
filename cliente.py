import socket
import os

class ClienteArchivos:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        
    def enviar_comando(self, mensaje_comando):
        """Establece conexion, envia instruccion y retorna la respuesta de forma limpia."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Metemos un timeout prudente para que Windows no corte la conexion antes de tiempo
            client_socket.settimeout(15.0) 
            client_socket.connect((self.host, self.port))
            
            # 1. Enviar el comando completo de un solo viaje
            client_socket.sendall(mensaje_comando.encode('utf-8'))
            
            # 2. Recibimos la respuesta de forma segura. Al no haber shutdown, 
            # leemos lo que el servidor nos mande directo del buffer.
            respuesta_bytes = client_socket.recv(65536)
            respuesta = respuesta_bytes.decode('utf-8')
            
            client_socket.close()
            return respuesta
        except socket.timeout:
            return "ERROR: El servidor demoro demasiado en responder (Timeout)."
        except ConnectionRefusedError:
            return "ERROR: No se pudo conectar al servidor. ¿Esta encendido?"
        except Exception as e:
            return f"ERROR inesperado en la comunicacion: {str(e)}"

    def menu(self):
        while True:
            print("\n--- MENU CLIENTE INTERACTIVO ---")
            print("1. Listar archivos remotos en 'entrada'")
            print("2. Descargar un archivo del servidor")
            print("3. Subir un archivo local al servidor")
            print("4. Ver logs de operaciones del servidor")
            print("5. Solicitar copia remota (Entrada -> Procesados)")
            print("6. Salir")
            opcion = input("Seleccione una opcion: ")
           
            if opcion == "1":
                res = self.enviar_comando("LISTAR")
                print(f"\n[Servidor] Archivos:\n{res}")
               
            elif opcion == "2":
                nombre = input("Nombre del archivo a descargar: ")
                res = self.enviar_comando(f"DESCARGAR|{nombre}")
                if "ERROR" in res:
                    print(f"\n[Servidor] {res}")
                else:
                    # En vez de imprimirlo, lo creamos y guardamos localmente
                    try:
                        with open(nombre, "w", encoding="utf-8") as f:
                            f.write(res)
                        print(f"\n[Cliente] ¡Archivo '{nombre}' descargado y guardado con éxito!")
                    except Exception as e:
                        print(f"\n[Cliente] Error al guardar el archivo localmente: {e}")

            elif opcion == "3":
                ruta_local = input("Ingrese la ruta del archivo local a subir (ej: test.txt) o por ejemplo una ruta como home/[usuario]/archivo1.txt: ")
                # 1. Expandimos el '~' (ej: ~/SO_ULS/hola.txt -> /home/usuario/SO_ULS/hola.txt)
                ruta_local = os.path.expanduser(ruta_local)
                # 2. Aseguramos la ruta absoluta real del sistema
                ruta_local = os.path.abspath(ruta_local)
                if os.path.exists(ruta_local):
                    try:
                        nombre_archivo = os.path.basename(ruta_local)
                        # Agregamos encoding utf-8 para evitar caídas por caracteres chilenos (ñ, acentos)
                        with open(ruta_local, "r", encoding="utf-8") as f:
                            contenido = f.read()
                        res = self.enviar_comando(f"SUBIR|{nombre_archivo}|{contenido}")
                        print(f"\n[Servidor] {res}")
                    except Exception as e:
                        print(f"\n[Cliente] Error técnico al leer o transferir el archivo: {e}")
                else:
                    print(f"\n[Cliente] ERROR: El archivo no existe. Python buscó en la ruta exacta:\n-> {ruta_local}")

            elif opcion == "4":
                res = self.enviar_comando("VER_LOGS")
                print(f"\n--- HISTORIAL DE LOGS DEL SERVIDOR ---\n{res}")

            elif opcion == "5":
                nombre = input("Nombre del archivo a procesar de forma remota: ")
                res = self.enviar_comando(f"COPIAR|{nombre}")
                print(f"\n[Servidor] {res}")
            elif opcion == "6":
                print("Saliendo del cliente...")
                break
            else:
                print("Opcion invalida.")

if __name__ == "__main__":
    cliente = ClienteArchivos()
    cliente.menu()
