import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(page_title="Gestión Térmica para la Minería Chilena", layout="wide")

st.title("Gestión Térmica para la Minería Chilena")

# =========================
# BASE DE DATOS COMPLETA
# =========================
CHILE_DB = {
    "Arica y Parinacota": {
        "Pampa Camarones": (-18.4783, -70.3126),
        "Quebrada Blanca Norte": (-18.5000, -70.0000)
    },
    "Tarapacá": {
        "Collahuasi": (-20.9833, -68.6167),
        "Quebrada Blanca": (-21.0000, -68.8000)
    },
    "Antofagasta": {
        "Escondida": (-24.2708, -69.0642),
        "Chuquicamata": (-22.2908, -68.9025),
        "Spence": (-22.8167, -69.2500),
        "Radomiro Tomic": (-22.2139, -68.8681)
    },
    "Atacama": {
        "El Salvador": (-26.2458, -69.6258),
        "Candelaria": (-27.5097, -70.2828)
    },
    "Coquimbo": {
        "Los Pelambres": (-31.7167, -70.4833),
        "Andacollo": (-30.2333, -71.0833)
    },
    "O'Higgins": {
        "El Teniente": (-34.0833, -70.4500)
    },
    "Magallanes": {
        "Punta Arenas Industrial": (-53.1638, -70.9171)
    }
}

# =========================
# FUNCIONES
# =========================
def obtener_clima(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation"
        data = requests.get(url, timeout=10).json()["current"]
        return data
    except:
        return None

def sugerir_ropa(sensacion):
    if sensacion <= 5: return "🟦 Frío Extremo", "Ropa térmica completa"
    elif sensacion <= 12: return "🟦 Frío", "Chaqueta + protección viento"
    elif sensacion <= 18: return "🟢 Confortable", "Ropa estándar"
    elif sensacion <= 25: return "🟡 Templado", "Ropa liviana + hidratación"
    elif sensacion <= 30: return "🟠 Calor", "Ropa ligera + pausas"
    else: return "🔴 Extremo", "Control estricto"

def interpretar_wbgt(w):
    if w < 25: return "🟢 Seguro", "Normal"
    elif w < 28: return "🟡 Precaución", "Hidratación+"
    elif w < 30: return "🟠 Riesgo Alto", "Pausas 30'"
    else: return "⛔ Crítico", "SUSPENDER"

# =========================
# INTERFAZ
# =========================
region_sel = st.selectbox("🌍 Seleccione Región", list(CHILE_DB.keys()))
faenas = CHILE_DB[region_sel]

resultados = []

for nombre, coords in faenas.items():
    d = obtener_clima(coords[0], coords[1])
    if d:
        temp = d['temperature_2m']
        viento = d['wind_speed_10m']
        hum = d['relative_humidity_2m']
        radiacion = d.get('shortwave_radiation', 0)

        # Sensación térmica real
        sensacion = 13.12 + 0.6215*temp - 11.37*(viento**0.16) + 0.3965*temp*(viento**0.16)

        # WBGT mejorado
        wbgt_val = temp + (hum * 0.02) + (radiacion * 0.002)

        riesgo_ropa, ropa_desc = sugerir_ropa(sensacion)
        estado_wbgt, accion = interpretar_wbgt(wbgt_val)

        resultados.append({
            "Faena": nombre,
            "Temp °C": float(temp),
            "Viento km/h": float(viento),
            "Radiación W/m²": float(radiacion),
            "Sensación °C": float(sensacion),
            "WBGT": float(wbgt_val),
            "Estado WBGT": estado_wbgt,
            "Riesgo Ropa": riesgo_ropa,
            "Sugerencia EPP": ropa_desc
        })

# =========================
# VISUALIZACIÓN
# =========================
if resultados:
    df = pd.DataFrame(resultados)

    st.subheader(f"Resumen: {region_sel}")
    m_cols = st.columns(len(resultados))

    for i, res in enumerate(resultados):
        with m_cols[i]:
            st.metric(res["Faena"], f"{res['WBGT']:.1f} WBGT", res["Estado WBGT"])

    st.markdown("### 📋 Detalle Técnico Operacional")

    def color_wbgt(val):
        if '🟢' in str(val): return 'background-color: #d4edda'
        if '🟡' in str(val): return 'background-color: #fff3cd'
        if '🟠' in str(val): return 'background-color: #ffe5d0'
        if '⛔' in str(val): return 'background-color: #f8d7da'
        return ''

    st.dataframe(
        df.style.format({
            "Temp °C": "{:.1f}",
            "Viento km/h": "{:.1f}",
            "Radiación W/m²": "{:.0f}",
            "Sensación °C": "{:.1f}",
            "WBGT": "{:.1f}"
        }).map(color_wbgt, subset=['Estado WBGT']),
        use_container_width=True
    )

st.caption(f"Actualizado: {datetime.now().strftime('%H:%M')} | Sistema con radiación solar ☀️")
