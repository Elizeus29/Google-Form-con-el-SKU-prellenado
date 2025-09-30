import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase
from pyzbar.pyzbar import decode as zbar_decode

# =========================
# CONFIGURA AQUÍ TU FORM
# =========================
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScua9KznddTAn4XUVzRsLc4zmzeDzVg7gkhNLbklKp4yOQYBg/viewform"  # <- reemplaza TU_FORM_ID
ENTRY_SKU = "entry.5441271"  # <- reemplaza por el entry real de tu campo SKU
# =========================


st.set_page_config(page_title="Escáner SKU", layout="centered")

# UI minimalista
st.markdown(
    """
    <style>
      .block-container{padding-top:0.8rem;padding-bottom:0.8rem}
      header, footer {display:none;}
      .stButton > button {font-weight:600}
    </style>
    """,
    unsafe_allow_html=True,
)

# Estado para el último código detectado
if "last_code" not in st.session_state:
    st.session_state.last_code = ""

class BarcodeProcessor(VideoProcessorBase):
    def __init__(self) -> None:
        self.last = ""

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Decodificar con pyzbar (EAN-13, Code128, QR, etc.)
        results = zbar_decode(img)
        code_text = None
        for obj in results:
            code_text = obj.data.decode("utf-8").strip()
            (x, y, w, h) = obj.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Mostrar texto
            cv2.putText(img, code_text, (x, max(30, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
            break  # con 1 basta

        if code_text:
            self.last = code_text
            st.session_state.last_code = code_text

        return av.VideoFrame.from_ndarray(img, format="bgr24")

col1, col2 = st.columns([3,2], vertical_alignment="center")

with col1:
    webrtc_ctx = webrtc_streamer(
        key="cam",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

with col2:
    sku = st.text_input("SKU", value=st.session_state.last_code, placeholder="—", label_visibility="hidden")
    # Sincroniza cuando cambia el estado
    if st.session_state.last_code and st.session_state.last_code != sku:
        sku = st.session_state.last_code

    # Construye link al Form con el SKU
    form_link = "#"
    disabled = True
    if sku:
        import urllib.parse as up
        url = up.urlparse(FORM_URL)
        q = dict(up.parse_qsl(url.query))
        q[ENTRY_SKU] = sku
        new_q = up.urlencode(q)
        form_link = up.urlunparse((url.scheme, url.netloc, url.path, url.params, new_q, url.fragment))
        disabled = False

    open_form = st.link_button("Abrir Form", url=form_link, disabled=disabled, use_container_width=True)

# Botón para limpiar si escaneó algo extraño
st.button("Limpiar", on_click=lambda: st.session_state.update(last_code=""))
