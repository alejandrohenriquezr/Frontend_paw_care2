from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from authlib.integrations.flask_client import OAuth
import os
import base64
import requests
from config import Config
import jwt
import pandas as pd
import unicodedata

app = Flask(__name__)
app.config.from_object(Config)

def get_google_provider_cfg():
    return requests.get(Config.GOOGLE_DISCOVERY_URL).json()

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v3/',
    authorize_params={"prompt": "select_account"},
    access_token_url='https://www.googleapis.com/oauth2/v4/token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri="http://127.0.0.1:5000/login/callback",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

# 📌 Ruta principal
@app.route("/")
def home():
    return render_template("index.html")

def generate_nonce(length=16):
    """Genera un valor único para el nonce."""
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8')

# 📌 Ruta de inicio de sesión con Google
@app.route("/login")
def login():
    nonce = generate_nonce()
    session['nonce'] = nonce
    redirect_uri = url_for('callback', _external=True)
    return google.authorize_redirect(redirect_uri, nonce=nonce)

# 📌 Ruta de callback (Google redirige aquí después de autenticación)
@app.route("/login/callback")
def callback():
    token = google.authorize_access_token()

    # Obtener metadatos de OpenID de Google
    google_provider_cfg = get_google_provider_cfg()
    jwks_uri = google_provider_cfg.get("jwks_uri")
    
    if not jwks_uri:
        return "Error: No se encontró 'jwks_uri' en los metadatos de Google", 500

    # Validar token con nonce
    nonce = session.pop("nonce", None)  # Obtener nonce de la sesión
    if nonce is None:
        return "Error: Nonce missing", 400

    user_info = google.parse_id_token(token, nonce=nonce)  # ← Aquí agregamos nonce

    # Guardar la sesión del usuario
    session["user"] = user_info
    return redirect(url_for("sitio_privado"))

# 📌 Ruta de Dashboard (Solo accesible si está autenticado)
@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("home"))
    
    return f"Bienvenido {user['name']} ({user['email']})"

# 📌 Ruta de logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    id_token = token.get('id_token')
    claims = jwt.decode(id_token, options={"verify_signature": False})
    if claims['nonce'] != session['nonce']:
        return 'Error: Nonce no coincide'
    # Procesar el token y la sesión del usuario
    return redirect(url_for('sitio_privado'))

@app.route('/sitio_privado')
def sitio_privado():
    user = session.get("user")
    print(session.get("user"))
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template('sitio_privado.html', user=user)

@app.route("/api/clinicas", methods=["GET"])
def obtener_clinicas():
    try:
        # 🔥 Cargar el CSV
        df = pd.read_csv("data/clinicas.csv", delimiter=";")

        # 🔥 Renombrar columnas para evitar espacios en blanco
        df.columns = df.columns.str.strip()

        # 🔍 Convertir a JSON y devolver
        clinicas_json = df.to_dict(orient="records")
        return jsonify({"clinicas": clinicas_json})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sugerencias", methods=["GET"])
def obtener_sugerencias():
    query = request.args.get("q", "").lower()  # Obtener el texto ingresado por el usuario
    query = remover_tildes(query)  # 🔥 Eliminar tildes de la búsqueda
    resultados = []

    if query:
        try:
            print("📂 Intentando leer el archivo: data/clinicas.csv")  # Depuración
            df = pd.read_csv("data/clinicas.csv", sep=";")  # Leer el archivo CSV

            print("✅ Archivo CSV leído correctamente")

            # Mostrar las primeras filas del archivo en la consola
            print("🔍 Primeras filas del CSV:\n", df.head())

            # Verificar si la columna existe en el CSV
            if "nombre" not in df.columns:
                print("❌ ERROR: La columna 'nombre' no existe en el CSV")
                return 
            clinicas = df["nombre"].dropna().unique()  # Obtener nombres únicos
            
            # Filtrar sugerencias que contengan el texto ingresado
            resultados = [c for c in clinicas if query in remover_tildes(c.lower())]                
        except Exception as e:
            print(f"❌ ERROR al leer el CSV: {str(e)}")  # Mostrar error en la terminal
            return jsonify({"error": f"Error al leer el CSV: {str(e)}"}), 500

    return jsonify(resultados)  # Devolver sugerencias en formato JSON

def remover_tildes(texto):
    """Elimina las tildes de un texto"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn'
    )

@app.route("/cerrar_sesion")
def cerrar_sesion():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)