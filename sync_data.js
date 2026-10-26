/* Helper compartido: persistencia PORTABLE de datos.
 * Los datos editables (estrategias, permisos, caracterizacion, imagenes de terreno y
 * anotaciones KMZ) se guardan en data/estado_app.json dentro del proyecto, junto a
 * la carpeta uploads/, para que viajen de un computador a otro copiando la carpeta.
 *
 * Uso por pagina:
 *   1) cargarEstadoServidor()  -> el estado completo guardado en el servidor (o null).
 *   2) guardarEstadoServidor(parche) -> fusiona { clave: valor } en el archivo.
 *   3) leerLocalStorage / escribirLocalStorage -> cache por navegador (respaldo).
 *   4) recolectarPrefijoLocalStorage(prefijo) -> migra claves sueltas al estado.
 */

function leerLocalStorage(clave, fallback) {
  try {
    var raw = localStorage.getItem(clave);
    if (!raw) return fallback;
    var datos = JSON.parse(raw);
    return datos !== null && datos !== undefined ? datos : fallback;
  } catch (e) {
    return fallback;
  }
}

function escribirLocalStorage(clave, valor) {
  try {
    localStorage.setItem(clave, JSON.stringify(valor));
    return true;
  } catch (e) {
    return false;
  }
}

async function cargarEstadoServidor() {
  try {
    var res = await fetch('/api/data/estado', { method: 'GET' });
    if (!res.ok) return null;
    var data = await res.json();
    if (!data || !data.ok || !data.data) return null;
    return data.data;
  } catch (e) {
    return null;
  }
}

async function guardarEstadoServidor(parche) {
  if (!parche || typeof parche !== 'object') return null;
  try {
    var res = await fetch('/api/data/estado', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parche)
    });
    if (!res.ok) return null;
    var data = await res.json();
    return data && data.ok ? data.data : null;
  } catch (e) {
    return null;
  }
}

/* Recolecta del localStorage todas las claves con cierto prefijo y las devuelve en
 * un objeto { sufijoSinPrefijo: valor }. Sirve para migrar datos por-clave sueltos
 * (ej. terreno_img_<id>, kmz_eia_anot_<categoria>) al estado portable. */
function recolectarPrefijoLocalStorage(prefijo) {
  var salida = {};
  try {
    for (var i = 0; i < localStorage.length; i++) {
      var clave = localStorage.key(i);
      if (!clave || clave.indexOf(prefijo) !== 0) continue;
      var raw = localStorage.getItem(clave);
      if (!raw) continue;
      try {
        salida[clave.slice(prefijo.length)] = JSON.parse(raw);
      } catch (e) {
        /* valor no JSON: se conserva como texto */
        salida[clave.slice(prefijo.length)] = raw;
      }
    }
  } catch (e) {}
  return salida;
}

/* ---------------------------------------------------------------------------
 * Historial compartido del asistente GEO-IA (todas las vistas).
 * La conversación se conserva al cambiar de vista (index2, index3...) y al
 * cerrar/reabrir el panel. Solo se reestablece cuando se APAGA el proyecto:
 * el servidor genera un token de sesión nuevo en cada arranque y, si no
 * coincide, el historial se descarta.
 *
 * Uso por página:
 *   1) window._mapaChat.iniciar(function (msgs) { ...renders los mensajes... })
 *   2) en appendMessage(): window._mapaChat.agregar(html, 'user'|'bot')
 * ---------------------------------------------------------------------------
 */
window._mapaChat = {
  clave: 'mapa_chat_v1',
  sesion: null,
  historial: [],
  restaurando: false,
  iniciar: function (alListo) {
    alListo = alListo || function () {};
    var self = this;
    if (this.sesion !== null) {
      self._cargar(alListo);
      return;
    }
    self._ping(alListo);
    // Si el navegador demoró el primer ping (pestaña recién abierta, arranque
    // lento), se reintenta hasta conseguir la sesión de la aplicación.
    setTimeout(function () {
      if (self.sesion === null) self._ping(alListo);
    }, 3000);
  },
  _ping: function (alListo) {
    var self = this;
    fetch('/api/ping')
      .then(function (r) { return r.json(); })
      .then(function (p) {
        self.sesion = (p && p.sesion) || null;
        self._cargar(alListo);
      })
      .catch(function () {
        /* sin conexión ahora: el reintento de iniciar() volverá a intentarlo */
      });
  },
  _cargar: function (alListo) {
    var guardado = leerLocalStorage(this.clave, null);
    if (!guardado || !this.sesion || guardado.sesion !== this.sesion) {
      /* Sesión del servidor diferente: proyecto apagado/encendido -> historial limpio */
      if (!guardado && this.sesion && this.historial.length) {
        /* Mensajes escritos en los primeros instantes (antes del ping): se
         * persisten ahora que ya se conoce la sesión actual. */
        this._persistir();
      } else {
        try { localStorage.removeItem(this.clave); } catch (e) {}
      }
      alListo(this.historial);
      return;
    }
    this.historial = Array.isArray(guardado.msgs) ? guardado.msgs.slice(-200) : [];
    alListo(this.historial);
  },
  _persistir: function () {
    try {
      localStorage.setItem(this.clave, JSON.stringify({
        sesion: this.sesion,
        msgs: this.historial.slice(-200)
      }));
    } catch (e) {}
  },
  agregar: function (html, sender) {
    if (this.restaurando) return;
    this.historial.push({ h: html, s: sender });
    if (this.sesion === null) {
      /* Aún no se conoce la sesión (arranque): se persiste en _cargar cuando
       * llegue el ping. Así nada se pierde y nada se guarda sin sesión. */
      return;
    }
    this._persistir();
  },
  borrar: function () {
    this.historial = [];
    try { localStorage.removeItem(this.clave); } catch (e) {}
  }
};