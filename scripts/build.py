"""Genera los SVG del perfil de GitHub (tema claro y oscuro).

Uso:
    python scripts/build.py          # todo
    python scripts/build.py estatico # banner, proyectos y pie
    python scripts/build.py stats    # solo la tarjeta de actividad (pide la API)

La tarjeta de actividad lee la API GraphQL con GITHUB_TOKEN; si no existe,
usa `gh auth token`. Solo usa la biblioteca estándar.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

USUARIO = "ALEDEROSEE"
RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

TEMAS = {
    "dark": {
        "bg0": "#0b0e1a", "bg1": "#14183a", "borde": "#272c52",
        "texto": "#eef1f8", "suave": "#a3abc0", "tenue": "#6f7790",
        "chip_bg": "#161a33", "chip_borde": "#343a6c", "chip_texto": "#d3d8fb",
        "a1": "#9b7bff", "a2": "#d65bf0", "a3": "#ff6b7a",
        "puntos": "#ffffff", "puntos_op": "0.07",
        "orbe_op": "0.45",
        "ventana": "#161a35", "ventana_borde": "#2c3260", "barra": "#1d2244",
        "telefono": "#05060c", "pantalla": "#0f1228", "item": "#1a1f40", "linea": "#2c3366",
        "tarjeta": "#0f1324", "tarjeta_borde": "#252a45", "brillo_op": "0.24",
        "pista": "#20253f",
    },
    "light": {
        "bg0": "#ffffff", "bg1": "#f3efff", "borde": "#e2dbfa",
        "texto": "#1f2328", "suave": "#57606a", "tenue": "#8a929c",
        "chip_bg": "#f6f3ff", "chip_borde": "#dcd2fb", "chip_texto": "#5236c9",
        "a1": "#6a3df0", "a2": "#a512c4", "a3": "#d6334a",
        "puntos": "#5236c9", "puntos_op": "0.10",
        "orbe_op": "0.22",
        "ventana": "#ffffff", "ventana_borde": "#e2dbfa", "barra": "#f4f1fd",
        "telefono": "#1f2233", "pantalla": "#f7f5ff", "item": "#ffffff", "linea": "#e4ddfb",
        "tarjeta": "#ffffff", "tarjeta_borde": "#e3e1ee", "brillo_op": "0.11",
        "pista": "#ece9f6",
    },
}

ESTILO_BASE = f"""
.sans{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
"""


def guardar(nombre: str, svg: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / nombre).write_text(svg.strip() + "\n", encoding="utf-8")
    print("  -", nombre)


def gradiente_acento(t: dict, gid: str = "acc", x2: str = "1", y2: str = "0") -> str:
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="{t["a1"]}"/>'
        f'<stop offset="0.55" stop-color="{t["a2"]}"/>'
        f'<stop offset="1" stop-color="{t["a3"]}"/></linearGradient>'
    )


def ancho_texto(texto: str, px: float, factor: float = 0.6) -> float:
    return len(texto) * px * factor


# ─────────────────────────────── Banner ────────────────────────────────

FRASES = [
    "Apps Android con Kotlin y Jetpack Compose",
    "Interfaces web con React, Vite y Tailwind",
    "APIs REST con Django y Spring Boot",
    "Prototipos IoT con ESP32 y MQTT",
]

CHIPS = ["Kotlin", "Jetpack Compose", "React", "Django", "Spring Boot", "Docker"]


def frases_animadas(t: dict, x: float, y: float, px: float) -> str:
    """Efecto de escritura: cada frase se revela, se queda y se borra."""
    n, ciclo = len(FRASES), 18.0
    paso = 1.0 / n
    partes = []
    for i, frase in enumerate(FRASES):
        ancho = round(len(frase) * px * 0.6, 1)
        a = i * paso
        b = a + paso * 0.32
        c = a + paso * 0.86
        d = a + paso * 0.96
        tiempos = f"0;{a:.4f};{b:.4f};{c:.4f};{d:.4f};1"
        valores = f"0;0;{ancho};{ancho};0;0"
        partes.append(f"""
  <clipPath id="frase{i}"><rect x="{x}" y="{y - px}" height="{px * 1.6}" width="0">
    <animate attributeName="width" dur="{ciclo}s" repeatCount="indefinite"
      keyTimes="{tiempos}" values="{valores}"/></rect></clipPath>
  <text class="mono" x="{x}" y="{y}" font-size="{px}" fill="{t['texto']}" textLength="{ancho}"
    lengthAdjust="spacing" clip-path="url(#frase{i})">{escape(frase)}</text>
  <rect class="cursor" x="{x}" y="{y - px * 0.82}" width="{px * 0.55:.1f}" height="{px * 1.05:.1f}" rx="1.5" fill="{t['a2']}" opacity="0">
    <animate attributeName="x" dur="{ciclo}s" repeatCount="indefinite"
      keyTimes="{tiempos}" values="{x};{x};{x + ancho + 4};{x + ancho + 4};{x};{x}"/>
    <animate attributeName="opacity" dur="{ciclo}s" repeatCount="indefinite" calcMode="discrete"
      keyTimes="0;{a:.4f};{d:.4f}" values="0;1;0"/>
  </rect>""")
    return "".join(partes)


def chips(t: dict, x: float, y: float) -> str:
    out, cx = [], x
    for nombre in CHIPS:
        w = ancho_texto(nombre, 13.5, 0.58) + 30
        out.append(
            f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="34" rx="17" fill="{t["chip_bg"]}" stroke="{t["chip_borde"]}"/>'
            f'<text class="sans" x="{cx + w / 2:.1f}" y="{y + 22}" font-size="13.5" font-weight="600" '
            f'text-anchor="middle" fill="{t["chip_texto"]}">{escape(nombre)}</text>'
        )
        cx += w + 10
    return "".join(out)


def ilustracion(t: dict) -> str:
    """Ventana de navegador con código + teléfono con una app en Compose."""
    lineas = [
        (0, 58, "a1"), (16, 96, "suave"), (16, 70, "a2"), (32, 120, "suave"),
        (32, 54, "a3"), (16, 84, "a1"), (0, 30, "suave"), (0, 74, "a2"),
    ]
    codigo = []
    for i, (sangria, ancho, color) in enumerate(lineas):
        y = 140 + i * 17
        fill = t[color]
        op = "0.55" if color == "suave" else "0.95"
        codigo.append(
            f'<rect x="{812 + sangria}" y="{y}" width="{ancho}" height="7" rx="3.5" fill="{fill}" opacity="{op}"/>'
        )
    codigo.append(
        f'<rect class="parpadeo" x="{812 + 78}" y="{140 + 7 * 17 - 3}" width="7" height="13" rx="1.5" fill="{t["a2"]}"/>'
    )
    items = []
    for i in range(3):
        y = 210 + i * 40
        items.append(
            f'<g class="aparece" style="animation-delay:{i * 0.25:.2f}s">'
            f'<rect x="1004" y="{y}" width="122" height="32" rx="9" fill="{t["item"]}" stroke="{t["linea"]}"/>'
            f'<circle cx="1019" cy="{y + 16}" r="7" fill="{t[("a1", "a2", "a3")[i]]}" opacity="0.9"/>'
            f'<rect x="1032" y="{y + 9}" width="{(62, 50, 70)[i]}" height="5" rx="2.5" fill="{t["suave"]}" opacity="0.7"/>'
            f'<rect x="1032" y="{y + 19}" width="{(40, 56, 34)[i]}" height="4" rx="2" fill="{t["suave"]}" opacity="0.4"/>'
            "</g>"
        )
    return f"""
<g class="flota2">
  <rect x="790" y="96" width="265" height="200" rx="14" fill="{t['ventana']}" stroke="{t['ventana_borde']}"/>
  <path d="M790 124 V110 a14 14 0 0 1 14 -14 H1041 a14 14 0 0 1 14 14 V124 Z" fill="{t['barra']}"/>
  <circle cx="808" cy="110" r="4.5" fill="#ff5f57"/><circle cx="823" cy="110" r="4.5" fill="#febc2e"/>
  <circle cx="838" cy="110" r="4.5" fill="#28c840"/>
  <rect x="856" y="103" width="120" height="14" rx="7" fill="{t['ventana']}" opacity="0.9"/>
  {''.join(codigo)}
</g>
<g class="flota1">
  <rect x="990" y="56" width="152" height="300" rx="28" fill="{t['telefono']}"/>
  <rect x="997" y="63" width="138" height="286" rx="22" fill="{t['pantalla']}"/>
  <circle cx="1066" cy="76" r="4" fill="{t['telefono']}"/>
  <rect x="1004" y="92" width="58" height="7" rx="3.5" fill="{t['texto']}" opacity="0.75"/>
  <rect x="1004" y="112" width="122" height="84" rx="14" fill="url(#acc2)"/>
  <rect x="1016" y="128" width="52" height="7" rx="3.5" fill="#ffffff" opacity="0.95"/>
  <rect x="1016" y="142" width="82" height="5" rx="2.5" fill="#ffffff" opacity="0.6"/>
  <rect x="1016" y="168" width="40" height="16" rx="8" fill="#ffffff" opacity="0.25"/>
  {''.join(items)}
  <circle cx="1112" cy="322" r="15" fill="url(#acc)"/>
  <path d="M1112 315 v14 M1105 322 h14" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round"/>
</g>"""


def banner(t: dict) -> str:
    W, H = 1200, 400
    pin = (
        "M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7zm0 9.5"
        "A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"
    )
    gorro = "M12 3 1 9l11 6 9-4.9V17h2V9L12 3zM5 13.2v4L12 21l7-3.8v-4L12 17l-7-3.8z"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
  aria-label="Alejandro Alvarez Sayaverde, desarrollador Android y web en Arequipa, Perú">
<title>Alejandro Alvarez Sayaverde · Desarrollador Android y Web</title>
<style>{ESTILO_BASE}
.flota1{{animation:flota 7s ease-in-out infinite}}
.flota2{{animation:flota 7s ease-in-out -3.5s infinite}}
.orbeA{{animation:deriva 18s ease-in-out infinite}}
.orbeB{{animation:deriva 22s ease-in-out -8s infinite reverse}}
.parpadeo{{animation:parpadeo 1.1s steps(1) infinite}}
.aparece{{animation:aparece .8s ease-out both}}
@keyframes flota{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-9px)}}}}
@keyframes deriva{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(-40px,26px)}}}}
@keyframes parpadeo{{0%{{opacity:1}}50%{{opacity:0}}}}
@keyframes aparece{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
</style>
<defs>
  <linearGradient id="fondo" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{t['bg0']}"/><stop offset="1" stop-color="{t['bg1']}"/></linearGradient>
  {gradiente_acento(t)}
  {gradiente_acento(t, "acc2", "1", "1")}
  <filter id="desenfoque" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="70"/></filter>
  <pattern id="rejilla" width="26" height="26" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1.3" fill="{t['puntos']}"/></pattern>
  <radialGradient id="desvanece" cx="0.78" cy="0.35" r="0.7">
    <stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
  <mask id="mascara"><rect width="{W}" height="{H}" fill="url(#desvanece)"/></mask>
  <clipPath id="marco"><rect width="{W}" height="{H}" rx="24"/></clipPath>
</defs>
<g clip-path="url(#marco)">
  <rect width="{W}" height="{H}" fill="url(#fondo)"/>
  <g opacity="{t['orbe_op']}" filter="url(#desenfoque)">
    <circle class="orbeA" cx="1010" cy="90" r="150" fill="{t['a1']}"/>
    <circle class="orbeB" cx="1150" cy="360" r="120" fill="{t['a3']}"/>
    <circle class="orbeA" cx="560" cy="430" r="140" fill="{t['a2']}" opacity="0.6"/>
  </g>
  <rect width="{W}" height="{H}" fill="url(#rejilla)" opacity="{t['puntos_op']}" mask="url(#mascara)"/>
  {ilustracion(t)}
</g>
<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="23.5" fill="none" stroke="{t['borde']}" stroke-width="1.5"/>

<text class="sans" x="64" y="92" font-size="15" font-weight="700" letter-spacing="4.2" fill="url(#acc)">HOLA, SOY</text>
<text class="sans" x="62" y="146" font-size="44" font-weight="800" letter-spacing="-0.6" fill="{t['texto']}">Alejandro Alvarez Sayaverde</text>
<text class="sans" x="64" y="188" font-size="24" font-weight="600" fill="url(#acc)">Desarrollador Android y Web</text>
<rect x="64" y="206" width="56" height="4" rx="2" fill="url(#acc)"/>
<text class="mono" x="64" y="256" font-size="19" font-weight="700" fill="{t['a2']}">~$</text>
{frases_animadas(t, 96, 256, 19)}
{chips(t, 64, 284)}
<g fill="{t['suave']}">
  <path d="{pin}" transform="translate(62 344) scale(0.78)"/>
  <text class="sans" x="86" y="360" font-size="15">Arequipa, Perú</text>
  <path d="{gorro}" transform="translate(206 343) scale(0.82)"/>
  <text class="sans" x="232" y="360" font-size="15">Diseño y Desarrollo de Software · Tecsup</text>
</g>
</svg>"""


# ───────────────────────────── Proyectos ───────────────────────────────

ICONOS = {
    "telefono": '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.2h2"/>',
    "bolsa": '<path d="M5.5 8h13l-1.2 12.5H6.7L5.5 8z"/><path d="M9 10V7a3 3 0 0 1 6 0v3"/>',
    "mapa": '<path d="M12 21.5s-6.5-6-6.5-11.5a6.5 6.5 0 0 1 13 0c0 5.5-6.5 11.5-6.5 11.5z"/><circle cx="12" cy="10" r="2.4"/>',
    "estrella": '<path d="M12 3.2l2.5 5.4 5.9.7-4.4 4 1.2 5.8L12 16.2l-5.2 2.9L8 13.3l-4.4-4 5.9-.7z"/>',
    "ticket": '<path d="M3.5 7h17v3.2a1.9 1.9 0 0 0 0 3.6V17h-17v-3.2a1.9 1.9 0 0 0 0-3.6z"/><path d="M14.5 7.5v1.6M14.5 11.2v1.6M14.5 14.9v1.6"/>',
    "nube": '<path d="M7.2 18.5h9.9a4.1 4.1 0 0 0 .6-8.15A6 6 0 0 0 6.1 9.9a4.3 4.3 0 0 0 1.1 8.6z"/>',
}

COLOR_LENGUAJE = {"Kotlin": "#A97BFF", "JavaScript": "#f1e05a", "Python": "#3572A5", "Java": "#b07219"}

PROYECTOS = [
    {
        "slug": "notivas", "titulo": "NotiVas", "icono": "telefono",
        "lenguaje": "Kotlin", "sub": "Kotlin Multiplatform · en equipo", "etiqueta": "PROYECTO FINAL",
        "grad": ("#7F52FF", "#E44857"),
        "desc": "App para estudiantes que reúne foros, entregas y notificaciones del curso, con un asistente de IA y un simulador de notas.",
        "tags": ["Compose Multiplatform", "Material 3", "IA"],
    },
    {
        "slug": "trazo-y-papel", "titulo": "Trazo y Papel", "icono": "bolsa",
        "lenguaje": "Python", "sub": "React + Django REST Framework", "etiqueta": "WEB",
        "grad": ("#F59E0B", "#EF4444"),
        "desc": "Tienda de papelería con catálogo, búsqueda, filtros por oferta, recomendaciones y control de stock desde el administrador.",
        "tags": ["React", "Vite", "shadcn/ui", "Django"],
    },
    {
        "slug": "mapas-compose", "titulo": "Mapas en Compose", "icono": "mapa",
        "lenguaje": "Kotlin", "sub": "Kotlin · Maps Compose", "etiqueta": "ANDROID",
        "grad": ("#10B981", "#0EA5E9"),
        "desc": "Mapa de Arequipa con marcadores, polígonos, seguimiento de ubicación, clustering, heatmap y Geocoder.",
        "tags": ["Jetpack Compose", "Google Maps SDK"],
    },
    {
        "slug": "meteoritos", "titulo": "Lluvia de meteoritos", "icono": "estrella",
        "lenguaje": "Kotlin", "sub": "Kotlin · animaciones en Compose", "etiqueta": "ANDROID",
        "grad": ("#8B5CF6", "#EC4899"),
        "desc": "Juego de carriles para esquivar meteoritos y juntar estrellas, más cuatro ejercicios de animación. El motor tiene 8 pruebas JUnit.",
        "tags": ["Compose Animation", "JUnit"],
    },
    {
        "slug": "ventanilla-ti", "titulo": "Ventanilla TI", "icono": "ticket",
        "lenguaje": "JavaScript", "sub": "React · Tailwind · shadcn/ui", "etiqueta": "WEB",
        "grad": ("#3B82F6", "#06B6D4"),
        "desc": "Registro de solicitudes de soporte técnico con validación por campo, estados, filtros y 16 pruebas con Vitest.",
        "tags": ["React 19", "Tailwind CSS", "Vitest"],
    },
    {
        "slug": "notivas-nube", "titulo": "NotivasNube", "icono": "nube",
        "lenguaje": "Kotlin", "sub": "Kotlin · Retrofit · MVVM", "etiqueta": "ANDROID",
        "grad": ("#6366F1", "#0EA5E9"),
        "desc": "CRUD de las notas de NotiVas contra una API REST pública, con StateFlow, inyección manual y 10 pruebas JVM.",
        "tags": ["Retrofit", "MVVM", "StateFlow"],
    },
]


def envolver(texto: str, maximo: int) -> list[str]:
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if len(prueba) > maximo and actual:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return lineas


def tarjeta(p: dict, t: dict) -> str:
    W, H = 480, 220
    g1, g2 = p["grad"]
    lineas = envolver(p["desc"], 54)[:3]
    desc = "".join(
        f'<text class="sans" x="24" y="{106 + i * 22}" font-size="14.5" fill="{t["suave"]}">{escape(l)}</text>'
        for i, l in enumerate(lineas)
    )
    tags, x = [], 24.0
    for tag in p["tags"]:
        w = ancho_texto(tag, 12, 0.6) + 20
        tags.append(
            f'<rect x="{x:.1f}" y="172" width="{w:.1f}" height="24" rx="12" fill="{g1}" fill-opacity="0.12" stroke="{g1}" stroke-opacity="0.35"/>'
            f'<text class="sans" x="{x + w / 2:.1f}" y="188" font-size="12" font-weight="600" text-anchor="middle" fill="{t["texto"]}" fill-opacity="0.85">{escape(tag)}</text>'
        )
        x += w + 8
    etiqueta = p["etiqueta"]
    we = ancho_texto(etiqueta, 10.5, 0.68) + 20
    color_leng = COLOR_LENGUAJE.get(p["lenguaje"], t["tenue"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
  aria-label="{escape(p['titulo'])}: {escape(p['desc'])}">
<title>{escape(p['titulo'])}</title>
<style>{ESTILO_BASE}
.brillo{{animation:respira 6s ease-in-out infinite}}
@keyframes respira{{0%,100%{{opacity:1}}50%{{opacity:.55}}}}
</style>
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{g1}"/><stop offset="1" stop-color="{g2}"/></linearGradient>
  <filter id="b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>
  <clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#c)">
  <rect width="{W}" height="{H}" fill="{t['tarjeta']}"/>
  <g class="brillo" opacity="{t['brillo_op']}" filter="url(#b)">
    <circle cx="{W - 10}" cy="-10" r="80" fill="url(#g)"/></g>
  <rect width="{W}" height="3" fill="url(#g)"/>
</g>
<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="17.5" fill="none" stroke="{t['tarjeta_borde']}" stroke-width="1.5"/>
<rect x="24" y="24" width="46" height="46" rx="13" fill="url(#g)"/>
<g transform="translate(32 32) scale(1.25)" fill="none" stroke="#ffffff" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{ICONOS[p['icono']]}</g>
<text class="sans" x="84" y="45" font-size="20" font-weight="700" fill="{t['texto']}">{escape(p['titulo'])}</text>
<circle cx="89" cy="62" r="4.5" fill="{color_leng}"/>
<text class="mono" x="100" y="66.5" font-size="13" fill="{t['tenue']}">{escape(p['sub'])}</text>
<rect x="{W - 24 - we:.1f}" y="26" width="{we:.1f}" height="22" rx="11" fill="{t['tarjeta']}" stroke="{g1}" stroke-opacity="0.55"/>
<text class="sans" x="{W - 24 - we / 2:.1f}" y="41" font-size="10.5" font-weight="700" letter-spacing="0.8" text-anchor="middle" fill="{t['texto']}" fill-opacity="0.85">{escape(etiqueta)}</text>
{desc}
{''.join(tags)}
<g transform="translate({W - 44} 172)">
  <circle cx="12" cy="12" r="12" fill="{g2}" fill-opacity="0.14"/>
  <path d="M8.5 15.5l7-7M10 8.5h5.5V14" fill="none" stroke="{g2}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</g>
</svg>"""


# ───────────────────────────────── Pie ─────────────────────────────────

def pie(t: dict) -> str:
    W, H = 1200, 110
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Separador decorativo">
<style>{ESTILO_BASE}
.ola1{{animation:ola 14s linear infinite}}
.ola2{{animation:ola 20s linear infinite reverse}}
@keyframes ola{{from{{transform:translateX(0)}}to{{transform:translateX(-600px)}}}}
</style>
<defs>{gradiente_acento(t)}</defs>
<g class="ola1" opacity="0.45"><path fill="url(#acc)" d="M0 70 C150 40 300 100 450 70 S750 40 900 70 S1200 100 1350 70 S1650 40 1800 70 V110 H0 Z"/></g>
<g class="ola2" opacity="0.25"><path fill="url(#acc)" d="M0 80 C150 105 300 55 450 80 S750 105 900 80 S1200 55 1350 80 S1650 105 1800 80 V110 H0 Z"/></g>
</svg>"""


# ───────────────────────────── Estadísticas ────────────────────────────

CONSULTA = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { name languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
    repositoriesContributedTo(first: 1, includeUserRepositories: false,
                              contributionTypes: [COMMIT, PULL_REQUEST]) { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""


def token() -> str:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def consultar() -> dict:
    cuerpo = json.dumps({"query": CONSULTA, "variables": {"login": USUARIO}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=cuerpo,
        headers={"Authorization": f"bearer {token()}", "Content-Type": "application/json",
                 "User-Agent": "perfil-readme-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        datos = json.load(r)
    if "errors" in datos:
        raise SystemExit(f"Error de la API: {datos['errors']}")
    return datos["data"]["user"]


def resumir(u: dict) -> dict:
    hoy = datetime.now(timezone(timedelta(hours=-5))).date()
    cc = u["contributionsCollection"]
    dias = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    dias = [d for d in dias if date.fromisoformat(d["date"]) <= hoy]
    racha_max = racha = 0
    for d in dias:
        racha = racha + 1 if d["contributionCount"] > 0 else 0
        racha_max = max(racha_max, racha)
    semanas_api = cc["contributionCalendar"]["weeks"]
    semanas = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in semanas_api]
    # La gráfica arranca en la semana de la primera contribución (mínimo 12 semanas).
    inicio = next((i for i, v in enumerate(semanas) if v > 0), 0)
    inicio = max(0, min(inicio, len(semanas) - 12))
    semanas = semanas[inicio:]
    desde = date.fromisoformat(semanas_api[inicio]["contributionDays"][0]["date"])
    bytes_por_leng: dict[str, list] = {}
    for repo in u["repositories"]["nodes"]:
        if repo["name"] == USUARIO:  # el repo del perfil solo tiene este script
            continue
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            bytes_por_leng.setdefault(n, [0, e["node"]["color"] or "#8b949e"])
            bytes_por_leng[n][0] += e["size"]
    total = sum(v[0] for v in bytes_por_leng.values()) or 1
    lenguajes = sorted(((n, v[0] / total, v[1]) for n, v in bytes_por_leng.items()), key=lambda x: -x[1])
    principales = lenguajes[:5]
    resto = sum(p for _, p, _ in lenguajes[5:])
    if resto > 0.001:
        principales.append(("Otros", resto, "#8b949e"))
    return {
        "hoy": hoy,
        "contribuciones": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "repos": u["repositories"]["totalCount"],
        "racha": racha_max,
        "colabora": u["repositoriesContributedTo"]["totalCount"],
        "semanas": semanas,
        "desde": desde,
        "lenguajes": principales,
    }


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                "septiembre", "octubre", "noviembre", "diciembre"]


def curva(puntos: list[tuple[float, float]]) -> str:
    """Curva suave (Catmull-Rom a Bézier) por los puntos dados."""
    d = f"M{puntos[0][0]:.1f} {puntos[0][1]:.1f}"
    for i in range(len(puntos) - 1):
        p0 = puntos[max(i - 1, 0)]
        p1, p2 = puntos[i], puntos[i + 1]
        p3 = puntos[min(i + 2, len(puntos) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def estadisticas(t: dict, s: dict) -> str:
    W, H = 1200, 330
    fecha = f"{s['hoy'].day} {MESES[s['hoy'].month - 1]} {s['hoy'].year}"
    tiles = [
        (s["contribuciones"], "contribuciones", "en el último año"),
        (s["commits"], "commits", "en el último año"),
        (s["repos"], "repositorios", "públicos propios"),
        (s["racha"], "días seguidos", "racha más larga"),
    ]
    bloques = []
    for i, (valor, l1, l2) in enumerate(tiles):
        x = 40 + i * 152
        bloques.append(
            f'<rect x="{x}" y="84" width="140" height="112" rx="14" fill="{t["chip_bg"]}" stroke="{t["chip_borde"]}" stroke-opacity="0.7"/>'
            f'<text class="sans" x="{x + 16}" y="132" font-size="36" font-weight="800" fill="url(#acc)">{valor}</text>'
            f'<text class="sans" x="{x + 16}" y="160" font-size="14.5" font-weight="600" fill="{t["texto"]}">{l1}</text>'
            f'<text class="sans" x="{x + 16}" y="179" font-size="13" fill="{t["tenue"]}">{l2}</text>'
        )
    # Barra de lenguajes
    bx, bw, by = 680, 480, 110
    segs, x = [], bx
    for nombre, prop, color in s["lenguajes"]:
        w = max(bw * prop, 3)
        segs.append(f'<rect x="{x:.1f}" y="{by}" width="{w:.1f}" height="12" fill="{color}"/>')
        x += w
    leyenda = []
    for i, (nombre, prop, color) in enumerate(s["lenguajes"]):
        col, fila = i % 3, i // 3
        lx, ly = bx + col * 165, by + 46 + fila * 30
        leyenda.append(
            f'<circle cx="{lx + 6}" cy="{ly - 5}" r="6" fill="{color}"/>'
            f'<text class="sans" x="{lx + 20}" y="{ly}" font-size="15" font-weight="600" fill="{t["texto"]}">{escape(nombre)}'
            f'<tspan class="mono" dx="8" font-size="13" font-weight="400" fill="{t["tenue"]}">{prop * 100:.1f}%</tspan></text>'
        )
    # Gráfico de contribuciones por semana
    sem = s["semanas"]
    desde = s["desde"]
    rango = ("últimas 52 semanas" if len(sem) >= 52
             else f"desde el {desde.day} de {MESES_LARGOS[desde.month - 1]} de {desde.year}")
    gx, gy, gw, gh = 40, 238, 1120, 64
    mx = max(sem) or 1
    pts = [(gx + i * gw / (len(sem) - 1), gy + gh - (v / mx) * gh) for i, v in enumerate(sem)]
    linea = curva(pts)
    area = f"{linea} L{gx + gw} {gy + gh} L{gx} {gy + gh} Z"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
  aria-label="Actividad en GitHub: {s['contribuciones']} contribuciones y {s['commits']} commits en el último año, {s['repos']} repositorios públicos">
<title>Actividad en GitHub</title>
<style>{ESTILO_BASE}
.traza{{stroke-dasharray:2600;stroke-dashoffset:2600;animation:traza 2.6s ease-out .3s forwards}}
@keyframes traza{{to{{stroke-dashoffset:0}}}}
</style>
<defs>
  <linearGradient id="fondo" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{t['bg0']}"/><stop offset="1" stop-color="{t['bg1']}"/></linearGradient>
  {gradiente_acento(t)}
  <linearGradient id="relleno" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{t['a1']}" stop-opacity="0.35"/><stop offset="1" stop-color="{t['a1']}" stop-opacity="0"/></linearGradient>
  <clipPath id="marco"><rect width="{W}" height="{H}" rx="22"/></clipPath>
  <clipPath id="barra"><rect x="{bx}" y="{by}" width="{bw}" height="12" rx="6"/></clipPath>
</defs>
<rect width="{W}" height="{H}" rx="22" fill="url(#fondo)"/>
<rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="21.5" fill="none" stroke="{t['borde']}" stroke-width="1.5"/>
<text class="sans" x="40" y="54" font-size="21" font-weight="700" fill="{t['texto']}">Actividad en GitHub</text>
<text class="sans" x="{W - 40}" y="54" font-size="13" text-anchor="end" fill="{t['tenue']}">Actualizado el {fecha}</text>
{''.join(bloques)}
<text class="sans" x="{bx}" y="96" font-size="14" font-weight="600" fill="{t['suave']}">Lenguajes en mis repositorios</text>
<rect x="{bx}" y="{by}" width="{bw}" height="12" rx="6" fill="{t['pista']}"/>
<g clip-path="url(#barra)">{''.join(segs)}</g>
{''.join(leyenda)}
<text class="sans" x="40" y="226" font-size="14" font-weight="600" fill="{t['suave']}">Contribuciones por semana · {rango}</text>
<path d="{area}" fill="url(#relleno)"/>
<path class="traza" d="{linea}" fill="none" stroke="url(#acc)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""


# ─────────────────────────────────── Main ───────────────────────────────

def construir_estatico() -> None:
    for nombre, t in TEMAS.items():
        guardar(f"banner-{nombre}.svg", banner(t))
        guardar(f"pie-{nombre}.svg", pie(t))
        for p in PROYECTOS:
            guardar(f"proyecto-{p['slug']}-{nombre}.svg", tarjeta(p, t))


def construir_stats() -> None:
    s = resumir(consultar())
    print(f"  contribuciones={s['contribuciones']} commits={s['commits']} repos={s['repos']} "
          f"racha={s['racha']} lenguajes={[(n, round(p * 100, 1)) for n, p, _ in s['lenguajes']]}")
    for nombre, t in TEMAS.items():
        guardar(f"stats-{nombre}.svg", estadisticas(t, s))


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if modo in ("todo", "estatico"):
        construir_estatico()
    if modo in ("todo", "stats"):
        construir_stats()
