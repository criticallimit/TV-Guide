# TV Guide para Home Assistant


El Reino Unido también es compatible con una lista preparada de canales principales.
Consulta qué hay en la televisión, planifica la noche, guarda programas y recibe recordatorios. TV Guide funciona en escritorio y móvil, con temas claros y oscuros que pueden seguir a Home Assistant.

[Dansk](https://criticallimit.github.io/TV-Guide/manuals/da.html) · [Deutsch](https://criticallimit.github.io/TV-Guide/manuals/de.html) · [English](https://criticallimit.github.io/TV-Guide/manuals/en.html) · [Español](https://criticallimit.github.io/TV-Guide/manuals/es.html) · [Nederlands](https://criticallimit.github.io/TV-Guide/manuals/nl.html) · [Français](https://criticallimit.github.io/TV-Guide/manuals/fr.html) · [Italiano](https://criticallimit.github.io/TV-Guide/manuals/it.html) · [Norsk](https://criticallimit.github.io/TV-Guide/manuals/nb.html) · [Svenska](https://criticallimit.github.io/TV-Guide/manuals/sv.html)

## Qué puedes hacer

- Elige **Alemania, Austria, Suiza, Países Bajos, Bélgica, Dinamarca, Noruega, Francia o Suecia**. Cada país tiene una lista preparada de canales principales y canales adicionales cuando hay datos de programación disponibles.
- Abre **Ahora**, **18:00**, **20:15**, **22:00**, o elige otro día y hora.
- Crea **Mis canales** con tu propia selección y orden. Puedes combinar canales de todos los países compatibles en una sola lista personal.
- Abre un programa para ver los detalles, guardarlo y configurar un recordatorio 5, 10, 15 o 30 minutos antes.
- La interfaz del complemento está disponible en **danés, alemán, inglés, neerlandés, francés, italiano, noruego o sueco**. La opción automática sigue tu perfil de Home Assistant.

Francia incluye 24 canales nacionales principales; BFMTV está excluido temporalmente.

## Instalación

Necesitas Home Assistant con la tienda de aplicaciones/complementos, por ejemplo Home Assistant OS.

1. Abre **Ajustes → Aplicaciones** (o **Complementos**) y la tienda.
2. Añade `https://github.com/criticallimit/TV-Guide` a **Repositories**.
3. Instala e inicia **TV Guide**.
4. Activa **Mostrar en la barra lateral** y abre **TV Guide**.

[Añadir el repositorio en Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fcriticallimit%2FTV-Guide)

La guía se abre mientras se cargan los datos. La primera descarga puede tardar unos minutos.

## País e idioma

Abre el botón de **ajustes** y selecciona **País e idioma**. Elige el país cuya programación quieres ver. Suiza incluye canales de sus tres regiones lingüísticas; Bélgica incluye canales en neerlandés y francés.

**Automático · Home Assistant** utiliza primero el idioma de tu perfil y después la configuración de la instalación. Si no hay idioma disponible, Dinamarca usa danés, Alemania y Austria usan alemán, Países Bajos neerlandés, Noruega noruego, Francia francés y Suecia sueco. En países multilingües se utiliza el idioma del navegador; el inglés es el idioma de reserva.

El país y el idioma son independientes. Los títulos y descripciones de los programas permanecen en el idioma de la fuente. Un recordatorio conserva el idioma utilizado cuando se creó.

## Personalizar la guía

**Canales principales** muestra la lista preparada para el país seleccionado. Abre **☰ Canales**, marca los países que quieras explorar y busca un canal. Añade canales a **Mis canales** y arrástralos o utiliza las flechas para establecer su orden. Desmarcar un país solo oculta sus canales disponibles; no elimina tus canales seleccionados. Elimina un canal con **×** y guarda los cambios. **Restablecer orden** recupera los canales principales del país actualmente seleccionado.

Los ajustes se agrupan en **País e idioma**, **Vista** y **Recordatorios**. Configura la vista predeterminada, el aspecto y los canales por fila en **Vista**. Un límite de canales de **0** muestra toda la lista seleccionada. Abre **Avanzado** para cambiar el intervalo de actualización de la programación.

## Guardar programas y recibir recordatorios

Abre un programa y selecciona **Guardar**. Los programas guardados aparecen en **★ Guardados**. Para un programa futuro guardado, activa el recordatorio y elige con cuánta antelación quieres recibirlo.

En los ajustes, abre **Recordatorios** y elige Home Assistant o un dispositivo móvil conectado. Utiliza **Probar notificación** para comprobar el destino. TV Guide y Home Assistant deben estar funcionando cuando llegue la hora del recordatorio.

## Añadir la tarjeta al panel

La barra lateral no necesita configuración adicional. Para el panel:

1. Abre **En tu panel** en los ajustes de TV Guide.
2. En Home Assistant, abre **Ajustes → Paneles → Recursos**. Activa el modo avanzado en tu perfil si Recursos está oculto.
3. Añade `/local/tv-guide-card-loader.js` como **módulo JavaScript**.
4. Recarga Home Assistant y añade la tarjeta **TV Guide**.

## Si falta algo

**No hay programación para un canal:** la disponibilidad depende de fuentes públicas. Los datos confirmados de las emisoras tienen prioridad y otras fuentes completan los huecos.

**Guía vacía después de una actualización o cambio de país:** espera a que termine la descarga y vuelve a abrir la guía después de unos minutos.

**No llega un recordatorio:** comprueba el destino en los ajustes y envía una notificación de prueba.

## Actualizaciones y ayuda

Instala las actualizaciones publicadas desde la tienda de aplicaciones/complementos de Home Assistant. Los cambios de la rama main pueden aparecer antes del siguiente release.

[Informar de un problema](https://github.com/criticallimit/TV-Guide/issues) indicando país, canal, fecha y hora.
