from __future__ import annotations

import os
import random
import string
import threading
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - solo para sistemas no POSIX
    fcntl = None


_fallback_lock = threading.Lock()


NOMBRE_BASE = "servidor_archivos"
NOMBRE_LOCK_FS = ".fs.lock"
NOMBRE_LOCK_LOG = ".log.lock"


def obtener_directorio_base() -> Path:
    return Path.home() / NOMBRE_BASE


def obtener_rutas() -> dict[str, Path]:
    base_dir = obtener_directorio_base()
    return {
        "base": base_dir,
        "entrada": base_dir / "entrada",
        "procesados": base_dir / "procesados",
        "logs": base_dir / "logs",
        "registro": base_dir / "logs" / "registro.log",
        "lock_fs": base_dir / NOMBRE_LOCK_FS,
        "lock_log": base_dir / NOMBRE_LOCK_LOG,
    }


def aplicar_permisos(path: Path, modo: int) -> None:
    if os.name == "posix":
        try:
            os.chmod(path, modo)
        except PermissionError:
            pass


def crear_contenido_aleatorio(longitud: int = 8) -> str:
    letras = string.ascii_letters + string.digits
    return "".join(random.choice(letras) for _ in range(longitud))


def crear_archivos_prueba(entrada_dir: Path) -> list[Path]:
    entrada_dir.mkdir(parents=True, exist_ok=True)
    archivos_creados: list[Path] = []
    existentes = {archivo.name for archivo in entrada_dir.glob("*.txt")}

    for indice in range(1, 4):
        nombre_archivo = f"prueba_{indice}.txt"
        if nombre_archivo in existentes:
            continue

        contenido = [
            f"Archivo de prueba {indice}",
            f"Identificador: {crear_contenido_aleatorio(12)}",
            f"Linea aleatoria: {crear_contenido_aleatorio(24)}",
        ]
        ruta_archivo = entrada_dir / nombre_archivo
        ruta_archivo.write_text("\n".join(contenido) + "\n", encoding="utf-8")
        aplicar_permisos(ruta_archivo, 0o600)
        archivos_creados.append(ruta_archivo)

    return archivos_creados


def preparar_entorno() -> dict[str, Path]:
    rutas = obtener_rutas()
    rutas["base"].mkdir(parents=True, exist_ok=True)
    rutas["entrada"].mkdir(parents=True, exist_ok=True)
    rutas["procesados"].mkdir(parents=True, exist_ok=True)
    rutas["logs"].mkdir(parents=True, exist_ok=True)

    aplicar_permisos(rutas["base"], 0o700)
    aplicar_permisos(rutas["entrada"], 0o700)
    aplicar_permisos(rutas["procesados"], 0o700)
    aplicar_permisos(rutas["logs"], 0o700)

    if not rutas["registro"].exists():
        rutas["registro"].write_text("", encoding="utf-8")
    aplicar_permisos(rutas["registro"], 0o600)

    crear_archivos_prueba(rutas["entrada"])
    return rutas


@contextmanager
def bloqueo_interprocesos(ruta_lock: Path):
    ruta_lock.parent.mkdir(parents=True, exist_ok=True)

    if fcntl is None:
        with _fallback_lock:
            yield
        return

    with open(ruta_lock, "a+", encoding="utf-8") as descriptor_lock:
        fcntl.flock(descriptor_lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(descriptor_lock, fcntl.LOCK_UN)