"""Interfaz de la calculadora. Los módulos se conectan mediante callbacks."""

import math
import time
import tkinter as tk
from tkinter import font, ttk


FONDO = "#131510"
PANEL = "#1a1d16"
SUPERFICIE = "#22261d"
BORDE = "#373d2e"
TEXTO = "#f0f2e9"
SECUNDARIO = "#b5bdae"
LIMA = "#d9fa77"
LAVA = "#c6b8fa"
ERROR = "#ffafa9"

OPERACIONES = (
    ("+", "+", "Suma"),
    ("-", "−", "Resta"),
    ("*", "×", "Multiplicación"),
    ("/", "÷", "División"),
    ("**", "xʸ", "Potencia"),
    ("raiz", "√", "Raíz cuadrada"),
)


def _fuentes(ventana):
    disponibles = set(font.families(ventana))
    tipografia = next(
        (nombre for nombre in ("Avenir Next", "Segoe UI", "DejaVu Sans")
         if nombre in disponibles),
        font.nametofont("TkDefaultFont").actual("family"),
    )
    mono = next(
        (nombre for nombre in ("Menlo", "Consolas", "DejaVu Sans Mono")
         if nombre in disponibles),
        font.nametofont("TkFixedFont").actual("family"),
    )
    return tipografia, mono


def _formato(numero):
    return str(numero) if isinstance(numero, int) else format(numero, ".12g")


def _color(desde, hasta, avance):
    origen = bytes.fromhex(desde[1:])
    destino = bytes.fromhex(hasta[1:])
    canales = bytes(round(a + (b - a) * avance) for a, b in zip(origen, destino))
    return "#" + canales.hex()


class _Movimiento:
    """Anima acentos con una curva de salida cúbica en el bucle de Tk."""

    def __init__(self, ventana):
        self.ventana = ventana
        self.pistas = {}
        self.temporizador = None

    def iniciar(self, nombre, duracion, dibujar):
        self.pistas[nombre] = (time.monotonic(), duracion, dibujar)
        dibujar(0)
        if self.temporizador is None:
            self.temporizador = self.ventana.after(16, self._paso)

    def _paso(self):
        self.temporizador = None
        ahora = time.monotonic()
        for nombre, (inicio, duracion, dibujar) in list(self.pistas.items()):
            avance = min((ahora - inicio) / duracion, 1)
            dibujar(1 - (1 - avance) ** 3)
            if avance == 1:
                del self.pistas[nombre]
        if self.pistas:
            self.temporizador = self.ventana.after(16, self._paso)

    def detener(self, nombre):
        self.pistas.pop(nombre, None)

    def cerrar(self):
        if self.temporizador is not None:
            self.ventana.after_cancel(self.temporizador)
        self.pistas.clear()
        self.ventana.destroy()


