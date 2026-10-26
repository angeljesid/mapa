/* ============================================================================
   GEO-IA · Asistente del EIA Garcero C (módulo compartido)
   ----------------------------------------------------------------------------
   Se abre en la MISMA página donde estás (no redirige al mapa), se cierra con
   la X, con la tecla Esc o volviendo a tocar el botón «Geo-IA».

   Uso en cualquier página:
     1) <script src="ia_geo.js"></script>   (antes de </body>)
     2) Poner  data-geo-ia  en el botón/menú que debe abrir el asistente.

   La conversación se comparte entre vistas (window._mapaChat de sync_data.js).
   ============================================================================ */
(function () {
  'use strict';

  // ---------------------------------------------------------------- prompt
  var SISTEMA = [
    'Eres GEO-IA, asistente experto ÚNICAMENTE en el EIA del Área de Desarrollo Garcero C (Perenco Colombia Limited, Casanare).',
    'ESTÁ PROHIBIDO responder preguntas ajenas al proyecto (matemáticas, enlaces web, temas personales o de otros proyectos). Si ocurre, rechaza amablemente en una sola línea.',
    'FORMATO OBLIGATORIO (respuestas fáciles de leer):',
    '1) Una frase corta inicial (máximo 1 línea) que responda directamente.',
    '2) De 3 a 6 viñetas que empiecen con "• " con los datos clave; escribe en **negrita** las cifras y nombres importantes.',
    '3) Si tienes la fuente, cierra con una línea "Fuente: CAP n.º, pág. n.º".',
    'No uses párrafos largos, no repitas la pregunta y no superes 120 palabras.',
    'Datos oficiales del proyecto (usalos como referencia):',
    '• Área de Desarrollo: 19.872,68 ha (MAGNA-SIRGAS Origen Único Nacional). Licencia original 19.900,54 ha (Res. 0409/2007, modificada por Res. 1972/2007, 0163/2014, 0312/2016 y 2102/2020; expediente LAM 0165).',
    '• Ubicación: municipios de Orocué y San Luis de Palenque (Casanare). El AD se traslapa con 7 UTM y 1 resguardo; el AIS suma 13 UTM.',
    '• Obras: 13 plataformas multipozo (hasta 2,5 ha y 5 pozos c/u; 65 pozos nuevos), ampliación Estación Sardinas (+9 ha), 2 granjas solares fotovoltaicas (9,9 MW / 20 ha c/u), subestaciones elevadoras/reductoras, 100 km de líneas de flujo (hasta 10"), 100 km de líneas eléctricas de media tensión, 100 km de accesos nuevos y DDV ampliado a 35 m.',
    '• Recurso hídrico: captación en Caño Tujua y Río Guanapalo (hasta 5 l/s), 18 ocupaciones de cauce, aprovechamiento forestal de 3.172,91 m³ y material de préstamo lateral de hasta 30.000 m³ por plataforma.',
    '• Inyección/reinyección: 467.329 BWPD (151.500 autorizados + 315.829 solicitados) en formaciones Carbonera, Guadalupe y Areniscas LSS (DISPOSAL y WATERFLOODING).',
    '• Evaluación ambiental (matriz de significancia, metodología Conesa): escenario sin proyecto (Matriz 01) — 139 interacciones en 15 actividades (52 Irrelevante, 63 Moderado, 12 Severo, 4 Leve y 8 Poco importante; 127 negativas / 12 positivas). Escenario con proyecto (Matriz 02) — 420 interacciones en 80 actividades (123 Irrelevante, 191 Moderado, 23 Severo, 10 Leve, 66 Poco importante y 7 Importante; 337 negativas / 83 positivas).',
    '• Planes: PMA (Cap. 7: 13 programas y 45 fichas para los medios abiótico, biótico y socioeconómico) y PSM (Cap. 8: 3 programas y 19 fichas de seguimiento, con indicadores, soportes y cronograma). Inversión forzosa del 1% aprobada transitoriamente (Res. 0409/2007, art. 21) para la cuenca del río Meta, microcuenca del Caño Guanapalo.',
    '• 1% y compensación: inversión forzosa de $735.250.000 (1% de $73.525.000.000); 3 proyectos del Plan Departamental articulados; compensación biótica de 1.513,43 ha (362,60 ha de intervención estimada: 216,68 ha naturales/seminaturales + 145,92 ha transformadas), con 3 acciones (preservar, rehabilitar, recuperar/uso sostenible) y 8 años de implementación.'
  ].join('\n');

  var SUGERENCIAS = [
    '¿Cuántas plataformas y pozos contempla el proyecto?',
    '¿Qué caracteriza el medio abiótico?',
    '¿Cuál es el área de influencia socioeconómica?',
    '¿Cuáles son las estrategias de desarrollo solicitadas?',
    '¿Cuál es el caudal de inyección/reinyección?',
    '¿Qué municipios componen el área de influencia?',
    '¿Qué obras se solicitan en la modificación de licencia?',
    '¿Cuál es el área total del Área de Desarrollo Garcero C?'
  ];

  var panel = null, historial = null, entrada = null, sugerencias = null;
  var iniciada = false;

  // ---------------------------------------------------------------- estilos
  function inyectarEstilos() {
    if (document.getElementById('geo-ia-estilos')) return;
    var st = document.createElement('style');
    st.id = 'geo-ia-estilos';
    st.textContent = [
      '.geo-ia-panel{position:fixed;top:0;right:0;height:100%;width:400px;max-width:94vw;background:rgba(15,20,29,.98);border-left:1px solid rgba(255,255,255,.12);display:flex;flex-direction:column;z-index:5000;transform:translateX(105%);transition:transform .25s ease;box-shadow:-12px 0 40px rgba(0,0,0,.6);color:#e6edf6;font-family:Inter,system-ui,sans-serif}',
      '.geo-ia-panel.abierto{transform:translateX(0)}',
      '.geo-ia-header{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:14px 16px;border-bottom:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.03)}',
      '.geo-ia-header h3{display:flex;align-items:center;gap:8px;margin:0;font-size:.95rem;font-weight:700}',
      '.geo-ia-header h3 svg{width:18px;height:18px;color:#8DB4E2}',
      '.geo-ia-cerrar{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:8px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.05);color:#cbd5e1;cursor:pointer;transition:all .2s}',
      '.geo-ia-cerrar:hover{background:rgba(255,80,80,.18);border-color:#ff6b6b;color:#fff}',
      '.geo-ia-cerrar svg{width:16px;height:16px}',
      '.geo-ia-mensajes{flex:1;overflow-y:auto;padding:14px 16px;display:flex;flex-direction:column;gap:10px;scrollbar-width:thin}',
      '.geo-ia-msg{max-width:92%;padding:10px 12px;border-radius:12px;font-size:.9rem;line-height:1.55;word-wrap:break-word}',
      '.geo-ia-msg.bot{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.09);align-self:flex-start}',
      '.geo-ia-msg.user{background:rgba(0,176,80,.16);border:1px solid rgba(0,176,80,.4);align-self:flex-end}',
      '.geo-ia-msg ul{margin:6px 0 2px;padding-left:18px}',
      '.geo-ia-msg li{margin-bottom:4px}',
      '.geo-ia-msg b{color:#fff}',
      '.geo-ia-sugerencias{display:flex;flex-wrap:wrap;gap:6px;padding:0 16px 10px}',
      '.geo-ia-chip{border:1px solid rgba(141,180,226,.45);background:rgba(141,180,226,.1);color:#cfe2ff;border-radius:999px;padding:6px 11px;font-size:.85rem;cursor:pointer;transition:all .2s;font-family:inherit}',
      '.geo-ia-chip:hover{background:rgba(141,180,226,.25)}',
      '.geo-ia-input{display:flex;gap:8px;padding:12px 14px;border-top:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.03)}',
      '.geo-ia-input input{flex:1;min-width:0;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:10px 12px;color:#e6edf6;font-size:.9rem;outline:none;font-family:inherit}',
      '.geo-ia-input input:focus{border-color:#00B050}',
      '.geo-ia-enviar{display:flex;align-items:center;justify-content:center;gap:6px;min-width:52px;height:40px;border:none;border-radius:8px;background:#00B050;color:#00130a;cursor:pointer;font-weight:700;transition:filter .2s}',
      '.geo-ia-enviar:hover{filter:brightness(1.12)}',
      '.geo-ia-enviar:active{transform:scale(.97)}',
      '.geo-ia-enviar svg{width:18px;height:18px}',
      '.geo-ia-escribiendo{display:inline-flex;align-items:center;gap:8px;color:#9fb0c4;font-size:.85rem}',
      '.geo-ia-escribiendo i{width:14px;height:14px;border:2px solid rgba(255,255,255,.25);border-top-color:#00B050;border-radius:50%;animation:geo-ia-spin .8s linear infinite;display:inline-block}',
      '@keyframes geo-ia-spin{to{transform:rotate(360deg)}}'
    ].join('\n');
    document.head.appendChild(st);
  }

  // ---------------------------------------------------------------- utilidades
  function aHTML(texto) {
    var t = String(texto == null ? '' : texto);
    t = t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    t = t.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
    t = t.replace(/(^|\s)\*([^*\n]+)\*(?=\s|$)/g, '$1<b>$2</b>');
    var lineas = t.split(/\r?\n/);
    var html = '', enLista = false;
    lineas.forEach(function (l) {
      var item = l.match(/^\s*(?:[•\-\*]|\d+[.)])\s+(.+)$/);
      if (item) {
        if (!enLista) { html += '<ul>'; enLista = true; }
        html += '<li>' + item[1] + '</li>';
      } else {
        if (enLista) { html += '</ul>'; enLista = false; }
        if (l.trim()) html += '<div>' + l + '</div>';
      }
    });
    if (enLista) html += '</ul>';
    return html;
  }

  function agregar(texto, quien) {
    var div = document.createElement('div');
    div.className = 'geo-ia-msg ' + quien;
    div.innerHTML = aHTML(texto);
    historial.appendChild(div);
    historial.scrollTop = historial.scrollHeight;
    iniciada = true;
    actualizarSugerencias();
    if (window._mapaChat && !window._mapaChat.restaurando) {
      try { window._mapaChat.agregar(div.innerHTML, quien); } catch (e) {}
    }
    return div;
  }

  function burbujaCargando() {
    var div = document.createElement('div');
    div.className = 'geo-ia-msg bot';
    div.innerHTML = '<span class="geo-ia-escribiendo"><i></i> Consultando el EIA…</span>';
    historial.appendChild(div);
    historial.scrollTop = historial.scrollHeight;
    return div;
  }

  function actualizarSugerencias() {
    if (!sugerencias) return;
    var hayTexto = entrada && entrada.value.trim().length > 0;
    sugerencias.style.display = (iniciada || hayTexto) ? 'none' : 'flex';
  }

  function pintarSugerencias() {
    sugerencias.innerHTML = '';
    SUGERENCIAS.forEach(function (s) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'geo-ia-chip';
      b.textContent = s;
      b.title = 'Preguntar: ' + s;
      b.addEventListener('click', function () {
        entrada.value = s;
        enviar();
      });
      sugerencias.appendChild(b);
    });
    actualizarSugerencias();
  }

  // ---------------------------------------------------------------- enviar
  var enviando = false;

  async function enviar() {
    var texto = (entrada.value || '').trim();
    if (!texto || enviando) return;
    enviando = true;

    agregar(texto, 'user');
    entrada.value = '';
    actualizarSugerencias();
    var cargando = burbujaCargando();

    try {
      var res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: texto, sistema: SISTEMA })
      });
      var data = await res.json();
      cargando.remove();
      agregar((data && data.respuesta) || 'No pude generar una respuesta en este momento.', 'bot');
    } catch (e) {
      cargando.remove();
      agregar('No pude conectar con el asistente. Abre la aplicación con iniciar.bat y usa http://localhost:8000', 'bot');
    } finally {
      enviando = false;
      entrada.focus();
    }
  }

  // ---------------------------------------------------------------- panel
  function crearPanel() {
    inyectarEstilos();
    if (document.getElementById('geo-ia-panel')) return;

    panel = document.createElement('div');
    panel.id = 'geo-ia-panel';
    panel.className = 'geo-ia-panel';
    panel.innerHTML =
      '<div class="geo-ia-header">' +
        '<h3><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a3 3 0 0 0-3 3v1a3 3 0 0 0-3 3v1a3 3 0 0 0 1 2.2V15a3 3 0 0 0 3 3h1a3 3 0 0 0 3 3 3 3 0 0 0 3-3V9a3 3 0 0 0-3-3V6a3 3 0 0 0-3-3z"/></svg> Asistente Geo-IA</h3>' +
        '<button type="button" class="geo-ia-cerrar" id="geo-ia-cerrar" title="Cerrar (Esc)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>' +
      '</div>' +
      '<div class="geo-ia-mensajes" id="geo-ia-mensajes"></div>' +
      '<div class="geo-ia-sugerencias" id="geo-ia-sugerencias"></div>' +
      '<div class="geo-ia-input">' +
        '<input type="text" id="geo-ia-input" placeholder="Escribe tu consulta sobre el proyecto…" autocomplete="off">' +
        '<button type="button" class="geo-ia-enviar" id="geo-ia-enviar" title="Enviar (Enter)">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2" fill="currentColor" stroke="none"/></svg>' +
        '</button>' +
      '</div>';
    document.body.appendChild(panel);

    historial = document.getElementById('geo-ia-mensajes');
    entrada = document.getElementById('geo-ia-input');
    sugerencias = document.getElementById('geo-ia-sugerencias');

    document.getElementById('geo-ia-cerrar').addEventListener('click', cerrar);
    document.getElementById('geo-ia-enviar').addEventListener('click', enviar);
    entrada.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); enviar(); }
    });
    entrada.addEventListener('input', actualizarSugerencias);

    // saludo inicial (no se guarda en el historial compartido para no duplicarlo)
    if (window._mapaChat) window._mapaChat.restaurando = true;
    agregar('¡Hola! Soy **GEO-IA**, asistente del EIA del Área de Desarrollo Garcero C (Perenco, Casanare).\n\n' +
      'Pregúntame por las obras, el área de influencia, la caracterización, la evaluación ambiental, el PMA o el 1% y la compensación.\n\n' +
      '• ¿Cuántas plataformas y pozos contempla el proyecto?\n' +
      '• ¿Qué caracteriza el medio abiótico?\n' +
      '• ¿Cuál es el caudal de inyección/reinyección?', 'bot');
    if (window._mapaChat) window._mapaChat.restaurando = false;
    iniciada = false;              // el saludo no cuenta como conversación
    pintarSugerencias();

    // restaurar la conversación de la sesión (compartida entre vistas)
    if (window._mapaChat) {
      window._mapaChat.iniciar(function (msgs) {
        if (!msgs || !msgs.length) return;
        window._mapaChat.restaurando = true;
        msgs.forEach(function (m) {
          var html = String(m.h || '');
          // evita repetir el saludo (ya se muestra arriba): se descartan los
          // mensajes del bot que empiezan con el saludo de bienvenida.
          var plano = html.replace(/<[^>]+>/g, '').trim();
          if (plano.indexOf('¡Hola! Soy GEO-IA') === 0) return;
          var div = document.createElement('div');
          div.className = 'geo-ia-msg ' + m.s;
          div.innerHTML = html;
          historial.appendChild(div);
        });
        historial.scrollTop = historial.scrollHeight;
        window._mapaChat.restaurando = false;
        iniciada = document.querySelectorAll('#geo-ia-mensajes .geo-ia-msg.user').length > 0;
        actualizarSugerencias();
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && panel.classList.contains('abierto')) cerrar();
    });
  }

  function abrir() {
    crearPanel();
    panel.classList.add('abierto');
    setTimeout(function () { if (entrada) entrada.focus(); }, 120);
  }

  function cerrar() {
    if (panel) panel.classList.remove('abierto');
  }

  function alternar() {
    crearPanel();
    if (panel.classList.contains('abierto')) cerrar(); else abrir();
  }

  // ---------------------------------------------------------------- arranque
  function iniciar() {
    document.querySelectorAll('[data-geo-ia]').forEach(function (el) {
      el.style.cursor = 'pointer';
      el.addEventListener('click', function (e) {
        e.preventDefault();
        alternar();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }

  window.GeoIA = { abrir: abrir, cerrar: cerrar, alternar: alternar };
})();
