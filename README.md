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

### Paso 1: Configurar el entorno local y permisos (Linux/WSL)

Cree los directorios necesarios y aplique la política de exclusión de acceso a usuarios externos:

```bash
mkdir -p ~/servidor_archivos/entrada ~/servidor_archivos/procesados ~/servidor_archivos/logs
chmod 700 ~/servidor_archivos

```

### Paso 2: Levantar el Servidor Central

Abra una terminal en la raíz del proyecto e inicialice el backend de red:

```bash
python -u servidor.py

```

### Paso 3: Activar el Demonio de Monitoreo

Abra una segunda terminal en paralelo y ejecute el proceso de background:

```bash
python -u demonio.py

```

### Paso 4: Inicializar Clientes Interactivos

Abra terminales adicionales (hasta 4 para pruebas de estrés de concurrencia completa) y ejecute la interfaz de usuario:

```bash
python cliente.py

```

---

## 🔒 Mecanismos de Sincronización Implementados

* 
**Exclusión Mutua (Mutex):** Se implementó `threading.Lock()` para asegurar la atomicidad en la sección crítica del código. Esto previene las condiciones de carrera (Race Conditions) cuando los clientes y el demonio acceden en paralelo al archivo compartido de auditoría (`registro.log`) o manipulan directorios simultáneamente.


* 
**Vaciado de Buffer (Flush):** Las salidas estándares en consola incorporan el argumento `flush=True` para mitigar la retención pasiva de E/S en la memoria RAM impuesta por la gestión de buffers de Windows, asegurando telemetría en tiempo real.



---

## 👥 Integrantes del Grupo

* Rodrigo Collao 

* Cristián Contreras 

* Gabriel Muñoz 

* Aidan Reid 

* Pablo Monardes 


