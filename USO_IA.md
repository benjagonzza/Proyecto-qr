# Declaración de Uso de Inteligencia Artificial (USO_IA.md)

## 1. Herramientas de IA Utilizadas
Se utilizó asistencia de modelos de lenguaje principal de **Google Gemini** para la estructuración de la interfaz, resolución de incompatibilidades de versión y refactorización de lógica POO.

## 2. Modelos Empleados
* **Google Gemini 1.5 Pro / Flash** (asistente de arquitectura, desarrollo y depuración).

## 3. Prompts Específicos Ejecutados
1. *"¿Cómo estructurar un ScreenManager en KivyMD 2.0 evitando errores de ParserException e IDs no encontrados en las pantallas?"*
2. *"Necesito integrar notificaciones emergentes en Windows desde Python dentro de un método POO al cambiar el estado de un elemento."*
3. *"¿Cómo implementar un servidor Flask en un hilo secundario en Kivy para recibir peticiones POST por código QR y actualizar el estado de un JSON local?"*
4. *"Ejemplo de UrlRequest en Kivy para Remote Config con Fallback local en caso de estar offline."*
5. *"¿Cómo solucionar el error de pantalla negra al ejecutar Kivy en Windows por conflictos con OpenGL backend?"*

## 4. Outputs Generados por la IA
* Fragmentos de código en Kivy Language (`.kv`) con reglas de clase `<Pantalla...>:`.
* Esquemas para la integración de `plyer.notification.notify`.
* Estructura base para el hilo secundario con `threading.Thread` y la plantilla HTML para el microservicio Flask.
* Plantilla estándar de declaración de uso de IA y documentación técnica.

## 5. Evaluaciones y Ajustes Humanos
El código generado por la IA fue revisado, probado y corregido activamente por el equipo de desarrollo en los siguientes puntos críticos:
* **Corrección de Backend Gráfico:** Se eliminó la variable de entorno `angle_sdl2` que causaba que la aplicación abriera en pantalla negra en Windows.
* **Refactorización de Navegación en KivyMD 2.0:** La IA sugirió inicialmente sintaxis obsoleta de KivyMD 1.2 (`self.root.ids.screen_manager`), la cual fue corregida manualmente a `self.root.current` y `self.root.get_screen()` para alinearse a las reglas del `MDScreenManager`.
* **Diseño de Interfaz y Contraste (Dark Theme):** Se ajustaron manualmente los valores de `md_bg_color`, `radius`, `MDTextFieldHintText` y colores de etiquetas para asegurar un alto contraste y una lectura clara de las cajas de texto en modo oscuro.
* **Adición del Cierre de Sesión:** Se implementó de forma autónoma la función `cerrar_sesion()` para reiniciar la sesión activa del usuario y limpiar la memoria de la app.

## 6. Reflexión Ética y Aprendizaje Técnico
El uso de la Inteligencia Artificial funcionó como un acelerador de desarrollo para resolver problemas de sintaxis propios del framework KivyMD y librerías de hilos. El valor de aprendizaje del equipo radicó en comprender la arquitectura de integración entre Flask, Kivy, Plyer y la persistencia en archivos JSON, lo que nos permite explicar, defender y modificar de manera autónoma cada línea del código presentado ante el docente.