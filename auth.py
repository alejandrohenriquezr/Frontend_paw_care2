from flask import Flask, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
import os
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY  # Se necesita para manejar sesiones
oauth = OAuth(app)

# Configurar el cliente OAuth con Google
google = oauth.register(
    name="google",
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={
        "scope": "openid email profile",
        "nonce": "random_nonce_value"  # Agregar este parámetro
    }
)

@app.route("/login")
def google_login():
    session["nonce"] = os.urandom(16).hex()  # Generar un nonce aleatorio
    return google.authorize_redirect(
        url_for("google_callback", _external=True),
        nonce=session["nonce"]  # Pasar el nonce en la solicitud
    )

@app.route("/login/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token, nonce=session.pop("nonce", None))

    if user_info:
        session["user"] = user_info
        return redirect(url_for("sitio_privado"))  # Redirigir a la página protegida
    else:
        return "Error en la autenticación", 400


@app.route("/sitio_privado")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    return f"Hola, {user['name']}! <a href='/logout'>Cerrar sesión</a>"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

