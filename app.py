import streamlit as st
import streamlit.components.v1 as components
from urllib.parse import urlparse, parse_qs

st.set_page_config(page_title="Escáner SKU → Google Forms", page_icon="🧾", layout="centered")

st.title("🧾 Escanear SKU → Google Forms")

st.markdown("""
**Instrucciones:**
1) En tu Google Form ve a **⋮ → Obtener enlace prellenado**, escribe un SKU de prueba y copia la URL.  
2) Pega aquí la **URL prellenada**. El app detectará el ID del campo `entry.xxxxx`.  
3) Pulsa **Iniciar cámara**, escanea, y usa **Abrir Form** para ir al formulario con el SKU cargado.
""")

prefilled_url = st.text_input(
    "URL prellenada de Google Forms",
    value="",
    placeholder="https://docs.google.com/forms/d/e/1FAIpQLScua9KznddTAn4XUVzRsLc4zmzeDzVg7gkhNLbklKp4yOQYBg/viewform?usp=pp_url&entry.5441271=100200300400500"
)

def extract_form_and_entry(url: str):
    """Devuelve (form_url_base, entry_param) o ('','') si no logra extraer."""
    if not url or "docs.google.com/forms" not in url:
        return "", ""
    try:
        parsed = urlparse(url)
        # URL base del formulario (viewform)
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        qs = parse_qs(parsed.query)
        entry_key = ""
        for k in qs.keys():
            if k.startswith("entry."):
                entry_key = k
                break
        # Normalización por si no es 'viewform'
        if not base.endswith("/viewform"):
            if base.endswith("/"):
                base = base + "viewform"
            else:
                base = base + "/viewform"
        return base, entry_key
    except Exception:
        return "", ""

form_url_detected, entry_param_detected = extract_form_and_entry(prefilled_url)

form_url = st.text_input("FORM_URL (base del formulario)", value=form_url_detected)
entry_param = st.text_input("ENTRY del campo SKU (entry.xxxxx)", value=entry_param_detected)

st.divider()
st.markdown("### Escáner en vivo")
st.caption("Pulsa **Iniciar cámara**, apunta al código de barras o QR. Cuando detecte un valor, se mostrará y podrás abrir el Form con un clic.")

if not form_url or not entry_param:
    st.warning("Completa **FORM_URL** y **ENTRY del campo SKU** para habilitar el escáner.")
else:
    # Componente HTML con ZXing. No forzamos redirección; mostramos un botón/enlace seguro.
    html = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    body {{ margin:0; font-family: system-ui, Arial, sans-serif; background:#0b0f1a; color:#fff; }}
    .wrap {{ max-width: 720px; margin: 0 auto; padding: 16px; }}
    .card {{ background:#111827; border-radius:16px; padding:20px; box-shadow:0 10px 30px rgba(0,0,0,.3); }}
    h1 {{ font-size:1.1rem; margin:0 0 12px; }}
    video {{ width:100%; border-radius:12px; background:#000; }}
    .row {{ display:flex; gap:8px; margin:12px 0; align-items:center; flex-wrap:wrap; }}
    .btn {{ padding:10px 14px; border-radius:10px; border:0; cursor:pointer; background:#2563eb; color:#fff; font-weight:600; }}
    .btn:disabled {{ opacity:.6; cursor:not-allowed; }}
    .input {{ flex:1; min-width:200px; padding:10px; border-radius:10px; border:1px solid #374151; background:#0f172a; color:#fff; }}
    .status {{ margin-top:8px; font-size:.95rem; opacity:.9; }}
    .link {{ display:inline-block; margin-left:8px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Escanear código (SKU)</h1>
      <div class="row">
        <button class="btn" id="startBtn">Iniciar cámara</button>
        <button class="btn" id="flipBtn">Cambiar cámara</button>
      </div>
      <video id="preview" playsinline></video>
      <div class="row">
        <input id="sku" class="input" placeholder="SKU detectado…" readonly />
        <button class="btn" id="copyBtn">Copiar</button>
        <a class="btn link" id="openLink" href="#" target="_blank" rel="noopener" aria-disabled="true">Abrir Form</a>
      </div>
      <div class="status" id="status">Estado: esperando…</div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/@zxing/library@latest"></script>
  <script>
    const FORM_URL = "{form_url}";
    const ENTRY_SKU = "{entry_param}";

    const codeReader = new ZXing.BrowserMultiFormatReader();
    const videoEl = document.getElementById('preview');
    const statusEl = document.getElementById('status');
    const skuEl = document.getElementById('sku');
    const startBtn = document.getElementById('startBtn');
    const flipBtn = document.getElementById('flipBtn');
    const copyBtn = document.getElementById('copyBtn');
    const openLink = document.getElementById('openLink');

    let devices = [];
    let currentDeviceId = null;
    let scanning = false;

    function updateOpenLink(value) {{
      if (!value) {{
        openLink.setAttribute('href', '#');
        openLink.setAttribute('aria-disabled', 'true');
        openLink.textContent = 'Abrir Form';
        return;
      }}
      const url = new URL(FORM_URL);
      url.searchParams.set(ENTRY_SKU, value);
      openLink.setAttribute('href', url.toString());
      openLink.removeAttribute('aria-disabled');
      openLink.textContent = 'Abrir Form';
    }}

    async function listCameras() {{
      devices = await ZXing.BrowserCodeReader.listVideoInputDevices();
      if (!devices.length) throw new Error("No hay cámaras disponibles");
      if (!currentDeviceId) currentDeviceId = devices[devices.length - 1].deviceId; // trasera si existe
    }}

    async function startScan() {{
      try {{
        await listCameras();
        statusEl.textContent = "Estado: cámara iniciada…";
        await codeReader.decodeFromVideoDevice(currentDeviceId, videoEl, (result, err) => {{
          if (result) {{
            const value = (result.getText() || '').trim();
            if (value) {{
              skuEl.value = value;
              statusEl.textContent = "Detectado: " + value;
              updateOpenLink(value);
            }}
          }} else if (err && !(err instanceof ZXing.NotFoundException)) {{
            statusEl.textContent = "Error: " + err;
          }}
        }});
        scanning = true;
      }} catch (e) {{
        statusEl.textContent = "Error al iniciar: " + e.message;
      }}
    }}

    startBtn.addEventListener('click', startScan);

    flipBtn.addEventListener('click', async () => {{
      try {{
        if (!devices.length) await listCameras();
        const idx = devices.findIndex(d => d.deviceId === currentDeviceId);
        currentDeviceId = devices[(idx + 1) % devices.length].deviceId;
        codeReader.reset();
        scanning = false;
        statusEl.textContent = "Cambiando cámara…";
        startScan();
      }} catch (e) {{
        statusEl.textContent = "No se pudo cambiar de cámara: " + e.message;
      }}
    }});

    copyBtn.addEventListener('click', async () => {{
      const value = skuEl.value;
      if (!value) {{
        statusEl.textContent = "No hay SKU para copiar.";
        return;
      }}
      try {{
        await navigator.clipboard.writeText(value);
        statusEl.textContent = "SKU copiado al portapapeles.";
      }} catch (e) {{
        statusEl.textContent = "No se pudo copiar: " + e.message;
      }}
    }});

    window.addEventListener('pagehide', () => codeReader.reset());
  </script>
</body>
</html>
    """
    components.html(html, height=740, scrolling=True)