class _Calculadora:
    def __init__(self, ventana, calcular, agregar, listar, limpiar):
        self.ventana = ventana
        self.calcular = calcular
        self.agregar = agregar
        self.listar = listar
        self.limpiar = limpiar
        self.historial = []

        self.primero = tk.StringVar(ventana)
        self.segundo = tk.StringVar(ventana)
        self.operacion = tk.StringVar(ventana, value="+")
        self.resultado = tk.StringVar(ventana, value="—")
        self.detalle = tk.StringVar(ventana, value="Aquí verás el resultado del cálculo.")
        self.mensaje = tk.StringVar(ventana)

        self.familia, self.mono = _fuentes(ventana)
        self.movimiento = _Movimiento(ventana)
        self.colores_estado = "#56634b"
        self._estilos()
        self._construir()
        self._seleccionar_operacion()
        self._actualizar_historial()

        self.ventana.protocol("WM_DELETE_WINDOW", self.movimiento.cerrar)
        for entrada in (self.entrada_a, self.entrada_b):
            entrada.bind("<Return>", self._enviar_desde_entrada)
            entrada.bind("<KP_Enter>", self._enviar_desde_entrada)
        self.ventana.after_idle(self.entrada_a.focus_set)

    def _estilos(self):
        estilos = ttk.Style(self.ventana)
        estilos.theme_use("clam")
        estilos.configure(
            "Eje.TEntry", fieldbackground=SUPERFICIE, foreground=TEXTO,
            insertcolor=LIMA, bordercolor=BORDE, lightcolor=SUPERFICIE,
            darkcolor=SUPERFICIE, padding=(12, 9), font=(self.mono, 15),
        )
        estilos.map("Eje.TEntry", bordercolor=[
            ("invalid", ERROR), ("focus", LIMA)
        ])
        estilos.configure(
            "Eje.TButton", background=SUPERFICIE, foreground=TEXTO,
            bordercolor=BORDE, lightcolor=SUPERFICIE, darkcolor=SUPERFICIE,
            focuscolor=LIMA, font=(self.familia, 11, "bold"), padding=(9, 6),
        )
        estilos.map("Eje.TButton", background=[
            ("pressed", "#354229"), ("active", "#2b3324")
        ], bordercolor=[("focus", LIMA), ("active", "#65734f")])
        estilos.configure(
            "Primario.Eje.TButton", background=LIMA, foreground="#151c0d",
            bordercolor=LIMA, lightcolor=LIMA, darkcolor=LIMA,
            focuscolor="#3a4d1b", font=(self.familia, 13, "bold"), padding=(14, 9),
        )
        estilos.map("Primario.Eje.TButton", background=[
            ("pressed", "#b8dc52"), ("active", "#e5ff9b")
        ])
        estilos.configure(
            "Secundario.Eje.TButton", background=PANEL, foreground=SECUNDARIO,
            lightcolor=PANEL, darkcolor=PANEL, font=(self.familia, 10, "bold"),
            padding=(8, 4),
        )
        estilos.map("Secundario.Eje.TButton", foreground=[
            ("disabled", "#a1aa99"), ("active", TEXTO)
        ], background=[("active", SUPERFICIE)])

        estilos.layout("Operacion.TRadiobutton", [
            ("Radiobutton.border", {"sticky": "nswe", "children": [
                ("Radiobutton.padding", {"sticky": "nswe", "children": [
                    ("Radiobutton.focus", {"sticky": "nswe", "children": [
                        ("Radiobutton.label", {"sticky": ""}),
                    ]}),
                ]}),
            ]}),
        ])
        estilos.configure(
            "Operacion.TRadiobutton", background=SUPERFICIE, foreground=SECUNDARIO,
            borderwidth=1, bordercolor=BORDE, relief="flat",
            lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, padding=(8, 6),
            focuscolor=LIMA, font=(self.familia, 11, "bold"),
        )
        estilos.map(
            "Operacion.TRadiobutton",
            background=[("selected", "#333d22"), ("active", "#2b3225")],
            foreground=[("selected", LIMA), ("active", TEXTO)],
            bordercolor=[("focus", LIMA), ("selected", "#70834b")],
        )

    def _etiqueta(self, padre, texto="", tamano=12, color=TEXTO,
                  fondo=PANEL, peso="normal", variable=None, mono=False, **opciones):
        return tk.Label(
            padre, text=texto, textvariable=variable, bg=fondo, fg=color,
            font=(self.mono if mono else self.familia, tamano, peso),
            anchor="w", borderwidth=0, padx=0, pady=0, **opciones,
        )

    def _construir(self):
        marco = tk.Frame(self.ventana, bg=FONDO, padx=28, pady=18)
        marco.pack(fill="both", expand=True)
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(3, weight=1)

        barra = tk.Frame(marco, bg=FONDO)
        barra.grid(row=0, column=0, sticky="ew")
        logo = tk.Canvas(barra, width=34, height=34, bg=LIMA, highlightthickness=0)
        logo.pack(side="left")
        logo.create_line(7, 23, 12, 23, 17, 11, 22, 25, 26, 17, 29, 17,
                         fill=FONDO, width=2, capstyle="round", joinstyle="round")
        self._etiqueta(barra, "eje.", 20, fondo=FONDO, peso="bold").pack(
            side="left", padx=(9, 0),
        )
        tk.Frame(marco, bg=BORDE, height=1).grid(
            row=1, column=0, sticky="ew", pady=(12, 13),
        )

        titulo = tk.Frame(marco, bg=FONDO)
        titulo.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self._etiqueta(titulo, "Calculadora", 32, fondo=FONDO, peso="bold").pack(
            anchor="w",
        )
        self._etiqueta(
            titulo, "Elige una operación e ingresa los valores.", 13, SECUNDARIO, FONDO,
        ).pack(anchor="w", pady=(2, 0))

        espacio = tk.Frame(marco, bg=FONDO)
        espacio.grid(row=3, column=0, sticky="nsew")
        espacio.grid_columnconfigure(0, weight=3, minsize=405)
        espacio.grid_columnconfigure(1, weight=2, minsize=245)
        espacio.grid_rowconfigure(0, weight=1)

        panel = self._panel(espacio)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        derecha = self._panel(espacio)
        derecha.grid(row=0, column=1, sticky="nsew")
        self._formulario(panel)
        self._crear_historial(derecha)

        pie = self._etiqueta(
            marco, "Intro  ·  Calcular desde un campo", 10, SECUNDARIO, FONDO,
        )
        pie.grid(row=4, column=0, sticky="w", pady=(9, 0))

    def _panel(self, padre):
        panel = tk.Frame(
            padre, bg=PANEL, highlightbackground=BORDE, highlightthickness=1,
            padx=17, pady=16,
        )
        panel.grid_columnconfigure(0, weight=1)
        return panel

    def _campo(self, padre, nombre, variable):
        grupo = tk.Frame(padre, bg=PANEL)
        grupo.grid_columnconfigure(0, weight=1)
        self._etiqueta(grupo, nombre, 11, SECUNDARIO, peso="bold").grid(
            row=0, column=0, sticky="w", pady=(0, 4),
        )
        entrada = ttk.Entry(
            grupo, textvariable=variable, style="Eje.TEntry", width=10,
            font=(self.mono, 15), takefocus=True,
        )
        entrada.grid(row=1, column=0, sticky="ew")
        return grupo, entrada

    def _formulario(self, panel):
        self._etiqueta(panel, "Operación", 16, peso="bold").grid(
            row=0, column=0, sticky="w", pady=(0, 8),
        )
        selector = tk.Frame(panel, bg=PANEL)
        selector.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.opciones = []
        for columna in range(3):
            selector.grid_columnconfigure(columna, weight=1, uniform="operaciones")
        for i, (identificador, simbolo, nombre) in enumerate(OPERACIONES):
            fila, columna = divmod(i, 3)
            boton = ttk.Radiobutton(
                selector, text=f"{simbolo}   {nombre}", value=identificador,
                variable=self.operacion, command=self._seleccionar_operacion,
                style="Operacion.TRadiobutton", takefocus=True,
            )
            boton.grid(row=fila, column=columna, sticky="ew",
                       padx=(0, 6 if columna < 2 else 0), pady=(0, 5))
            self.opciones.append(boton)
            for tecla, salto in (("Left", -1), ("Right", 1), ("Up", -3), ("Down", 3)):
                boton.bind(f"<{tecla}>",
                           lambda evento, indice=i, delta=salto:
                           self._navegar_operaciones(indice + delta))
            boton.bind("<Return>", lambda evento, tecla=boton: tecla.invoke())

        campos = tk.Frame(panel, bg=PANEL)
        campos.grid(row=2, column=0, sticky="ew")
        campos.grid_columnconfigure(0, weight=1, uniform="campos")
        campos.grid_columnconfigure(1, weight=1, uniform="campos")
        self.grupo_a, self.entrada_a = self._campo(campos, "Primer número", self.primero)
        self.grupo_b, self.entrada_b = self._campo(campos, "Segundo número", self.segundo)
        self.grupo_a.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        self.grupo_b.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        ttk.Button(
            panel, text="Calcular", command=self._ejecutar,
            style="Primario.Eje.TButton", takefocus=True,
        ).grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.error = self._etiqueta(panel, tamano=10, color=ERROR, variable=self.mensaje)
        self.error.grid(row=4, column=0, sticky="ew", pady=(3, 5))
        self.error.bind("<Configure>", self._ajustar_texto)
        self._tarjeta_resultado(panel)
        panel.grid_rowconfigure(5, weight=1)

    def _tarjeta_resultado(self, panel):
        tarjeta = tk.Frame(
            panel, bg=SUPERFICIE, highlightthickness=1, highlightbackground=BORDE,
            padx=13, pady=8,
        )
        tarjeta.grid(row=5, column=0, sticky="nsew")
        tarjeta.grid_columnconfigure(0, weight=1)
        tarjeta.grid_rowconfigure(1, weight=1)
        self._etiqueta(
            tarjeta, "Resultado", 11, SECUNDARIO, SUPERFICIE, "bold",
        ).grid(row=0, column=0, sticky="w")
        self.numero = self._etiqueta(
            tarjeta, tamano=26, fondo=SUPERFICIE, peso="bold",
            variable=self.resultado, mono=True,
        )
        self.fuente_resultado = font.Font(
            root=self.ventana, family=self.mono, size=26, weight="bold",
        )
        self.numero.configure(font=self.fuente_resultado)
        self.numero.grid(row=1, column=0, sticky="ew")
        self.numero.bind("<Configure>", self._ajustar_resultado)
        self.resultado.trace_add("write", self._ajustar_resultado)
        contexto = self._etiqueta(
            tarjeta, tamano=10, color=SECUNDARIO, fondo=SUPERFICIE, variable=self.detalle,
            justify="left",
        )
        contexto.grid(row=2, column=0, sticky="ew", pady=(2, 4))
        contexto.bind("<Configure>", self._ajustar_texto)
        self.indicador = tk.Canvas(
            tarjeta, height=3, width=84, bg=SUPERFICIE, highlightthickness=0,
        )
        self.indicador.grid(row=3, column=0, sticky="w")
        self.indicador.create_rectangle(0, 0, 84, 3, fill=BORDE, outline="")
        self.barra_resultado = self.indicador.create_rectangle(
            0, 0, 20, 3, fill=self.colores_estado, outline="",
        )

    def _crear_historial(self, panel):
        encabezado = tk.Frame(panel, bg=PANEL)
        encabezado.grid(row=0, column=0, sticky="ew")
        encabezado.grid_columnconfigure(0, weight=1)
        self._etiqueta(encabezado, "Historial", 16, peso="bold").grid(
            row=0, column=0, sticky="w", pady=(0, 2),
        )
        self.contador = self._etiqueta(
            encabezado, tamano=10, color=LAVA, fondo=SUPERFICIE, mono=True,
        )
        self.contador.configure(padx=7, pady=3)
        self.contador.grid(row=0, column=1, sticky="e")
        self._etiqueta(panel, "Últimos cinco cálculos", 11, SECUNDARIO).grid(
            row=1, column=0, sticky="w", pady=(2, 13),
        )
        panel.grid_rowconfigure(2, weight=1)
        cuerpo = tk.Frame(panel, bg=PANEL)
        cuerpo.grid(row=2, column=0, sticky="nsew")
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        self.vacio = tk.Frame(cuerpo, bg=SUPERFICIE, padx=10, pady=8)
        self.vacio.grid(row=0, column=0, sticky="nsew")
        centro = tk.Frame(self.vacio, bg=SUPERFICIE)
        centro.place(relx=.5, rely=.5, anchor="center", relwidth=.94)
        reloj = tk.Canvas(centro, width=36, height=36, bg=SUPERFICIE, highlightthickness=0)
        reloj.pack(pady=(0, 9))
        reloj.create_oval(5, 5, 31, 31, outline=LAVA, width=1.5)
        reloj.create_line(18, 11, 18, 18, 23, 21, fill=LAVA, width=1.5,
                          capstyle="round", joinstyle="round")
        self._etiqueta(
            centro, "Sin operaciones todavía", 12, TEXTO, SUPERFICIE, "bold",
        ).pack()
        self._etiqueta(
            centro, "Tus cálculos aparecerán aquí.", 10, SECUNDARIO, SUPERFICIE,
        ).pack(pady=(3, 0))

        self.filas = tk.Frame(cuerpo, bg=PANEL)
        self.filas.grid(row=0, column=0, sticky="nsew")
        self.filas.grid_columnconfigure(0, weight=1)

        self.borrar = ttk.Button(
            panel, text="Borrar historial", command=self._borrar_historial,
            style="Secundario.Eje.TButton", takefocus=True,
        )
        self.borrar.grid(row=3, column=0, sticky="ew", pady=(12, 0))

    def _seleccionar_operacion(self):
        es_raiz = self.operacion.get() == "raiz"
        if es_raiz:
            self.grupo_b.grid_remove()
            self.grupo_a.grid_configure(columnspan=2, padx=0)
        else:
            self.grupo_a.grid_configure(columnspan=1, padx=(0, 4))
            self.grupo_b.grid()
        self._limpiar_error()

    def _navegar_operaciones(self, destino):
        boton = self.opciones[destino % len(self.opciones)]
        boton.focus_set()
        boton.invoke()
        return "break"

    def _ajustar_texto(self, evento):
        ancho = max(evento.width - 3, 1)
        if int(evento.widget.cget("wraplength")) != ancho:
            evento.widget.configure(wraplength=ancho)

    def _ajustar_resultado(self, *_):
        ancho = self.numero.winfo_width()
        if ancho <= 1:
            return
        texto = self.resultado.get()
        for tamano in range(26, 12, -1):
            self.fuente_resultado.configure(size=tamano)
            if self.fuente_resultado.measure(texto) <= ancho - 3:
                break

    def _leer(self, variable, entrada, ordinal):
        texto = variable.get().strip().replace(",", ".")
        try:
            numero = float(texto)
            if not math.isfinite(numero):
                raise ValueError
        except ValueError:
            entrada.state(["invalid"])
            entrada.focus_set()
            raise ValueError(f"Ingresa un número válido en el {ordinal} campo.") from None
        return numero

    def _limpiar_error(self):
        self.mensaje.set("")
        self.entrada_a.state(["!invalid"])
        self.entrada_b.state(["!invalid"])

    def _enviar_desde_entrada(self, _evento):
        self._ejecutar()
        return "break"

    def _ejecutar(self):
        self._limpiar_error()
        operacion = self.operacion.get()
        try:
            a = self._leer(self.primero, self.entrada_a, "primer")
            if operacion == "raiz":
                expresion = f"√{_formato(a)}"
                valor = self.calcular(operacion, a)
            else:
                b = self._leer(self.segundo, self.entrada_b, "segundo")
                simbolo = next(simbolo for clave, simbolo, _ in OPERACIONES if clave == operacion)
                expresion = f"{_formato(a)} {simbolo if operacion != '**' else '^'} {_formato(b)}"
                valor = self.calcular(operacion, a, b)
            if isinstance(valor, complex) or not math.isfinite(valor):
                raise ValueError("El resultado no es un número real finito.")
        except ValueError as error:
            self._mostrar_error(str(error) or "Revisa los valores de la operación.")
            return
        except OverflowError:
            self._mostrar_error("El resultado es demasiado grande.")
            return
        except ZeroDivisionError:
            self._mostrar_error("No se puede dividir entre cero.")
            return

        numero = _formato(valor)
        self.agregar(self.historial, f"{expresion} = {numero}")
        self.detalle.set(expresion)
        self.resultado.set(numero)
        self._actualizar_historial()
        self.movimiento.iniciar("resultado", .26, self._animar_resultado)

    def _mostrar_error(self, texto):
        self.movimiento.detener("resultado")
        self.mensaje.set(texto)
        self.indicador.coords(self.barra_resultado, 0, 0, 20, 3)
        self.indicador.itemconfigure(self.barra_resultado, fill=ERROR)
        self.numero.configure(fg=TEXTO)

    def _animar_resultado(self, avance):
        ancho = 20 + 64 * avance
        self.indicador.coords(self.barra_resultado, 0, 0, ancho, 3)
        self.indicador.itemconfigure(
            self.barra_resultado, fill=_color(self.colores_estado, LIMA, avance),
        )
        self.numero.configure(fg=_color(TEXTO, LIMA, avance))

    def _actualizar_historial(self):
        items = self.listar(self.historial)
        self.contador.configure(text=f"{len(items)} / 5")
        self.borrar.state(["!disabled"] if items else ["disabled"])
        for fila in self.filas.winfo_children():
            fila.destroy()
        if not items:
            self.filas.grid_remove()
            self.vacio.grid()
            return
        self.vacio.grid_remove()
        self.filas.grid()
        for i, registro in enumerate(items):
            expresion, separador, resultado = str(registro).rpartition(" = ")
            fila = tk.Frame(self.filas, bg=SUPERFICIE, padx=9, pady=7)
            fila.grid(row=i, column=0, sticky="ew", pady=(0, 5))
            fila.grid_columnconfigure(0, weight=1)
            operacion = self._etiqueta(
                fila, expresion if separador else resultado, 11, SECUNDARIO, SUPERFICIE,
                mono=True, justify="left",
            )
            operacion.grid(row=0, column=0, sticky="ew")
            operacion.bind("<Configure>", self._ajustar_texto)
            if separador:
                valor = self._etiqueta(
                    fila, f"= {resultado}", 11, LIMA if i == 0 else TEXTO,
                    SUPERFICIE, "bold", mono=True, justify="left",
                )
                valor.grid(row=1, column=0, sticky="ew", pady=(2, 0))
                valor.bind("<Configure>", self._ajustar_texto)

    def _borrar_historial(self):
        self.limpiar(self.historial)
        self._actualizar_historial()
        self.entrada_a.focus_set()


def iniciar_interfaz(calcular, agregar, listar, limpiar):
    """Abre la ventana y recibe las operaciones y el historial del equipo."""
    ventana = tk.Tk()
    ventana.title("Eje · Calculadora")
    ventana.configure(bg=FONDO)
    ancho = min(970, ventana.winfo_screenwidth() - 32)
    alto = min(690, ventana.winfo_screenheight() - 60)
    ventana.geometry(f"{ancho}x{alto}")
    ventana.minsize(min(ancho, 750), min(alto, 580))
    _Calculadora(ventana, calcular, agregar, listar, limpiar)
    ventana.mainloop()
