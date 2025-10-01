import streamlit as st


# =========================
# CONFIGURA AQUÍ TU FORM
# =========================
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScua9KznddTAn4XUVzRsLc4zmzeDzVg7gkhNLbklKp4yOQYBg/viewform"  # <- reemplaza TU_FORM_ID
ENTRY_SKU = "entry.5441271"  # <- reemplaza por el entry real de tu campo SKU
# =========================

st.set_page_config(page_title="Escáner SKU", layout="centered")
st.markdown("<style>.block-container{padding:0} header,footer{display:none}</style>", unsafe_allow_html=True)

st.html(f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
  <title>Escáner SKU</title>
  <style>
    :root { --bg:#0b0f1a; --card:#111827; --ink:#fff; --accent:#2563eb; --stroke:#374151; }
    * { box-sizing:border-box }
    body { margin:0; background:var(--bg); color:var(--ink); font-family: system-ui, Arial, sans-serif; }
    .wrap { max-width:720px; margin:0 auto; padding:10px; }
    .card { background:var(--card); border-radius:16px; padding:12px; box-shadow:0 10px 30px rgba(0,0,0,.3); }
    video { width:100%; border-radius:12px; background:#000; }
    .row { display:flex; gap:8px; margin:10px 0; align-items:center; }
    .btn { padding:10px 14px; border-radius:10px; border:0; cursor:pointer; background:var(--accent); color:#fff; font-weight:600; }
    .btn:disabled { opacity:.6; cursor:not-allowed; }
    .input { flex:1; min-width:160px; padding:10px; border-radius:10px; border:1px solid var(--stroke); background:#0f172a; color:#fff; }
    a.btn { text-decoration:none; display:inline-block; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="row">
        <button class="btn" id="startBtn">Iniciar cámara</button>
        <button class="btn" id="flipBtn">Cambiar</button>
      </div>
      <video id="preview" playsinline muted autoplay></video>
      <div class="row">
        <input id="sku" class="input" placeholder="SKU…" readonly />
        <a class="btn" id="openLink" href="#" target="_blank" rel="noopener" aria-disabled="true">Abrir Form</a>
      </div>
    </div>
  </div>

  <!-- ZXing (lector de códigos) -->
  <script src="https://cdn.jsdelivr.net/npm/@zxing/library@latest"></script>
  <script>
    // ======= CONFIG =======
    const FORM_URL = "https://docs.google.com/forms/d/e/TU_FORM_ID/viewform"; // <- tu Form
    const ENTRY_SKU = "entry.1234567890";                                      // <- tu entry SKU
    // ======================

    const codeReader = new ZXing.BrowserMultiFormatReader();
    const videoEl = document.getElementById('preview');
    const startBtn = document.getElementById('startBtn');
    const flipBtn  = document.getElementById('flipBtn');
    const skuEl    = document.getElementById('sku');
    const openLink = document.getElementById('openLink');

    let devices = [];
    let currentDeviceId = null;
    let running = false;
    let currentStream = null;

    function isChromeMobile() {
      const ua = navigator.userAgent.toLowerCase();
      return /android/.test(ua) && /chrome\//.test(ua) && !/edg\//.test(ua);
    }

    function updateOpenLink(value) {
      if (!value) {
        openLink.setAttribute('href', '#');
        openLink.setAttribute('aria-disabled', 'true');
        return;
      }
      const url = new URL(FORM_URL);
      url.searchParams.set(ENTRY_SKU, value);
      openLink.setAttribute('href', url.toString());
      openLink.removeAttribute('aria-disabled');
    }

    async function stopCurrentStream() {
      try { codeReader.reset(); } catch (e) {}
      if (currentStream) {
        currentStream.getTracks().forEach(t => t.stop());
        currentStream = null;
      }
      running = false;
    }

    async function warmUpWithFacingMode() {
      // Pre-permiso + pre-view para desbloquear enumerateDevices completo
      const constraints = {
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
          focusMode: "continuous",
          advanced: [ { facingMode: "environment" } ]
        },
        audio: false
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      currentStream = stream;
      videoEl.srcObject = stream;
      await videoEl.play().catch(() => {});
      return stream;
    }

    async function listCameras() {
      const inputs = await ZXing.BrowserCodeReader.listVideoInputDevices();
      devices = inputs || [];
      if (!devices.length) throw new Error("No hay cámaras disponibles");
      if (!currentDeviceId) currentDeviceId = devices[devices.length - 1].deviceId; // suele ser trasera
    }

    async function tryDecodeWithConstraints() {
      // Camino ideal (funciona muy bien en Safari/Chrome modernos)
      await codeReader.decodeFromConstraints(
        {
          video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
          audio: false
        },
        videoEl,
        (result, err) => {
          if (result) {
            const value = (result.getText() || "").trim();
            if (value) {
              skuEl.value = value;
              updateOpenLink(value);
            }
          }
        }
      );
      running = true;
    }

    async function tryDecodeWithDeviceId(id) {
      // Camino forzado para Chrome: deviceId explícito
      await codeReader.decodeFromVideoDevice(id, videoEl, (result, err) => {
        if (result) {
          const value = (result.getText() || "").trim();
          if (value) {
            skuEl.value = value;
            updateOpenLink(value);
          }
        }
      });
      running = true;
    }

    async function startScan() {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error("Este navegador no permite acceso a la cámara");
        }

        // 1) Precalienta permisos/preview
        await warmUpWithFacingMode();
        await listCameras();

        // 2) En Chrome móvil: prueba primero deviceId (suele ser más estable)
        if (isChromeMobile()) {
          try {
            await stopCurrentStream();
            await tryDecodeWithDeviceId(currentDeviceId);
            return;
          } catch (e) {
            console.warn("deviceId directo falló, probando constraints…", e);
          }
        }

        // 3) Constraints con environment
        try {
          await tryDecodeWithConstraints();
          return;
        } catch (e) {
          console.warn("constraints falló, probando deviceId…", e);
        }

        // 4) Fallback final: deviceId
        await stopCurrentStream();
        await tryDecodeWithDeviceId(currentDeviceId);

      } catch (e) {
        console.error("No se pudo iniciar la cámara:", e);
        alert("No se pudo iniciar la cámara. Revisa permisos del navegador para la cámara (Ajustes del sitio) y vuelve a intentar.");
      }
    }

    startBtn.addEventListener('click', async () => {
      if (running) return;
      await startScan();
    });

    flipBtn.addEventListener('click', async () => {
      try {
        await listCameras();
        const idx = devices.findIndex(d => d.deviceId === currentDeviceId);
        currentDeviceId = devices[(idx + 1) % devices.length].deviceId;
        await stopCurrentStream();
        // En Chrome, insistimos con deviceId al alternar
        if (isChromeMobile()) {
          await tryDecodeWithDeviceId(currentDeviceId);
        } else {
          await tryDecodeWithConstraints();
        }
      } catch (e) {
        console.error("No se pudo cambiar de cámara:", e);
        alert("No se pudo cambiar de cámara.");
      }
    });

    window.addEventListener('pagehide', () => { stopCurrentStream(); });
  </script>
</body>
</html>
""")

