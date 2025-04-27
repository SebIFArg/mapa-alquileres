import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import gspread
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials

# --- Autenticación usando st.secrets corregido ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

credentials_dict = {
    "type": st.secrets.GOOGLE_SERVICE_ACCOUNT.type,
    "project_id": st.secrets.GOOGLE_SERVICE_ACCOUNT.project_id,
    "private_key_id": st.secrets.GOOGLE_SERVICE_ACCOUNT.private_key_id,
    "private_key": st.secrets.GOOGLE_SERVICE_ACCOUNT.private_key.replace("\\n", "\n"),
    "client_email": st.secrets.GOOGLE_SERVICE_ACCOUNT.client_email,
    "client_id": st.secrets.GOOGLE_SERVICE_ACCOUNT.client_id,
    "auth_uri": st.secrets.GOOGLE_SERVICE_ACCOUNT.auth_uri,
    "token_uri": st.secrets.GOOGLE_SERVICE_ACCOUNT.token_uri,
    "auth_provider_x509_cert_url": st.secrets.GOOGLE_SERVICE_ACCOUNT.auth_provider_x509_cert_url,
    "client_x509_cert_url": st.secrets.GOOGLE_SERVICE_ACCOUNT.client_x509_cert_url,
    "universe_domain": st.secrets.GOOGLE_SERVICE_ACCOUNT.universe_domain,
}

creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
client = gspread.authorize(creds)

# --- Cargar datos desde Google Sheets ---
sheet = client.open("alquileres_sebarg").sheet1
df = get_as_dataframe(sheet)

# --- Debug: mostrar contenido crudo de la planilla ---
st.subheader("📋 Debug - Contenido crudo de la planilla")
st.dataframe(df)

# --- Validar que existan las columnas necesarias ---
columnas_requeridas = {"titulo", "precio", "superficie", "cochera", "lat", "lon", "url"}
if columnas_requeridas.issubset(df.columns):
    # Solo trabajamos si están todas las columnas
    df = df.dropna(subset=["lat", "lon"])
    
    # Convertir precio a número
    df["precio_num"] = df["precio"].astype(str).str.replace(r"[^0-9]", "", regex=True).astype(float)

    # --- Filtros ---
    st.sidebar.title("Filtros")
    precio_max = st.sidebar.slider("Precio máximo", 50000, 800000, 250000, step=10000)
    cochera = st.sidebar.checkbox("Solo con cochera")

    df_filtrado = df[df["precio_num"] <= precio_max]
    if cochera:
        df_filtrado = df_filtrado[df_filtrado["cochera"] == True]

    # --- Mostrar mapa ---
    st.title("🏡 Mapa de alquileres en Belgrano")

    if df_filtrado.empty:
        st.warning("⚠️ No hay resultados para los filtros aplicados.")
    else:
        mapa = folium.Map(location=[-34.562, -58.45], zoom_start=14)
        for _, row in df_filtrado.iterrows():
            popup = folium.Popup(
                f"<b>{row['titulo']}</b><br>"
                f"Precio: {row['precio']}<br>"
                f"Superficie: {row['superficie']} m²<br>"
                f"Cochera: {'Sí' if row['cochera'] else 'No'}<br>"
                f"<a href='{row['url']}' target='_blank'>Ver aviso</a>",
                max_width=300
            )
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=6,
                color="blue",
                fill=True,
                fill_color="blue",
                popup=popup
            ).add_to(mapa)

        st_folium(mapa, width=700, height=500)

else:
    st.error("❌ ERROR: La hoja de Google Sheets no contiene todas las columnas necesarias ('titulo', 'precio', 'superficie', 'cochera', 'lat', 'lon', 'url').")

