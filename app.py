import streamlit as st
import streamlit.components.v1 as components

# =========================
# CONFIGURA AQUÍ TU FORM
# =========================
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScua9KznddTAn4XUVzRsLc4zmzeDzVg7gkhNLbklKp4yOQYBg/viewform"  # <- reemplaza TU_FORM_ID
ENTRY_SKU = "entry.5441271"  # <- reemplaza por el entry real de tu campo SKU
# =========================

st.set_page_config(page_title="Escáner SKU → Google Forms", page_icon="🧾", layout="centered")

st.title("🧾 Escanear SKU → Google Forms (hardcoded)")
st.caption("Inicia la cámara, escanea el código de barras o QR. Se habilitará el botón para abrir el Form con el SKU cargado.")

# Componente HTML con ZXing. No pedimos nada al usuario; todo viene del hardcode.
html = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    :root {{
      --bg:#0b0f1a; --card:#111827; --ink:#fff; --muted:#9ca3af; --accent:#2563eb; --stroke:#374151;
    }}
    body {{ margin:0; font-family: system-ui, Arial, sans-serif; background:var(--bg); color:var(--ink); }}
    .wrap {{ max-width: 720px; margin: 0 auto; padding: 16px; }}
    .card {{ background:var(--card); border-radius:16px; padding:20px; box-shadow:0 10px 30px rgba(0,0,0,.3); }}
    h1 {{ font-size:1.1rem; margin:0 0 12px; }}
    video {{ width:100%; border-radius:12px; background:#000; }}
    .row {{ display:flex; gap:8px; margin:12px 0; align-items:center; flex-wrap:wrap; }}
    .btn {{ padding:10px 14px; border-radius:10px; border:0; cursor:pointer; background:var(--accent); color:#fff; font-weight:600; }}
    .btn:disabled {{ opacity:.6; cursor:not-allowed; }}
    .input {{ flex:1; min-width:200px; padding:10px; border-radius:10px; border:1px solid var(--stroke); background:#0f172a; color:#fff; }}
    .status {{ margin-top:8px; font-size:.95rem; color:var(--muted); }}
    .help {{ font-size:.9rem; color:var(--muted); }}
    .link {{ display:inline-block; margin-left:8px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Escanear código (SKU)</h1>

      <div class="help">1) Pulsa <b>Iniciar cámara</b> &nbsp; 2) Apunta al código &nbsp; 3) Pulsa <b>Abrir Form</b></div>

      <div class="row">
        <button class="btn" id="startBtn">Iniciar cámara</button>
        <button class="btn" id="flipBtn">Cambiar cámara</button>
      </div>

      <video id="preview" playsinline></video>

      <div class="row">
        <input id="sku" class="input" placeholder="SKU detectado…" readonly />
        <button class="btn" id="copyBtn" title="Copiar SKU">Copiar</button>
        <a class="btn link" id="openLink" href="#" target="_blank" rel="noopener" aria-disabled="true">Abrir Form</a>
      </div>

      <div class="status" id="status">Estado: esperando…</div>
    </div>
  </div>

  <!-- Librería ZXing para lectura de códigos -->
  <script src="https://cdn.jsdelivr.net/npm/@zxing/library@latest"></script>
  <script>
    const FORM_URL = "{FORM_URL}";
    const ENTRY_SKU = "{ENTRY_SKU}";

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
      const inputs = await ZXing.BrowserCodeReader.listVideoInputDevices();
      if (!inputs.length) throw new Error("No hay cámaras disponibles");
      devices = inputs;
      // Intenta usar la trasera si existe (normalmente la última)
      if (!currentDeviceId) currentDeviceId = devices[devices.length - 1].deviceId;
    }}

    async function startScan() {{
      try {{
        await listCameras();
        statusEl.textContent = "Estado: cámara iniciada…";
        await codeReader.decodeFromVideoDevice(currentDeviceId, videoEl, (result, err) => {{
          if (result) {{
            const value = (result.getText() || '').trim();
            if (value) {{
              skuEl.value = value;               // ← captura automática del SKU
              statusEl.textContent = "Detectado: " + value;
              updateOpenLink(value);            // ← habilita el botón Abrir Form
            }}
          }} else if (err && !(err instanceof ZXing.NotFoundException)) {{
            statusEl.textContent = "Error: " + err;
          }}
        }});
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

    // Limpia cámara si navegas fuera
    window.addEventListener('pagehide', () => codeReader.reset());
  </script>
</body>
</html>
"""

components.html(html, height=760, scrolling=True)
