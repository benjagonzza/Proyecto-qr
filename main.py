import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import socket
import threading
from io import BytesIO
import qrcode

from flask import Flask, render_template_string, request

from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.list import (
    MDListItem, 
    MDListItemHeadlineText, 
    MDListItemSupportingText,
    MDListItemLeadingIcon
)

Window.size = (390, 720)


# --- DETECCIÓN EXACTA DE IP DE RED ---
def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Se conecta simbólicamente para obtener la interfaz activa
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


# --- SERVIDOR WEB SIMPLIFICADO PARA EL MÓVIL ---
flask_app = Flask(__name__)
app_kivy_ref = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Equipo</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; text-align: center; }
        .card { background: #1e293b; border-radius: 16px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); max-width: 350px; margin: auto; }
        h1 { font-size: 20px; color: #38bdf8; margin-bottom: 8px; }
        p { color: #94a3b8; font-size: 14px; margin: 4px 0; }
        .badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; margin: 16px 0; background: #334155; color: #e2e8f0; }
        .btn { display: block; width: 100%; padding: 16px; margin: 12px 0; border: none; border-radius: 12px; font-weight: bold; font-size: 16px; cursor: pointer; box-sizing: border-box; text-decoration: none; }
        .btn-disp { background: #22c55e; color: white; }
        .btn-prest { background: #f59e0b; color: white; }
        .success-msg { background: #15803d; color: white; padding: 10px; border-radius: 8px; margin-top: 15px; font-weight: bold; display: none; }
    </style>
</head>
<body>
    <div class="card">
        <h1>{{ equipo.nombre }}</h1>
        <p>Código: <strong>{{ equipo.qr }}</strong></p>
        <p>Ubicación: {{ equipo.ubicacion }}</p>

        <div class="badge">Estado actual: {{ equipo.estado }}</div>

        <form action="/cambiar_estado" method="POST">
            <input type="hidden" name="qr" value="{{ equipo.qr }}">
            <button type="submit" name="nuevo_estado" value="Disponible" class="btn btn-disp">
                🟢 MARCAR COMO DISPONIBLE
            </button>
            <button type="submit" name="nuevo_estado" value="En Préstamo" class="btn btn-prest">
                🟠 MARCAR EN PRÉSTAMO
            </button>
        </form>

        {% if actualizado %}
        <div class="success-msg" style="display:block;">
            ¡Estado actualizado con éxito en la computadora!
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@flask_app.route('/equipo/<codigo_qr>')
def ver_equipo(codigo_qr):
    actualizado = request.args.get('actualizado', False)
    if app_kivy_ref:
        equipo = next((i for i in app_kivy_ref.inventario if i["qr"].lower() == codigo_qr.lower()), None)
        if equipo:
            return render_template_string(HTML_TEMPLATE, equipo=equipo, actualizado=actualizado)
    return "<h1>Equipo no encontrado en la base de datos</h1>", 404

@flask_app.route('/cambiar_estado', methods=['POST'])
def cambiar_estado_web():
    codigo_qr = request.form.get('qr')
    nuevo_estado = request.form.get('nuevo_estado')
    
    if app_kivy_ref:
        for equipo in app_kivy_ref.inventario:
            if equipo["qr"].lower() == codigo_qr.lower():
                equipo["estado"] = nuevo_estado
                Clock.schedule_once(lambda dt: app_kivy_ref.actualizar_todo(), 0)
                break
    return render_template_string(
        HTML_TEMPLATE, 
        equipo=next(i for i in app_kivy_ref.inventario if i["qr"].lower() == codigo_qr.lower()), 
        actualizado=True
    )


class PantallaInicio(MDScreen):
    pass

class PantallaCatalogo(MDScreen):
    pass

class PantallaEscaner(MDScreen):
    pass

class PantallaPrestamos(MDScreen):
    pass


class LabRedesApp(MDApp):
    def build(self):
        global app_kivy_ref
        app_kivy_ref = self

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.dialog = None
        self.ip_local = obtener_ip_local()
        self.equipo_seleccionado_qr = None

        self.inventario = [
            {
                "nombre": "Switch Cisco Catalyst 2960", 
                "cat": "Switches", 
                "qr": "QR-SW-2960", 
                "ubicacion": "Estante A1", 
                "estado": "En Préstamo", 
                "icon": "lan"
            },
            {
                "nombre": "Router MikroTik RB750Gr3", 
                "cat": "Routers", 
                "qr": "QR-RT-750", 
                "ubicacion": "Estante B2", 
                "estado": "Disponible", 
                "icon": "router-wireless"
            },
            {
                "nombre": "Crimpadora RJ45 Profesional", 
                "cat": "Herramientas", 
                "qr": "QR-CR-001", 
                "ubicacion": "Caja 3", 
                "estado": "En Préstamo", 
                "icon": "tools"
            },
            {
                "nombre": "Tester de Red Fluke Networks", 
                "cat": "Medición", 
                "qr": "QR-TS-800", 
                "ubicacion": "Estante C1", 
                "estado": "En Desuso", 
                "icon": "sine-wave"
            },
            {
                "nombre": "Patch Cord UTP Cat6 (x10)", 
                "cat": "Cables", 
                "qr": "QR-CB-CAT6", 
                "ubicacion": "Cajón D", 
                "estado": "Disponible", 
                "icon": "ethernet"
            },
        ]
        
        # Servidor Web en segundo plano
        threading.Thread(target=lambda: flask_app.run(host='0.0.0.0', port=5000, debug=False), daemon=True).start()

        return self.root

    def on_start(self):
        self.equipo_seleccionado_qr = self.inventario[0]
        self.actualizar_todo()

    def cambiar_pantalla(self, nombre_pantalla):
        self.root.ids.screen_manager.current = nombre_pantalla

    def generar_textura_qr(self, url_web):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url_web)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        im = CoreImage(buffer, ext="png")
        return im.texture

    def seleccionar_equipo_qr(self, equipo):
        self.equipo_seleccionado_qr = equipo
        self.actualizar_visor_qr()

    def actualizar_visor_qr(self):
        if not self.equipo_seleccionado_qr:
            return

        sc = self.root.ids.screen_manager.get_screen('escaner')
        
        url_equipo = f"http://{self.ip_local}:5000/equipo/{self.equipo_seleccionado_qr['qr']}"
        
        tex = self.generar_textura_qr(url_equipo)
        sc.ids.qr_image_view.texture = tex
        sc.ids.lbl_qr_titulo.text = self.equipo_seleccionado_qr['nombre']
        sc.ids.lbl_qr_codigo.text = f"URL: {url_equipo}"

    def actualizar_todo(self):
        self.actualizar_inicio()
        self.actualizar_catalogo()
        self.actualizar_escaner()
        self.actualizar_prestamos()
        self.actualizar_visor_qr()

    def actualizar_inicio(self):
        disp = sum(1 for i in self.inventario if i["estado"] == "Disponible")
        prest = sum(1 for i in self.inventario if i["estado"] == "En Préstamo")
        desu = sum(1 for i in self.inventario if i["estado"] == "En Desuso")

        sc = self.root.ids.screen_manager.get_screen('inicio')
        sc.ids.lbl_disp.text = str(disp)
        sc.ids.lbl_prest.text = str(prest)
        sc.ids.lbl_desu.text = str(desu)

    def obtener_badge_estado(self, estado):
        if estado == "Disponible":
            return "[color=33E06C]🟢 Disponible[/color]"
        elif estado == "En Préstamo":
            return "[color=FFB703]🟠 En Préstamo[/color]"
        else:
            return "[color=FF6161]🔴 En Desuso[/color]"

    def actualizar_catalogo(self, filtro=""):
        sc = self.root.ids.screen_manager.get_screen('catalogo')
        lista = sc.ids.lista_catalogo
        lista.clear_widgets()

        filtrados = [
            i for i in self.inventario 
            if filtro.lower() in i['nombre'].lower() 
            or filtro.lower() in i['cat'].lower() 
            or filtro.lower() in i['qr'].lower()
        ]

        for item in filtrados:
            estado_formatted = self.obtener_badge_estado(item['estado'])
            item_widget = MDListItem(
                MDListItemLeadingIcon(icon=item.get("icon", "devices")),
                MDListItemHeadlineText(text=item['nombre']),
                MDListItemSupportingText(
                    text=f"Cat: {item['cat']} | Ubicación: {item['ubicacion']}\nEstado: {estado_formatted}",
                    markup=True
                ),
                on_release=lambda x, eq=item: self.abrir_opciones_equipo(eq)
            )
            lista.add_widget(item_widget)

    def actualizar_escaner(self):
        sc = self.root.ids.screen_manager.get_screen('escaner')
        lista = sc.ids.lista_escaner
        lista.clear_widgets()

        for item in self.inventario:
            estado_formatted = self.obtener_badge_estado(item['estado'])
            item_widget = MDListItem(
                MDListItemLeadingIcon(icon="qrcode"),
                MDListItemHeadlineText(text=f"{item['nombre']}"),
                MDListItemSupportingText(text=f"Código: {item['qr']} | {estado_formatted}", markup=True),
                on_release=lambda x, eq=item: self.seleccionar_equipo_qr(eq)
            )
            lista.add_widget(item_widget)

    def actualizar_prestamos(self):
        sc = self.root.ids.screen_manager.get_screen('prestamos')
        lista = sc.ids.lista_prestamos
        lista.clear_widgets()

        prestados = [i for i in self.inventario if i["estado"] == "En Préstamo"]

        if not prestados:
            lista.add_widget(
                MDListItem(
                    MDListItemLeadingIcon(icon="check-circle-outline"),
                    MDListItemHeadlineText(text="No hay préstamos activos"),
                    MDListItemSupportingText(text="Todos los equipos están en su estante correspondiente.")
                )
            )
            return

        for item in prestados:
            item_widget = MDListItem(
                MDListItemLeadingIcon(icon=item.get("icon", "tools")),
                MDListItemHeadlineText(text=item['nombre']),
                MDListItemSupportingText(text=f"Código: {item['qr']} | Origen: {item['ubicacion']}"),
                on_release=lambda x, eq=item: self.abrir_opciones_equipo(eq)
            )
            lista.add_widget(item_widget)

    def abrir_opciones_equipo(self, equipo):
        def cambiar_estado(nuevo_estado):
            equipo["estado"] = nuevo_estado
            if self.dialog:
                self.dialog.dismiss()
            self.actualizar_todo()

        def ver_qr_pantalla():
            if self.dialog:
                self.dialog.dismiss()
            self.seleccionar_equipo_qr(equipo)
            self.cambiar_pantalla('escaner')

        def cerrar_dialogo(*args):
            if self.dialog:
                self.dialog.dismiss()

        estado_actual = self.obtener_badge_estado(equipo['estado'])

        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Gestión de Inventario"),
            MDDialogSupportingText(
                text=f"[b]{equipo['nombre']}[/b]\nCódigo: [color=00B4D8]{equipo['qr']}[/color]\nUbicación: {equipo['ubicacion']}\nEstado actual: {estado_actual}\n\nSeleccione la acción:",
                markup=True
            ),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Ver QR"),
                    style="filled",
                    on_release=lambda x: ver_qr_pantalla()
                ),
                MDButton(
                    MDButtonText(text="Disponible"),
                    style="outlined",
                    on_release=lambda x: cambiar_estado("Disponible")
                ),
                MDButton(
                    MDButtonText(text="Préstamo"),
                    style="outlined",
                    on_release=lambda x: cambiar_estado("En Préstamo")
                ),
                MDButton(
                    MDButtonText(text="En Desuso"),
                    style="outlined",
                    on_release=lambda x: cambiar_estado("En Desuso")
                ),
                MDButton(
                    MDButtonText(text="Cerrar"),
                    style="text",
                    on_release=cerrar_dialogo
                ),
                spacing="6dp",
            ),
        )
        self.dialog.open()



if __name__ == '__main__':
    print("\n" + "="*40)
    print(">>> ¡ATENCIÓN! SE ESTÁ EJECUTANDO EL MAIN ACTUALIZADO <<<")
    print("="*40 + "\n")
    LabRedesApp().run()