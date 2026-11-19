"""Ejecuta la interfaz con resultados de muestra y un historial temporal."""

from interfaz import iniciar_interfaz


EJEMPLOS = {
    ("+", 2.5, 3): 5.5,
    ("-", 7, 3): 4,
    ("*", 7, 3): 21,
    ("/", 7, 2): 3.5,
    ("**", 2, 3): 8,
    ("raiz", 81, None): 9,
}


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
    """Registra una fila en el historial temporal de la demo."""
    historial.append(texto)
    del historial[:-5]


def listar(historial):
    """Devuelve una copia con el cálculo más reciente primero."""
    return historial[::-1]


def limpiar(historial):
    """Vacía el historial temporal de la demo."""
    historial.clear()


if __name__ == "__main__":
    print("Ejemplos de la demo: 2.5 + 3, 7 − 3, 7 × 3, 7 ÷ 2, 2 ^ 3 y √81.")
    iniciar_interfaz(calcular, agregar, listar, limpiar)
