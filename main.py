import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText

# Tamaño smartphone para pruebas
Window.size = (390, 720)


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
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"

        # Base de datos simulada en memoria
        self.inventario = [
            {"nombre": "Switch Cisco Catalyst 2960", "cat": "Switches", "qr": "QR-SW-2960", "ubicacion": "Estante A1", "estado": "Disponible"},
            {"nombre": "Router MikroTik RB750Gr3", "cat": "Routers", "qr": "QR-RT-750", "ubicacion": "Estante B2", "estado": "Disponible"},
            {"nombre": "Crimpadora RJ45 Profesional", "cat": "Herramientas", "qr": "QR-CR-001", "ubicacion": "Caja 3", "estado": "En Préstamo"},
            {"nombre": "Tester de Red Fluke Networks", "cat": "Medición", "qr": "QR-TS-800", "ubicacion": "Estante C1", "estado": "En Desuso"},
            {"nombre": "Patch Cord UTP Cat6 (x10)", "cat": "Cables", "qr": "QR-CB-CAT6", "ubicacion": "Cajón D", "estado": "Disponible"},
        ]
        return self.root

    def on_start(self):
        self.actualizar_todo()

    def cambiar_pantalla(self, nombre_pantalla):
        self.root.ids.screen_manager.current = nombre_pantalla

    def actualizar_todo(self):
        self.actualizar_inicio()
        self.actualizar_catalogo()
        self.actualizar_escaner()
        self.actualizar_prestamos()

    def actualizar_inicio(self):
        disp = sum(1 for i in self.inventario if i["estado"] == "Disponible")
        prest = sum(1 for i in self.inventario if i["estado"] == "En Préstamo")
        desu = sum(1 for i in self.inventario if i["estado"] == "En Desuso")

        sc = self.root.ids.screen_manager.get_screen('inicio')
        sc.ids.lbl_disp.text = str(disp)
        sc.ids.lbl_prest.text = str(prest)
        sc.ids.lbl_desu.text = str(desu)

    def actualizar_catalogo(self, filtro=""):
        sc = self.root.ids.screen_manager.get_screen('catalogo')
        lista = sc.ids.lista_catalogo
        lista.clear_widgets()

        filtrados = [
            i for i in self.inventario 
            if filtro.lower() in i['nombre'].lower() or filtro.lower() in i['cat'].lower() or filtro.lower() in i['qr'].lower()
        ]

        for item in filtrados:
            item_widget = MDListItem(
                MDListItemHeadlineText(text=item['nombre']),
                MDListItemSupportingText(text=f"Cat: {item['cat']} | Ubicación: {item['ubicacion']} | Estado: {item['estado']}")
            )
            lista.add_widget(item_widget)

    def actualizar_escaner(self):
        sc = self.root.ids.screen_manager.get_screen('escaner')
        lista = sc.ids.lista_escaner
        lista.clear_widgets()

        for item in self.inventario:
            item_widget = MDListItem(
                MDListItemHeadlineText(text=f"Escanear {item['qr']} — {item['nombre']}"),
                MDListItemSupportingText(text=f"Estado actual: {item['estado']}"),
                on_release=lambda x, qr=item['qr']: self.simular_escanio(qr)
            )
            lista.add_widget(item_widget)

    def actualizar_prestamos(self):
        sc = self.root.ids.screen_manager.get_screen('prestamos')
        lista = sc.ids.lista_prestamos
        lista.clear_widgets()

        prestados = [i for i in self.inventario if i["estado"] == "En Préstamo"]

        if not prestados:
            lista.add_widget(MDListItem(MDListItemHeadlineText(text="No hay préstamos activos a tu nombre")))
            return

        for item in prestados:
            item_widget = MDListItem(
                MDListItemHeadlineText(text=item['nombre']),
                MDListItemSupportingText(text=f"QR: {item['qr']} | Devolución estimada: Hoy 18:00 hrs"),
                on_release=lambda x, qr=item['qr']: self.simular_escanio(qr)
            )
            lista.add_widget(item_widget)

    def simular_escanio(self, codigo_qr):
        equipo = next((item for item in self.inventario if item["qr"] == codigo_qr), None)
        if not equipo:
            return

        es_disponible = equipo["estado"] == "Disponible"
        nuevo_estado = "En Préstamo" if es_disponible else "Disponible"

        def confirmar_accion(*args):
            equipo["estado"] = nuevo_estado
            self.dialog.dismiss()
            self.actualizar_todo()

        def cancelar_accion(*args):
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title=f"Lectura QR: {codigo_qr}",
            text=f"Equipo: {equipo['nombre']}\nUbicación: {equipo['ubicacion']}\n\n¿Desea cambiar el estado a '{nuevo_estado}'?",
            buttons=[
                MDButton(MDButtonText(text="Cancelar"), on_release=cancelar_accion),
                MDButton(MDButtonText(text="Confirmar"), on_release=confirmar_accion),
            ],
        )
        self.dialog.open()


if __name__ == '__main__':
    LabRedesApp().run()