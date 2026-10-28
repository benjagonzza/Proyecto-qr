# Documentación Técnica del Sistema LabRedes A+S

## 1. Contexto y Necesidad Comunitaria (A+S)
El Laboratorio de Redes de la Universidad Católica de Temuco (UC Temuco) requería un sistema digitalizado para la gestión y control de préstamo de equipos (switches, routers, herramientas de crimpado y equipos de medición). El objetivo principal del proyecto Aprendizaje+Servicio (A+S) es reducir la carga cognitiva del encargado de laboratorio y prevenir la pérdida de material mediante una solución multiplataforma que integre monitoreo en tiempo real, notificaciones emergentes en el sistema operativo y sincronización remota mediante dispositivos móviles.

---

## 2. Arquitectura de los 4 Servicios Requeridos

El sistema fue desarrollado bajo el paradigma de **Programación Orientada a Objetos (POO)** en Python utilizando el framework **KivyMD 2.0** y un servidor web embebido **Flask**.

### Servicio 1: Autenticación de Usuarios y Control de Sesión
* **Descripción:** Control de acceso mediante credenciales de correo institucional y clave.
* **Mecanismo:**
  * Las credenciales se leen e ingresan mediante los métodos `ejecutar_login()` y `registrar_usuario()`.
  * Sanitización de cadenas con `.strip()` para evitar fallos por espacios en blanco.
  * Validación de coincidencia de contraseñas en el registro.
  * Método `cerrar_sesion()` que borra la referencia del usuario en memoria (`self.usuario_actual = None`), dispara una notificación nativa de salida y redirige a la pantalla de `login`.

### Servicio 2: Persistencia de Datos en JSON Local
* **Descripción:** Guardado permanente del estado del inventario y de los usuarios registrados sin depender de bases de datos externas de difícil despliegue.
* **Archivos:**
  * `usuarios.json`: Almacena el diccionario `{ correo: contraseña }`. Cuenta por defecto: `admin@uct.cl` / `123456`.
  * `inventario.json`: Almacena la lista de diccionarios de equipos con su estado (`Disponible`, `En Préstamo`, `En Desuso`), código QR, categoría y ubicación.
* **Métodos POO:** `cargar_usuarios_json()`, `guardar_usuarios_json()`, `cargar_inventario_json()`, `guardar_inventario_json()`.

### Servicio 3: Notificaciones Locales Nativas (Plyer)
* **Descripción:** Alertas emergentes directas en el escritorio del sistema operativo Windows cuando ocurren eventos críticos.
* **Puntos de Disparo:**
  1. **Autenticación Exitosa:** Salta al iniciar sesión correctamente o registrar una cuenta nueva.
  2. **Cierre de Sesión:** Salta al presionar el botón de desconexión en el panel superior.
  3. **Mutación de Inventario:** Salta cada vez que se cambia el estado de un equipo desde la interfaz desktop o desde el navegador del celular mediante el QR.
* **Método POO:** `emitir_notificacion_nativa(titulo, mensaje)` envolviendo `plyer.notification.notify()`.

### Servicio 4: Configuración Remota (Remote Config con Fallback)
* **Descripción:** Carga dinámica del banner institucional de noticias y contacto de soporte desde la nube.
* **Mecanismo:**
  * Uso de `UrlRequest` para consultar asíncronamente un archivo JSON alojado en GitHub Gist (`URL_REMOTE_CONFIG`).
  * Enlace reactivo mediante `StringProperty` en `main.py` hacia la vista `.kv`.
  * **Manejo de Fallback:** Si no hay conexión a internet o el servidor no responde dentro de 3 segundos, se activa la función `al_error()`, garantizando que la app continúe funcionando localmente con un banner estático.

---

## 3. Servidor Web Flask Integrado (Sincronización QR Móvil)

Para permitir que cualquier ayudante o docente pueda cambiar el estado de un equipo escaneando un código QR con su celular sin instalar la app:

1. `main.py` detecta la IP local de la computadora en la red (`obtener_ip_local()`).
2. Se inicia un servidor Flask en un hilo secundario independiente (`threading.Thread(..., daemon=True)`).
3. En la pantalla **Código QR**, se genera dinámicamente una imagen QR que apunta a la URL `http://<IP_LOCAL>:5000/equipo/<CODIGO_QR>`.
4. Al abrir el enlace desde el celular, Flask renderiza un template HTML responsivo. Al presionar "Marcar como Disponible" o "Marcar en Préstamo", la ruta `/cambiar_estado` invoca el método POO `actualizar_estado_equipo_poo()`, guardando en `inventario.json`, actualizando las vistas en tiempo real y disparando la notificación emergente en la computadora.

---

## 4. Estructura del Código y Matriz de Archivos

| Archivo | Función Principal |
| :--- | :--- |
| **`main.py`** | Controlador principal POO (`LabRedesApp`), lógica de negocio