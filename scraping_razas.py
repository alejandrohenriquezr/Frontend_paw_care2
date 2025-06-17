import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Función para limpiar nombres
def limpiar_texto(texto):
    return texto.strip().replace("\n", "").replace("\xa0", " ")

# Diccionario base para especies y sus URLs principales
especies_urls = {
    3: {"grupo": "Vacuno", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Razas_bovinas"},
    4: {"grupo": "Pez", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Peces_de_acuario"},
    5: {"grupo": "Ave", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Razas_aviar"},
    6: {"grupo": "Ave de corral", "url": "https://es.wikipedia.org/wiki/Anexo:Razas_de_gallinas"},
    7: {"grupo": "Reptil", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Reptiles_como_mascotas"},
    8: {"grupo": "Arácnido", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Ar%C3%A1cnidos"},
    9: {"grupo": "Insecto", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Insectos"},
    10: {"grupo": "Caprino", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Razas_caprinas"},
    11: {"grupo": "Rana", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Anfibios"},
    12: {"grupo": "Sapo", "url": "https://es.wikipedia.org/wiki/Categor%C3%ADa:Bufonidae"}
}

# Lista para almacenar todas las razas extraídas
data = []

for id_especie, info in especies_urls.items():
    grupo = info["grupo"]
    url = info["url"]

    print(f"Extrayendo de {grupo}: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar todos los enlaces dentro del contenido principal
    enlaces = soup.select("div.mw-parser-output ul li a")
    for i, enlace in enumerate(enlaces):
        nombre_raza = limpiar_texto(enlace.get_text())
        link = "https://es.wikipedia.org" + enlace.get("href") if enlace.get("href") else ""

        data.append({
            "id_raza": len(data) + 1,
            "nombre_raza": nombre_raza,
            "grupo": grupo,
            "sub_grupo": "",
            "pais": "",
            "url": link,
            "image": "",
            "pdf": "",
            "id_especie": id_especie
        })

        # Limitar para pruebas (quitar este bloque para modo full)
        if i > 50:
            break

        time.sleep(0.1)  # Evitar sobrecarga

# Guardar DataFrame a CSV
output = pd.DataFrame(data)
output.to_csv("razas_extraidas_auto.csv", index=False, encoding='utf-8')
print("CSV generado con", len(output), "razas.")
