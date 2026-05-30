# SO-LAB-ServerFTP


Asignatura: **Sistemas Operativos (2026)** — Universidad de La Serena. 


Sistema Multipropósito de Gestión de Archivos Remotos 🚀
Laboratorio Actividad N°5 — Sistemas Operativos (ULS)

Este proyecto consiste en un sistema multipropósito **Cliente-Servidor de Gestión de Archivos Remotos** desarrollado en Python. Implementa una arquitectura concurrente multihilo para atender conexiones simultáneas y un proceso demonio automatizado para el monitoreo y procesamiento de archivos en background, mitigando condiciones de carrera mediante primitivas de exclusión mutua (Locks).

---


## 🏗️ Arquitectura del Sistema

El ecosistema está compuesto por tres subsistemas independientes que interactúan de forma síncrona y asíncrona:

1. **Servidor (`servidor.py`):** Backend orientado a objetos que levanta un socket TCP/IP en el puerto 5000. Utiliza `threading` para derivar cada cliente entrante a un hilo independiente (*daemon thread*), permitiendo la concurrencia.
2. **Demonio (`demonio.py`):** Proceso de background que barre la carpeta de entrada cada 10 segundos. Al detectar archivos nuevos, genera un hilo de procesamiento atómico protegido por un Mutex (`threading.Lock`) para moverlos de forma segura a la carpeta de procesados sin corromper los logs.
3. **Cliente (`cliente.py`):** Interfaz interactiva por consola que permite realizar operaciones remotas de E/S como subir, descargar archivos, listar directorios y auditar el historial de logs del servidor.

---

## 📂 Estructura de Directorios del Servidor

**El sistema genera e interactúa de manera automatizada con la siguiente estructura de almacenamiento local bajo políticas de privilegios mínimos:

```
~/servidor_archivos/
├── entrada/      # Directorio de recepción y buffer de entrada para el demonio 
├── procesados/   # Directorio de destino final para archivos procesados 
└── logs/         # Directorio de auditoría 
    └── registro.log  # Archivo compartido sincronizado mediante Locks 

```

---

## 🛠️ Requisitos e Instalación

El proyecto fue desarrollado utilizando herramientas nativas del sistema operativo y no requiere de librerías de terceros (no necesita `pip install`):

* 
**Intérprete:** Python 3.12 (64-bits) o superior.


* 
**Módulos Estándar:** `socket`, `threading`, `os`, `shutil`, `time`, `datetime`.


* 
**Entorno:** Compatible con entornos Linux (WSL) y Windows (CMD/PowerShell).



---

## 🚀 Guía de Ejecución (Paso a Paso)

Para replicar el entorno y ejecutar la simulación de concurrencia completa, siga este orden estricto en terminales independientes:

###Paso 1: Configurar el entorno local y permisos (Linux/WSL)Navegue hasta la raíz del proyecto e inicialice la estructura de almacenamiento local mediante rutas relativas dinámicas. Posteriormente, aplique la política de privilegios mínimos para restringir el acceso a usuarios externos del sistema operativo:  
```
cd ~/SO_ULS/PROYECTOSO_FTP/
mkdir -p servidor_archivos/entrada servidor_archivos/procesados servidor_archivos/logs
chmod 700 servidor_archivos
```

Paso 2: Generación de Datos de Entrada (Opcional para pruebas síncronas)Inyecte cargas de trabajo iniciales en el buffer de entrada para validar el comportamiento del sistema antes de activar la automatización: 

```
echo "Datos de telemetria - Sensor Alfa: 42" > servidor_archivos/entrada/archivo1.txt
echo "Log de sistema operativo - Estado: OK" > servidor_archivos/entrada/archivo2.txt
echo "Buffer temporal de procesamiento v3" > servidor_archivos/entrada/archivo3.txt
```

Paso 3: Levantar el Servidor CentralAbra una terminal en la raíz del proyecto e inicialice el backend de red utilizando el parámetro -u para forzar el vaciado del buffer de salida en tiempo real:  `python3 -u servidor.py`


Paso 4 Activar el Demonio de Monitoreo: Abra una segunda terminal en paralelo y ejecute el proceso de background encargado del procesamiento automático:  `python3 -u demonio.py`


Paso 5 Inicializar Clientes Interactivos: Abra terminales adicionales (hasta 4 para pruebas de estrés de concurrencia completa) y ejecute la interfaz de usuario para interactuar con los sockets TCP/IP:  `python3 cliente.py`

## 🔒 Mecanismos de Sincronización Implementados

