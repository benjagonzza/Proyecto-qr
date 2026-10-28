import os
import json
import socket
import threading
import traceback
from io import BytesIO
import qrcode

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from flask import Flask, render_template_string, request

from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.network.urlrequest import UrlRequest
from kivy.lang import Builder

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

# --- SERVICIO 3: NOTIFICACIONES LOCALES CON PLYER ---
try:
    from plyer import notification
    PLYER_DISPONIBLE = True
except Exception:
    PLYER_DISPONIBLE = False

def emitir_notificacion_nativa(titulo, mensaje):
    if PLYER_DISPONIBLE:
        try:
            notification.notify(
                title=titulo,
                message=mensaje,
                app_name="LabRedes A+S",
                timeout=4
            )
        except Exception as e:
            print(f"[PLYER ERROR]: {e}")

Window.size = (390, 720)

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# --- SERVIDOR WEB FLASK (SINCRONIZACIÓN MÓVIL QR) ---
flask_app = Flask(__name__)
app_kivy_ref = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Equipo - LabRedes</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; text-align: center; }
        .card { background: #1e293b; border-radius: 16px; padding: 24px; max-width: 350px; margin: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.4); }
        h1 { font-size: 20px; color: #38bdf8; }
        .badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; background: #334155; margin: 12px 0; }
        .btn { display: block; width: 100%; padding: 14px; margin: 10px 0; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; }
        .btn-disp { background: #22c55e; color: white; }
        .btn-prest { background: #f59e0b; color: white; }
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
            <button type="submit" name="nuevo_estado" value="Disponible" class="btn btn-disp">🟢 MARCAR COMO DISPONIBLE</button>
            <button type="submit" name="nuevo_estado" value="En Préstamo" class="btn btn-prest">🟠 MARCAR EN PRÉSTAMO</button>
        </form>
    </div>
</body>
</html>
"""

@flask_app.route('/equipo/<codigo_qr>')
def ver_equipo(codigo_qr):
    if app_kivy_ref:
        equipo = next((i for i in app_kivy_ref.inventario if i["qr"].lower() == codigo_qr.lower()), None)
        if equipo:
            return render_template_string(HTML_TEMPLATE, equipo=equipo)
    return "Equipo no encontrado", 404

@flask_app.route('/cambiar_estado', methods=['POST'])
def cambiar_estado_web():
    codigo_qr = request.form.get('qr')
    nuevo_estado = request.form.get('nuevo_estado')
    if app_kivy_ref:
        app_kivy_ref.actualizar_estado_equipo_poo(codigo_qr, nuevo_estado, origen="Móvil QR")
        equipo = next((i for i in app_kivy_ref.inventario if i["qr"].lower() == codigo_qr.lower()), None)
        return render_template_string(HTML_TEMPLATE, equipo=equipo)
    return "Error", 500

# --- PANTALLAS ---
class PantallaLogin(MDScreen): pass
class PantallaRegistro(MDScreen): pass
class PantallaInicio(MDScreen): pass
class PantallaCatalogo(MDScreen): pass
class PantallaEscaner(MDScreen): pass
class PantallaPrestamos(MDScreen): pass

# --- CLASE PRINCIPAL ---
class LabRedesApp(MDApp):
    mensaje_banner = StringProperty("¡Bienvenidos al LabRedes UCT! (Modo Local)")
    contacto_soporte = StringProperty("Soporte: labredes@uct.cl")
    
    URL_REMOTE_CONFIG = "https://gist.githubusercontent.com/benjagonzza/raw/labredes_config.json"

    def build(self):
        global app_kivy_ref
        app_kivy_ref = self
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.dialog = None
        self.ip_local = obtener_ip_local()
        self.usuario_actual = None

        self.usuarios = self.cargar_usuarios_json()
        self.inventario = self.cargar_inventario_json()

        threading.Thread(target=lambda: flask_app.run(host='0.0.0.0', port=5000, debug=False), daemon=True).start()
        
        return Builder.load_file('labredes.kv')

    def on_start(self):
        self.cargar_remote_config()

    def cargar_usuarios_json(self):
        if os.path.exists("usuarios.json"):
            try:
                with open("usuarios.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"admin@uct.cl": "123456"}

    def guardar_usuarios_json(self):
        with open("usuarios.json", "w", encoding="utf-8") as f:
            json.dump(self.usuarios, f, indent=4, ensure_ascii=False)

    def ejecutar_login(self, email, password):
        email = email.strip()
        password = password.strip()
        if email in self.usuarios and self.usuarios[email] == password:
            self.usuario_actual = email
            emitir_notificacion_nativa("Acceso Correcto", f"Bienvenido/a {email}")
            self.actualizar_todo()
            self.cambiar_pantalla("inicio")
        else:
            self.mostrar_dialogo_error("Credenciales inválidas. Verifique correo y clave.")

    def registrar_usuario(self, email, password, confirm_password):
        email = email.strip()
        password = password.strip()
        if not email or not password:
            self.mostrar_dialogo_error("Complete todos los campos.")
            return
        if password != confirm_password:
            self.mostrar_dialogo_error("Las contraseñas no coinciden.")
            return
        if email in self.usuarios:
            self.mostrar_dialogo_error("El correo ya está registrado.")
            return

        self.usuarios[email] = password
        self.guardar_usuarios_json()
        emitir_notificacion_nativa("Registro Exitoso", "Cuenta creada correctamente.")
        self.cambiar_pantalla("login")

    def cargar_inventario_json(self):
        if os.path.exists("inventario.json"):
            try:
                with open("inventario.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return [
            {"nombre": "Switch Cisco Catalyst 2960", "cat": "Switches", "qr": "QR-SW-2960", "ubicacion": "Estante A1", "estado": "En Préstamo", "icon": "lan"},
            {"nombre": "Router MikroTik RB750Gr3", "cat": "Routers", "qr": "QR-RT-750", "ubicacion": "Estante B2", "estado": "Disponible", "icon": "router-wireless"},
            {"nombre": "Crimpadora RJ45 Profesional", "cat": "Herramientas", "qr": "QR-CR-001", "ubicacion": "Caja 3", "estado": "En Préstamo", "icon": "tools"},
            {"nombre": "Tester de Red Fluke Networks", "cat": "Medición", "qr": "QR-TS-800", "ubicacion": "Estante C1", "estado": "En Desuso", "icon": "sine-wave"}
        ]

    def guardar_inventario_json(self):
        with open("inventario.json", "w", encoding="utf-8") as f:
            json.dump(self.inventario, f, indent=4, ensure_ascii=False)

    def actualizar_estado_equipo_poo(self, codigo_qr, nuevo_estado, origen="Desktop"):
        for equipo in self.inventario:
            if equipo["qr"].lower() == codigo_qr.lower():
                equipo["estado"] = nuevo_estado
                self.guardar_inventario_json()
                
                Clock.schedule_once(lambda dt: self.actualizar_todo(), 0)
                
                emitir_notificacion_nativa(
                    "🔄 Inventario Actualizado",
                    f"{equipo['nombre']} -> {nuevo_estado} ({origen})"
                )
                break

    def cargar_remote_config(self):
        def al_exito(req, resultado):
            if isinstance(resultado, dict):
                self.mensaje_banner = resultado.get("mensaje_banner", self.mensaje_banner)
                self.contacto_soporte = resultado.get("contacto_soporte", self.contacto_soporte)

        def al_error(req, error):
            self.mensaje_banner = "¡LabRedes UCT! (Modo Local Offline)"

        try:
            UrlRequest(self.URL_REMOTE_CONFIG, on_success=al_exito, on_error=al_error, on_failure=al_error, timeout=3)
        except Exception:
            al_error(None, None)

    def cambiar_pantalla(self, nombre_pantalla):
        self.root.current = nombre_pantalla

    def mostrar_dialogo_error(self, texto):
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Atención"),
            MDDialogSupportingText(text=texto),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Aceptar"), on_release=lambda x: self.dialog.dismiss())
            )
        )
        self.dialog.open()

    def generar_textura_qr(self, url_web):
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url_web)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return CoreImage(buffer, ext="png").texture

    def actualizar_todo(self):
        try:
            self.actualizar_inicio()
            self.actualizar_catalogo()
            self.actualizar_escaner()
            self.actualizar_prestamos()
        except Exception as e:
            print(f"[ERROR ACTUALIZAR TODO]: {e}")
            traceback.print_exc()

    def actualizar_inicio(self):
        try:
            disp = sum(1 for i in self.inventario if i["estado"] == "Disponible")
            prest = sum(1 for i in self.inventario if i["estado"] == "En Préstamo")
            desu = sum(1 for i in self.inventario if i["estado"] == "En Desuso")
            sc = self.root.get_screen('inicio')
            if 'lbl_disp' in sc.ids: sc.ids.lbl_disp.text = str(disp)
            if 'lbl_prest' in sc.ids: sc.ids.lbl_prest.text = str(prest)
            if 'lbl_desu' in sc.ids: sc.ids.lbl_desu.text = str(desu)
        except Exception as e:
            print(f"[ERROR INICIO]: {e}")

    def obtener_badge_estado(self, estado):
        if estado == "Disponible": return "[color=33E06C]🟢 Disponible[/color]"
        elif estado == "En Préstamo": return "[color=FFB703]🟠 En Préstamo[/color]"
        else: return "[color=FF6161]🔴 En Desuso[/color]"

    def actualizar_catalogo(self, filtro=""):
        try:
            sc = self.root.get_screen('catalogo')
            if 'lista_catalogo' not in sc.ids: return
            lista = sc.ids.lista_catalogo
            lista.clear_widgets()
            filtrados = [i for i in self.inventario if filtro.lower() in i['nombre'].lower() or filtro.lower() in i['qr'].lower()]
            for item in filtrados:
                item_widget = MDListItem(
                    MDListItemLeadingIcon(icon=item.get("icon", "devices")),
                    MDListItemHeadlineText(text=item['nombre']),
                    MDListItemSupportingText(text=f"Código: {item['qr']} | {self.obtener_badge_estado(item['estado'])}", markup=True),
                    on_release=lambda x, eq=item: self.abrir_opciones_equipo(eq)
                )
                lista.add_widget(item_widget)
        except Exception as e:
            print(f"[ERROR CATALOGO]: {e}")

    def actualizar_escaner(self):
        try:
            sc = self.root.get_screen('escaner')
            if 'lista_escaner' not in sc.ids: return
            lista = sc.ids.lista_escaner
            lista.clear_widgets()
            for item in self.inventario:
                item_widget = MDListItem(
                    MDListItemLeadingIcon(icon="qrcode"),
                    MDListItemHeadlineText(text=item['nombre']),
                    MDListItemSupportingText(text=f"Código: {item['qr']}"),
                    on_release=lambda x, eq=item: self.seleccionar_equipo_qr(eq)
                )
                lista.add_widget(item_widget)
        except Exception as e:
            print(f"[ERROR ESCANER]: {e}")

    def seleccionar_equipo_qr(self, equipo):
        try:
            sc = self.root.get_screen('escaner')
            url_equipo = f"http://{self.ip_local}:5000/equipo/{equipo['qr']}"
            if 'qr_image_view' in sc.ids: sc.ids.qr_image_view.texture = self.generar_textura_qr(url_equipo)
            if 'lbl_qr_titulo' in sc.ids: sc.ids.lbl_qr_titulo.text = equipo['nombre']
            if 'lbl_qr_codigo' in sc.ids: sc.ids.lbl_qr_codigo.text = f"URL: {url_equipo}"
        except Exception as e:
            print(f"[ERROR SELECCIONAR QR]: {e}")

    def actualizar_prestamos(self):
        try:
            sc = self.root.get_screen('prestamos')
            if 'lista_prestamos' not in sc.ids: return
            lista = sc.ids.lista_prestamos
            lista.clear_widgets()
            prestados = [i for i in self.inventario if i["estado"] == "En Préstamo"]
            for item in prestados:
                lista.add_widget(
                    MDListItem(
                        MDListItemLeadingIcon(icon="hand-holding"),
                        MDListItemHeadlineText(text=item['nombre']),
                        MDListItemSupportingText(text=f"Código: {item['qr']} | Ubicación: {item['ubicacion']}"),
                        on_release=lambda x, eq=item: self.abrir_opciones_equipo(eq)
                    )
                )
        except Exception as e:
            print(f"[ERROR PRESTAMOS]: {e}")

    def abrir_opciones_equipo(self, equipo):
        def cambiar(est):
            self.actualizar_estado_equipo_poo(equipo['qr'], est, origen="Desktop")
            if self.dialog: self.dialog.dismiss()

        self.dialog = MDDialog(
            MDDialogHeadlineText(text=equipo['nombre']),
            MDDialogSupportingText(text=f"Estado actual: {equipo['estado']}"),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Disponible"), on_release=lambda x: cambiar("Disponible")),
                MDButton(MDButtonText(text="Préstamo"), on_release=lambda x: cambiar("En Préstamo")),
                MDButton(MDButtonText(text="Desuso"), on_release=lambda x: cambiar("En Desuso")),
                MDButton(MDButtonText(text="Cerrar"), on_release=lambda x: self.dialog.dismiss()),
            )
        )
        self.dialog.open()

if __name__ == '__main__':
    LabRedesApp().run()