import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

# --- Autenticación ---

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(creds)

# --- Cargar datos ---
sheet = client.open("alquileres_sebarg").sheet1
df = get_as_dataframe(sheet.get_worksheet(0)).dropna(subset=["lat", "lon"])
df["precio_num"] = df["precio"].str.replace(r"[^0-9]", "", regex=True).astype(float)

# --- Filtros ---
st.sidebar.title("Filtros")
precio_max = st.sidebar.slider("Precio máximo", 50000, 800000, 250000, step=10000)
cochera = st.sidebar.checkbox("Solo con cochera")
df_filtrado = df[df["precio_num"] <= precio_max]
if cochera:
    df_filtrado = df_filtrado[df_filtrado["cochera"] == True]

# --- Mapa ---
st.title("Mapa de alquileres en Belgrano")
mapa = folium.Map(location=[-34.562, -58.45], zoom_start=14)
for _, row in df_filtrado.iterrows():
    popup = folium.Popup(f"<b>{row['titulo']}</b><br>"
                     f"Precio: {row['precio']}<br>"
                     f"Superficie: {row['superficie']}<br>"
                     f"Cochera: {'Sí' if row['cochera'] else 'No'}<br>"
                     f"<a href='{row['url']}' target='_blank'>Ver aviso</a>", max_width=300)
    folium.CircleMarker(location=[row["lat"], row["lon"]], radius=6, color="blue",
                        fill=True, fill_color="blue", popup=popup).add_to(mapa)

st_folium(mapa, width=700, height=500)