* 
**Exclusión Mutua (Mutex):** Exclusión Mutua de Grano Fino (Fine-Grained Locking): Se implementó la primitiva de sincronización threading.Lock() configurada bajo un enfoque de grano fino. A diferencia de una estrategia de grano grueso—que introduce severos retardos e inanición por contención al bloquear bloques masivos de código—, nuestra arquitectura restringe la exclusión mutua única y estrictamente al milisegundo en que se modifican los recursos compartidos globales: el archivo centralizado de auditoría (registro.log) y el set de control en memoria RAM (archivos_en_proceso).  Las llamadas al sistema operativas que involucran Entrada/Salida (E/S) pesada en el disco duro, tales como shutil.move(), shutil.copy() y os.remove(), se ejecutan de forma completamente asíncrona y en paralelo fuera del bloque protegido por el candado, dado que cada hilo de ejecución atiende descriptores de archivos con nombres unívocos. Esto previene de forma absoluta las condiciones de carrera (Race Conditions) y los interbloqueos (Deadlocks) por reentrada, optimizando el rendimiento general del sistema (throughput) y garantizando que el servidor responda de manera instantánea a las peticiones del cliente sin experimentar congelamientos en la interfaz


* 
**Vaciado de Buffer (Flush):** Las salidas estándares en consola incorporan el argumento `flush=True` para mitigar la retención pasiva de E/S en la memoria RAM impuesta por la gestión de buffers de Windows, asegurando telemetría en tiempo real.

---

## 🛠️ Troubleshooting: Sincronización I/O en Entornos Híbridos (WSL/Windows)

Durante el desarrollo del sistema de transferencia concurrente, se detectó un problema crítico de bloqueo (*hang*) visual en la consola de PowerShell al procesar lotes de archivos concurrentes a través de WSL.

### El Problema
Cuando el directorio de entrada contenía archivos, los hilos secundarios procesaban, movían los elementos con éxito y escribían sus logs individuales en el disco. Sin embargo, al finalizar las tareas, el **hilo principal se quedaba suspendido de forma indefinida**. El script nunca llegaba a ejecutar las líneas de feedback finales ni el método de salida (`os._exit(0)`), impidiendo que el prompt de la terminal se liberara automáticamente.

**¿Por qué ocurría esto?**
1. **Deadlock de Exclusión Mutua (Lock):** Se invocaba el método de logging (que adquiere el candado `self.lock`) dentro de bloques de código que ya retenían el mismo lock en el hilo secundario, generando un interbloqueo sutil al cruzarse con operaciones pesadas de I/O.
2. **Latencia del Sistema de Archivos Cruzado (DrvFS a NTFS):** La transferencia física con `shutil.move()` desde el entorno Linux de WSL hacia el host de Windows genera una cola de operaciones en el kernel. El hilo principal rompía el ciclo de espera e intentaba matar el proceso (`os._exit()`) mientras los descriptores de archivos (`fd`) y los buffers de salida (`stdout`) de la consola aún no se habían purgado del todo, congelando la interfaz de PowerShell.

### La Solución
Se reestructuró quirúrgicamente el flujo de sincronización en el archivo `demonio.py` aplicando los siguientes cambios:

* **Desacoplamiento de Locks:** Se aislaron las llamadas a `registrar_log()` fuera de los contextos críticos concurrentes de los hilos, eliminando la contención y el riesgo de deadlock.
* **Espera Dinámica Eficiente en RAM:** Se optimizó el bucle de monitoreo del hilo principal sobre el conjunto `self.archivos_en_proceso`, implementando un delay de control de `50ms` (`time.sleep(0.05)`) que balancea el uso de CPU (i7) sin perder reactividad.
* **Ventana de Purga para el Kernel (Flush Cooldown):** Se añadió un retraso estratégico de `100ms` (`time.sleep(0.1)`) inmediatamente después de forzar el vaciado del buffer de salida (`sys.stdout.flush()`) y justo antes del cierre fulminante del script. Esto garantiza que WSL termine de transferir hasta el último byte visual a PowerShell antes de liberar la consola.
* **Formateador de Bloques Secuenciales:** Se adaptó el método de escritura para desglosar strings multilínea en escrituras atómicas, asegurando que el archivo `registro.log` mantenga marcas de tiempo uniformes y limpias.

---

## 👥 Integrantes del Grupo

* Rodrigo Collao 

* Cristián Contreras 

* Gabriel Muñoz 

* Aidan Reid 

* Pablo Monardes 


