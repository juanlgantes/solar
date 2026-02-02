# Plan de Mejoras Técnicas para Solahart YUBA S.L. Canarias

Este plan detalla 5 tareas técnicas para mejorar el sitio web, enfocándose en la responsividad y la adición de un formulario de contacto, manteniendo el diseño de fondo negro con letras neón.

- [x] 1. **Configuración del Viewport y Estructura Base Responsive**
   - [x] Verificar y asegurar la presencia del meta tag `<meta name="viewport" content="width=device-width, initial-scale=1.0">` en el `head` del HTML.
   - [x] Refactorizar los contenedores principales CSS para usar unidades relativas (%, rem, vw/vh) en lugar de píxeles fijos, permitiendo que el contenido fluya naturalmente.

2. [x] [x] [x] [x] [x] [x] **Implementación de Media Queries para Diseño Adaptativo**
   -[x] Crear puntos de ruptura (breakpoints) en el CSS para móviles (max-width: 768px) y tablets.
   - [x] Ajustar la navegación para que sea amigable en móviles (ej. menú hamburguesa o lista apilada).
   - [x] Modificar las propiedades de `flex-direction` o `grid-template-columns` para que los elementos se apilen verticalmente en pantallas pequeñas.

3. [x] **Desarrollo de la Estructura HTML del Formulario de Contacto**
   - [x] Crear una nueva sección `<section id="contacto">` en el archivo HTML.
   - [x] Implementar el formulario usando etiquetas `<form>`, `<label>`, `<input>` y `<textarea>`.
   - [x] Incluir campos para: Nombre completo, Correo electrónico, Teléfono y Mensaje. Añadir atributos de accesibilidad (`aria-label`, `for`).

4. [x] **Estilizado Neón del Formulario**
   - [x] Aplicar estilos CSS al formulario para integrarlo con el tema oscuro.
   - [x] Configurar `background-color: black` (o transparente) y color de texto neón para los inputs.
   - Añadir bordes brillantes (`box-shadow` o `border`) con colores neón (verde/azul/amarillo) que reaccionen al estado `:focus`.
   - Estilizar el botón de envío con efectos `hover` brillantes.

5. **Validación y Funcionalidad del Formulario con JavaScript**
   - Seleccionar el formulario y sus inputs en el archivo JS.
   - Añadir un "event listener" al evento `submit` para prevenir el envío por defecto (`e.preventDefault()`).
   - Implementar lógica de validación simple: campos no vacíos y formato de email válido.
   - Mostrar mensajes de retroalimentación (éxito o error) al usuario en el DOM, usando estilos neón.
