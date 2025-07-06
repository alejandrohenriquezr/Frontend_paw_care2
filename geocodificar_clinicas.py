import pandas as pd
import requests
import time

# Cargar las bases
df = pd.read_csv("data/clinicas.csv", sep=";")
dpa = pd.read_csv("data/dpa.csv", sep=";")

# Unir nombre de la comuna
df = df.merge(dpa[["id_dpa", "Nombre_Comuna"]], left_on="dpa", right_on="id_dpa", how="left")

# Función para obtener coordenadas
def obtener_coordenadas(direccion, comuna):
    direccion_completa = f"{direccion}, {comuna}, Chile"
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={direccion_completa}"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        if data:
            return data[0]["lat"], data[0]["lon"]
        else:
            return None, None
    except Exception as e:
        print(f"⚠️ Error con '{direccion_completa}': {e}")
        return None, None

# Inicializar listas
latitudes = []
longitudes = []

# Recorrer cada dirección
print("📍 Iniciando geocodificación...")
for i, row in df.iterrows():
    direccion = row["direccion"]
    comuna = row["Nombre_Comuna"]
    print(f"🔎 ({i+1}/{len(df)}): {direccion}, {comuna}")
    lat, lon = obtener_coordenadas(direccion, comuna)
    latitudes.append(lat)
    longitudes.append(lon)
    time.sleep(1)  # Espera para no ser bloqueado

# Agregar columnas al DataFrame
df["latitud"] = latitudes
df["longitud"] = longitudes

# Guardar archivo nuevo
df.to_csv("data/clinicas_geolocalizadas.csv", sep=";", index=False)
print("✅ Archivo guardado: data/clinicas_geolocalizadas.csv")
