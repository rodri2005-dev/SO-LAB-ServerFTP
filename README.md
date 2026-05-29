# SO-LAB-ServerFTP

Sistema multipropósito de gestión remota de archivos con sockets TCP, threads y sincronización para la actividad “Terminal, Hilos y Sincronización”.

## Arquitectura

El proyecto se divide en tres programas:

1. `servidor.py` atiende múltiples clientes por TCP usando un thread por conexión.
2. `cliente.py` ofrece un menú interactivo para listar, leer, copiar, subir, descargar y ver logs.
3. `demonio.py` revisa `entrada/` cada 10 segundos y mueve archivos nuevos a `procesados/` en segundo plano.

El entorno compartido se prepara automáticamente en `~/servidor_archivos/` con esta estructura:

```text
~/servidor_archivos/
├── entrada/
├── procesados/
└── logs/
    └── registro.log
```

Al iniciar cualquiera de los programas, el sistema crea la estructura si no existe y genera 3 archivos de prueba `.txt` en `entrada/` con contenido aleatorio.

## Permisos Linux

El código aplica permisos de tipo `700` para los directorios y `600` para los archivos de trabajo. Eso significa:

1. Solo el dueño puede leer, escribir y entrar en los directorios.
2. Solo el dueño puede leer y escribir `registro.log` y los archivos de prueba.
3. Se evita que otros usuarios del sistema accedan a los archivos de la práctica.

Comandos equivalentes en terminal Linux:

```bash
mkdir -p ~/servidor_archivos/entrada ~/servidor_archivos/procesados ~/servidor_archivos/logs
chmod 700 ~/servidor_archivos
chmod 700 ~/servidor_archivos/entrada ~/servidor_archivos/procesados ~/servidor_archivos/logs
chmod 600 ~/servidor_archivos/logs/registro.log
```

## Archivos de prueba

El sistema crea automáticamente tres archivos:

1. `prueba_1.txt`
2. `prueba_2.txt`
3. `prueba_3.txt`

Cada archivo recibe texto aleatorio. La idea es que el estudiante vea de inmediato archivos disponibles para `LISTAR`, `LEER`, `COPIAR` y `DESCARGAR`.

## Requisitos

Solo usa biblioteca estándar de Python. Los módulos principales son `socket`, `threading`, `os`, `shutil`, `time`, `pathlib`, `json` y `fcntl` en Linux para bloquear accesos concurrentes al sistema de archivos y al log compartido.

## Cómo funciona cada archivo

`servidor.py`:

1. Escucha en `127.0.0.1:5000`.
2. Recibe una solicitud JSON por conexión.
3. Procesa el comando y devuelve una respuesta JSON.
4. Registra conexiones, subidas, copias y lecturas en `registro.log`.

`cliente.py`:

1. Muestra un menú en consola.
2. Envía comandos al servidor.
3. Recibe la respuesta completa y la imprime de forma clara.

`demonio.py`:

1. Recorre `entrada/` cada 10 segundos.
2. Detecta archivos nuevos.
3. Lanza un thread por archivo.
4. Mueve el archivo a `procesados/` y deja trazabilidad en el log.

## Sincronización

Se usan dos capas de protección:

1. `threading.RLock()` para proteger el acceso concurrente entre threads dentro del mismo proceso.
2. Bloqueo de archivo con `fcntl.flock()` para coordinar servidor y demonio, que son procesos distintos.

Esto evita carreras cuando varios clientes suben o leen archivos al mismo tiempo y cuando el demonio mueve archivos mientras el servidor los manipula.

## Comandos soportados

1. `LISTAR`
2. `LEER <archivo>`
3. `COPIAR <archivo>`
4. `SUBIR <archivo>`
5. `DESCARGAR <archivo>`
6. `LOGS`

## Ejecución

Orden recomendado:

```bash
python3 servidor.py
python3 demonio.py
python3 cliente.py
```

En Windows también puedes usar `python` en lugar de `python3`.

## Problemas posibles y solución

1. Si el puerto `5000` ya está ocupado, cambia el puerto en `servidor.py` y `cliente.py`.
2. Si el servidor no responde, verifica que `servidor.py` esté ejecutándose antes del cliente.
3. Si no ves archivos en `entrada/`, espera a que se creen los archivos de prueba o sube uno manualmente desde el cliente.
4. Si el demonio no mueve archivos, confirma que tenga permisos de escritura sobre `~/servidor_archivos/`.

## Explicación pedagógica breve

Se usan threads en vez de procesos porque cada cliente solo necesita una tarea ligera de red y E/S. Los threads consumen menos recursos, permiten atender varios clientes a la vez y simplifican el código para una práctica universitaria. La sincronización es necesaria porque el servidor y el demonio comparten archivos y logs, así que sin bloqueo habría condiciones de carrera.


* Cristián Contreras 


