"""Ejecuta la interfaz con resultados de muestra e historial persistente."""

import json
from pathlib import Path

from interfaz import iniciar_interfaz


EJEMPLOS = {
    ("+", 2.5, 3): 5.5,
    ("-", 7, 3): 4,
    ("*", 7, 3): 21,
    ("/", 7, 2): 3.5,
    ("**", 2, 3): 8,
    ("raiz", 81, None): 9,
}

ARCHIVO_HISTORIAL = Path.home() / ".calculadora-grafica" / "historial.json"


def calcular(operacion, a, b=None):
    """Devuelve el resultado prefijado de uno de los ejemplos de la consigna."""
    if operacion == "/" and b == 0:
        raise ValueError("No se puede dividir entre cero.")
    if operacion == "raiz" and a < 0:
        raise ValueError("La raíz cuadrada requiere un número mayor o igual a cero.")
    try:
        return EJEMPLOS[operacion, a, b]
    except KeyError:
        raise ValueError("Usa uno de los ejemplos de la demo que aparecen en la terminal.") from None


def agregar(historial, texto):
    """Registra y persiste una operación sin límite de elementos."""
    historial.append(texto)
    ARCHIVO_HISTORIAL.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO_HISTORIAL.write_text(
        json.dumps(historial, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def listar(historial):
    """Carga todas las operaciones y devuelve las más recientes primero."""
    try:
        registros = json.loads(ARCHIVO_HISTORIAL.read_text(encoding="utf-8"))
        if not isinstance(registros, list):
            registros = []
    except (OSError, json.JSONDecodeError):
        registros = []
    historial[:] = [str(registro) for registro in registros]
    return historial[::-1]


def limpiar(historial):
    """Vacía el historial en memoria y en el almacenamiento local."""
    historial.clear()
    ARCHIVO_HISTORIAL.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO_HISTORIAL.write_text("[]", encoding="utf-8")


if __name__ == "__main__":
    print("Ejemplos de la demo: 2.5 + 3, 7 − 3, 7 × 3, 7 ÷ 2, 2 ^ 3 y √81.")
    iniciar_interfaz(calcular, agregar, listar, limpiar)
