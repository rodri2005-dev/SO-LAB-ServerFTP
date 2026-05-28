import socket
import os

class ClienteArchivos:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port

    def enviar_comando(self, mensaje_comando):
        """Establece conexion, envia instruccion y retorna la respuesta."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            client_socket.sendall(mensaje_comando.encode('utf-8'))
            respuesta = client_socket.recv(4096).decode('utf-8')
            client_socket.close()
            return respuesta
        except ConnectionRefusedError:
            return "ERROR: No se pudo conectar al servidor. ¿Esta encendido?"

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
                    print(f"\n[Contenido de {nombre}]:\n{res}")
                    
            elif opcion == "3":
                ruta_local = input("Ingrese la ruta del archivo local a subir (ej: test.txt): ")
                if os.path.exists(ruta_local):
                    nombre_archivo = os.path.basename(ruta_local)
                    with open(ruta_local, "r") as f:
                        contenido = f.read()
                    res = self.enviar_comando(f"SUBIR|{nombre_archivo}|{contenido}")
                    print(f"\n[Servidor] {res}")
                else:
                    print("El archivo local no existe.")
                    
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