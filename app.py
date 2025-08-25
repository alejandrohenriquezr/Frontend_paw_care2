from flask import Flask, send_file, abort, redirect, url_for, session, request, jsonify, render_template, send_from_directory
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from flask_mail import Mail, Message
from functools import wraps
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime, timedelta
#from fpdf import FPDF
#from docxtpl import DocxTemplate
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from google.oauth2 import service_account
from googleapiclient.discovery import build
from flask_session import Session
from werkzeug.utils import secure_filename
from math import radians, cos, sin, sqrt, atan2

# Para Transbank
#from flask import Flask, render_template, redirect, url_for, request
from transbank.webpay.webpay_plus.transaction import Transaction
from docx import Document
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import render_template_string
from google.oauth2.credentials import Credentials

import os, math
import base64
import requests
from config import Config
import jwt
import pandas as pd
import unicodedata
import csv
import io
import json
import uuid #Para generar los id de sesión para transbank
import fitz  # PyMuPDF
import pypandoc
import pytz
import numpy as np  # importar numpy para usar np.nan
import time
import re
import locale
import platform


#configuración de la APP
app = Flask(__name__)
app.config.from_object(Config)
Session(app)  # FALTA ESTA LÍNEA
#app.secret_key = os.urandom(24)
#app.secret_key = app.config["SECRET_KEY"]
#app.config["SESSION_COOKIE_SECURE"] = app.config["SESSION_COOKIE_SECURE"]
#app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

#Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'alhen1970@gmail.com'
app.config['MAIL_PASSWORD'] = 'ptjt fgco uoia jgyx'

mail = Mail(app)

# Detecta si está en Render o en local
RENDER = os.environ.get('RENDER', False)

if RENDER:
    REDIRECT_URI = "https://paw-care-app.onrender.com/login/callback"
else:
    REDIRECT_URI = "http://127.0.0.1:5000/login/callback"


# Detecta sistema operativo
so = platform.system()
# Configura el locale (para los meses del año) según el sistema operativo
try:
    if so == "Windows":
        # En Windows el locale suele ser "Spanish_Chile.1252" o "Spanish_Spain.1252"
        locale.setlocale(locale.LC_TIME, "Spanish_Spain.1252")
    elif so == "Darwin":  # macOS
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
    else:  # Linux y otros
        locale.setlocale(locale.LC_TIME, "es_ES.utf8")
except locale.Error:
    # Fallback por si el sistema no tiene instalado ese locale
    locale.setlocale(locale.LC_TIME, "")

# Configuración de OAuth
def get_google_provider_cfg():
    return requests.get(Config.GOOGLE_DISCOVERY_URL).json()

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    #authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v3/',
    #authorize_params={"prompt": "select_account"},
    #access_token_url='https://www.googleapis.com/oauth2/v4/token',
    access_token_url='https://oauth2.googleapis.com/token',
   # access_token_params=None,
    # refresh_token_url=None,
    #redirect_uri="http://127.0.0.1:5000/login/callback",
    #redirect_uri='https://paw-care-app.onrender.com/callback',
    redirect_uri=REDIRECT_URI,
    #client_kwargs={"scope": "openid email profile"},
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/calendar',
        'access_type': 'offline',
        'prompt': 'consent'
    },
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

# Configuración de la ruta de archivos estáticos
UPLOAD_FOLDER = "data/certificados"
CSV_FILE = "data/certificados.csv"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cargar una vez el CSV
staff_clinica_df=pd.read_csv("data/staff_clinica.csv", sep=";")
clinicas_df = pd.read_csv("data/clinicas.csv", sep=";")
staff_df = pd.read_csv("data/staff.csv", sep=";")
clinicas_especialidades_df = pd.read_csv("data/clinicas_especialidades.csv", sep=";")
especialidades_df = pd.read_csv("data/especialidades.csv", sep=";")
precios_df = pd.read_csv("data/precios.csv", sep=";")
dpa_df = pd.read_csv("data/dpa.csv", sep=";")
reservas_df = pd.read_csv("data/reservas.csv", sep=";")


prestaciones_df = pd.read_csv("data/prestaciones.csv", sep=";")
veterinario_especialidades_df = pd.read_csv("data/veterinario_prestaciones.csv", sep=";")
veterinario_prestaciones_df = veterinario_especialidades_df.copy()


#eliminamos los registros duplicado de id_especialidad para cada id_veterinario

#####################
## Preparamos el dataframe del listado de veterinarios, sus especialidad, las clínicas en que 
## trabajan y los precios que cobre

# 1. A veterinario_especialidades_df le unimos los datos del veterinario
veterinario_especialidades_df = veterinario_especialidades_df.merge(
    staff_df[["id_veterinario", "nombres", "apellidos", "sexo"]],
    left_on="id_veterinario",
    right_on="id_veterinario",
    how="left"    
)
veterinario_especialidades_df.to_csv("data/veterinario_especialidades_df_1.csv", sep=";", index=False)

# 2. A veterinario_especialidades_df le unimos los datos de las especialidades
veterinario_especialidades_df = veterinario_especialidades_df.merge(
    especialidades_df[["id_especialidad", "especialidad"]],
    left_on="id_especialidad",
    right_on="id_especialidad",
    how="left"
)
veterinario_especialidades_df.to_csv("data/veterinario_especialidades_df_2.csv", sep=";", index=False)

# 3. A veterinario_especialidades_df le unimos el id_clinica de donde trabajan
veterinario_especialidades_df = veterinario_especialidades_df.merge(
    staff_clinica_df[["id_veterinario", "id_clinica"]],
    left_on="id_veterinario",
    right_on="id_veterinario",
    how="left"
)
veterinario_especialidades_df.to_csv("data/veterinario_especialidades_df_3.csv", sep=";", index=False)

# 4. A veterinario_especialidades_df le unimos los datos de la clínica donde trabajan
veterinario_especialidades_df = veterinario_especialidades_df.merge(
    clinicas_df[["id_clinica", "nombre", "direccion", "n_calificaciones", "calificacion", "latitud", "longitud", "dpa"]],
    left_on="id_clinica",
    right_on="id_clinica",
    how="left"
)
veterinario_especialidades_df["latitud"] = pd.to_numeric(veterinario_especialidades_df["latitud"].str.replace(",", "."), errors="coerce")
veterinario_especialidades_df["longitud"] = pd.to_numeric(veterinario_especialidades_df["longitud"].str.replace(",", "."), errors="coerce")
# 4.1 renombramos nombre por nombre_clinica
veterinario_especialidades_df.rename(columns={"nombre": "nombre_clinica"}, inplace=True)

veterinario_especialidades_df.to_csv("data/veterinario_especialidades_df_4.csv", sep=";", index=False)

# 5. obtenemos los precios mínimos para la combinación de id_clinica y id_especialidad
minimos_df = precios_df.groupby(["id_clinica", "id_especialidad"], as_index=False)["valor"].min()
precios_df.to_csv("data/precios_df_1.csv", sep=";", index=False)

# 6. A veterinario_especialidades_df le unimos los precios mínimos
veterinario_especialidades_df = veterinario_especialidades_df.merge(
    minimos_df[["id_clinica", "id_especialidad", "valor"]],
    left_on=["id_clinica", "id_especialidad"],
    right_on=["id_clinica", "id_especialidad"],
    how="left"
)

#6.1 Reemplazamos los "." por "," en valor
#veterinario_especialidades_df["valor"] = veterinario_especialidades_df["valor"].astype(str).str.replace(".", ",")
#si veterinario_especialidades_df["valor"] es vacio o nulo le asignamos un 0
veterinario_especialidades_df["valor"] = veterinario_especialidades_df["valor"].fillna(0)

# Pasamos la columna valor a numero entero sin decimales
veterinario_especialidades_df["valor"] = veterinario_especialidades_df["valor"].astype(int)

veterinario_especialidades_df.to_csv("data/veterinario_especialidades_df_5.csv", sep=";", index=False)

# 7. a veterinario_especialidades_df le agregamos el nombre de la comuna
veterinario_especialidades_df = veterinario_especialidades_df.merge(
    dpa_df[["id_dpa", "Nombre_Comuna"]],
    left_on="dpa",
    right_on="id_dpa",
    how="left"
)

#8. a veterinario_especialidades_df le creamos la columna nombre_completo para facilitar la búsqueda
veterinario_especialidades_df['nombre_completo'] = veterinario_especialidades_df['nombres'] + " " + veterinario_especialidades_df['apellidos']

##FIN de Preparamos el dataframe del listado de veterinarios

###################
## Preparamos veterinario_prestaciones_df

# 1. A veterinario_prestaciones_df le unimos los datos de prestaciones_df
veterinario_prestaciones_df = veterinario_prestaciones_df.merge(
    prestaciones_df[["id_prestacion", "prestacion"]],
    left_on="id_prestacion",
    right_on="id_prestacion",
    how="left"
)


def construir_google_credentials(token_authlib):
    return Credentials(
        token=token_authlib['access_token'],
        refresh_token=token_authlib.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,        
        scopes=['https://www.googleapis.com/auth/calendar']
    )



# 📌 Ruta principal
@app.route("/")
def index():
    #si no hay argumentos ni rutas en la url, entonces eliminamos las variables de sesion comuna
    resultado_busqueda = None  # ✅ Definición inicial
    if not request.args:
        #eliminar las variables de session
        session["comuna"] = None
        session["busqueda"] = None
        session["comuna2"] = None
        #session["user"] = None
        print("[INFO] No hay argumentos en la URL, eliminando variables de sesión comuna y busqueda")
    else:

        print("[INFO] Hay argumentos en la URL, no se eliminan las variables de sesión comuna y busqueda")
        if "comuna" in request.args:
            comuna = request.args.get("comuna")
            session["comuna"] = comuna
            session["comuna2"] = comuna
            print(f"[INFO] Comuna obtenida de la URL del INDEX: {comuna}")
        else:
            comuna = 0
            session["comuna"] = comuna
            print(f"[INFO] busqueda obtenida de la URL del INDEX: {comuna}")              

        if "search" in request.args:
            busqueda = request.args.get("search")
            session["busqueda"] = busqueda
            print(f"[INFO] busqueda obtenida de la URL del INDEX: {busqueda}")
        else:
            busqueda = ""
            session["busqueda"] = busqueda
            print(f"[INFO] busqueda obtenida de la URL del INDEX: {busqueda}")            
        #ejecutamos la función obtener_clinicas()
        print(f"DEBUG index busqueda es {busqueda} y comuna es {comuna}")
        resultado_busqueda = obtener_resultado(busqueda, comuna)

        
    user=session.get("user", None)
    #session.clear()
    print(f"[INFO] user: {user}")
    # Verificar si el usuario está autenticado
    #si el usuario está autenticado, entonces redirigie a intex.html y entregar los datos del usuario
    if user:
        print(f"[INFO] usuario autenticado: {user}")
        # Redirigir a la página de inicio de sesión
        if resultado_busqueda:
            return render_template("index.html", user=user, veterinario_especialidades=resultado_busqueda[0], veterinario_prestaciones=resultado_busqueda[1], reservas=resultado_busqueda[2])
        else:
            return render_template("index.html", user=user)
    else:
        print(f"[INFO] usuario no autenticado: {user}")
        # Redirigir a la página de inicio de sesión
        if resultado_busqueda:
            return render_template("index.html", veterinario_especialidades=resultado_busqueda[0], veterinario_prestaciones=resultado_busqueda[1], reservas=resultado_busqueda[2])
        else:
            return render_template("index.html")
    #return render_template("index.html", user=user)



@app.route("/agendar2", methods=["POST"])
def agendar2():
    id_clinica = request.form.get("id_clinica")
    clinica = request.form.get("clinica")
    calificacion = request.form.get("calificacion")
    ncalificaciones = request.form.get("ncalificaciones")
    comuna = request.form.get("comuna")
    id_veterinario = request.form.get("veterinario")
    hora = request.form.get("hora")
    idprestacion = request.form.get("idprestacion")
    idespecialidad = request.form.get("idespecialidad")
    especialidad = request.form.get("especialidad")
    valor = request.form.get("valor")
    fecha = request.form.get("fecha")

    print("IdClínica:", id_clinica)
    print("Clínica:", clinica)
    print("comuna:", comuna)
    print("calificacion:", calificacion)
    print("ncalificaciones:", ncalificaciones)
    print("Veterinario:", id_veterinario)
    print("Hora:", hora)
    print("idprestacion:", idprestacion)
    print("idespecialidad:", idespecialidad)
    print("especialidad:", especialidad)
    print("valor:", valor)
    print("fecha:", fecha)

    staff_filtrado_df = staff_df.copy()
    print("staff_filtrado_df_1")
    print(staff_filtrado_df)

    staff_filtrado_df = staff_filtrado_df[staff_filtrado_df["id_veterinario"] == int(id_veterinario)]   
    print("staff_filtrado_df")
    print(staff_filtrado_df)


    # Puedes ahora renderizar tu template con esos datos
    return render_template("agendar2.html", 
                           id_clinica=id_clinica, 
                           clinica=clinica, 
                           comuna=comuna,
                           calificacion=calificacion,
                           ncalificaciones=ncalificaciones,
                           id_veterinario=id_veterinario, 
                           hora=hora,
                           idprestacion=idprestacion,
                           idespecialidad=idespecialidad,
                           especialidad=especialidad,
                           valor=valor,
                           fecha=fecha, 

                           veterinario=staff_filtrado_df.to_dict(orient="records"))


@app.route("/finalizar_pago", methods=["POST", "GET"])
def finalizar_pago():
    print(f"request.method={request.method}")
    if request.method == "POST":
        datos = request.form.to_dict()
        session["reserva_en_proceso"] = datos
        print("Variables de sesión en finalizar_pago:")
        for key, value in session.items():  
            print(f"{key}: {value}")  

        user = session.get('user')

        print("POST")
        if user:
            correo = session.get("correo_cliente") or user.get("email")
            print("DEBUG correo=", correo)
            # leer clientes_mascotas.csv según el correo
            df = pd.read_csv("data/clientes_mascotas.csv", sep=";")
            df_filtrado = df[df["correo_cliente"].str.strip() == correo.strip()]
            mascotas = df_filtrado[["id_clientes_mascotas", "correo_cliente", "nombre_mascota"]].to_dict(orient="records")
            return render_template("finalizar_pago.html", user=session["user"], clientes_mascotas=mascotas, **datos)
        else:
            return render_template("finalizar_pago.html", user=None, clientes_mascotas=[], **datos)
        #return redirect("finalizar_pago")

    elif request.method == "GET":
        datos = session.get("reserva_en_proceso")
        user = session.get("user")
        print(f"datos={datos}")
        print(f"user={user}")
        if not datos and not user:
            print("not datos and not user")
            return redirect("/")  # si no hay datos, volver al inicio
        elif datos and user:
            print("Tipo de user:", type(user))
            print("user:", (user))
            email_user=user["email"]
            clientes_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
            clientes_mascotas = clientes_mascotas[clientes_mascotas["correo_cliente"]==email_user]
            print(f"clientes_mascotas{clientes_mascotas}")
            clientes_mascotas=clientes_mascotas.to_dict(orient="records")
            return render_template("finalizar_pago.html", **datos, user=user,clientes_mascotas=clientes_mascotas)

        return render_template("finalizar_pago.html", **datos, user=None,clientes_mascotas=None)




@app.route("/finalizar_pago0", methods=["POST"])
def finalizar_pago0():
    id_clinica = request.form.get("id_clinica")
    clinica = request.form.get("clinica")
    nombresvet = request.form.get("nombresvet")
    apellidosvet = request.form.get("apellidosvet")
    calificacion = request.form.get("calificacion")
    ncalificaciones = request.form.get("ncalificaciones")
    comuna = request.form.get("comuna")
    direccion = request.form.get("direccion")
    id_veterinario = request.form.get("veterinario")
    hora = request.form.get("hora")
    idprestacion = request.form.get("idprestacion")
    idespecialidad = request.form.get("idespecialidad")
    especialidad = request.form.get("especialidad")
    valor = request.form.get("valor")
    fecha = request.form.get("fecha")

    print("IdClínica:", id_clinica)
    print("Clínica:", clinica)
    print("comuna:", comuna)
    print("direccion:", direccion)
    print("calificacion:", calificacion)
    print("ncalificaciones:", ncalificaciones)
    print("Veterinario:", id_veterinario)
    print("Hora:", hora)
    print("idprestacion:", idprestacion)
    print("idespecialidad:", idespecialidad)
    print("especialidad:", especialidad)
    print("valor:", valor)
    print("fecha:", fecha)

    staff_filtrado_df = staff_df.copy()
    print("staff_filtrado_df_1")
    print(staff_filtrado_df)

    staff_filtrado_df = staff_filtrado_df[staff_filtrado_df["id_veterinario"] == int(id_veterinario)]   
    print("staff_filtrado_df")
    print(staff_filtrado_df)


    # Puedes ahora renderizar tu template con esos datos
    return render_template("finalizar_pago.html", 
                           id_clinica=id_clinica, 
                           clinica=clinica, 
                           comuna=comuna,
                           direccion=direccion,
                           nombresvet=nombresvet,
                           apellidosvet=apellidosvet,
                           calificacion=calificacion,
                           ncalificaciones=ncalificaciones,
                           id_veterinario=id_veterinario, 
                           hora=hora,
                           idprestacion=idprestacion,
                           idespecialidad=idespecialidad,
                           especialidad=especialidad,
                           valor=valor,
                           fecha=fecha, 

                           veterinario=staff_filtrado_df.to_dict(orient="records"))


# 📌 Ruta nuevo agendar
@app.route("/agendar3")
def agendar3():
    #si no hay argumentos ni rutas en la url, entonces eliminamos las variables de sesion comuna
    resultado_busqueda = None  # ✅ Definición inicial
    if not request.args:
        #eliminar las variables de session
        session["comuna"] = None
        session["busqueda"] = None
        session["comuna2"] = None
        print("[INFO] No hay argumentos en la URL, eliminando variables de sesión comuna y busqueda")
    else:

        print("[INFO] Hay argumentos en la URL, no se eliminan las variables de sesión comuna y busqueda")
        if "comuna" in request.args:
            comuna = request.args.get("comuna")
            session["comuna"] = comuna
            session["comuna2"] = comuna

        if "search" in request.args:
            busqueda = request.args.get("search")
            session["busqueda"] = busqueda

        print(f"[INFO] Comuna obtenida de la URL del INDEX: {comuna}")
        print(f"[INFO] busqueda obtenida de la URL del INDEX: {busqueda}")
        #ejecutamos la función obtener_clinicas()
        
        resultado_busqueda = obtener_resultado(busqueda, comuna)

        
    user=session.get("user", None)
    print(f"[INFO] user: {user}")
    # Verificar si el usuario está autenticado
    #si el usuario está autenticado, entonces redirigie a intex.html y entregar los datos del usuario
    if user:
        print(f"[INFO] usuario autenticado: {user}")
        # Redirigir a la página de inicio de sesión
        if resultado_busqueda:
            return render_template("index.html", user=user, veterinario_especialidades=resultado_busqueda[0], veterinario_prestaciones=resultado_busqueda[1], reservas=resultado_busqueda[2])
        else:
            return render_template("index.html", user=user)
    else:
        print(f"[INFO] usuario no autenticado: {user}")
        # Redirigir a la página de inicio de sesión
        if resultado_busqueda:
            return render_template("index.html", veterinario_especialidades=resultado_busqueda[0], veterinario_prestaciones=resultado_busqueda[1], reservas=resultado_busqueda[2])
        else:
            return render_template("index.html")
    #return render_template("index.html", user=user)


def obtener_resultado(busqueda, comuna):
    ################
    ## Preparamos el dataframe para clinicas_filtrada_df para entregarlo en la respuesta
    print(f"obtener_resultado(busqueda, comuna)={busqueda} y {comuna}")
    clinicas_filtrada_df = veterinario_especialidades_df.copy()
    #print("head clinicas_filtrada_df")
    #print(clinicas_filtrada_df.head())
    clinicas_filtrada_comuna_df = clinicas_filtrada_df[clinicas_filtrada_df["dpa"]==int(comuna)]
    if not clinicas_filtrada_comuna_df.empty and busqueda: #Indica que sí hay una comuna en la búsqueda
        print("Existe comuna criterio de bùsqueda")
        clinicas_filtrada_df = clinicas_filtrada_comuna_df[clinicas_filtrada_comuna_df["especialidad"] == busqueda]
        if clinicas_filtrada_df.empty: #entonces está buscando por nombre del veterinario
            #debo buscar los datos del veterinario y las clinicas donde trabaja
            print("clinicas_filtrada_comuna_df filtrada por comuna")
            print(clinicas_filtrada_comuna_df)
            print("Buscando por nombre")
            staff_clinica= pd.read_csv("data/staff_clinica.csv", sep=";")
            staff= pd.read_csv("data/staff.csv", sep=";")
            staff['nombre_completo'] = staff['nombres'] + " " + staff['apellidos']
            staff_original=staff.copy()
            staff=staff[staff["nombre_completo"] == busqueda]
            id_veterinario = None  # valor por defecto
            if staff.empty: #Entonces estoy buscando por clínica
                staff = staff_original
                clinicas= pd.read_csv("data/clinicas.csv", sep=";")
                clinicas = clinicas[clinicas["nombre"] == busqueda]
                id_clinica=clinicas["id_clinica"].values[0]
                staff_clinica=staff_clinica[staff_clinica["id_clinica"] == id_clinica]
            else:
                id_veterinario=staff["id_veterinario"].values[0]        
                staff_clinica=staff_clinica[staff_clinica["id_veterinario"] == id_veterinario]
                clinicas= pd.read_csv("data/clinicas.csv", sep=";")

            print("DEBUG staff en obtener_resultado es")
            print(staff)
            print("DEBUG staff_clinica en obtener_resultado es")
            print(staff_clinica)    

         

            staff_clinica=staff_clinica.merge(
                staff[["id_veterinario", "nombres", "apellidos", "sexo", "correo", "estado", "valor"]],
                left_on="id_veterinario",
                right_on="id_veterinario",
                how="left"
            )
            print("DEBUG staff_clinica filtrado por id_veterinario en obtener_resultado es")
            print(staff_clinica)                 

            
            clinicas_filtrada_df = staff_clinica.merge(
                clinicas[["id_clinica", "nombre", "direccion", "dpa", "n_calificaciones", "calificacion", "latitud", "longitud", "estado"]],
                left_on="id_clinica",
                right_on="id_clinica",
                how="left"
            )
            print("DEBUG clinicas_filtrada_df filtrado por id_veterinario en obtener_resultado es")
            print(clinicas_filtrada_df)  

            veterinario_prestaciones=pd.read_csv("data/veterinario_prestaciones.csv", sep=";")
            #Si id_veterinario existe

            if id_veterinario is not None:
                veterinario_prestaciones=veterinario_prestaciones[veterinario_prestaciones["id_veterinario"] == id_veterinario]
            else:
                # veterinario_prestaciones contendrá todos los registros de veterinario_prestaciones que coincidan con el campo id_veterinario de staff_clinica
                veterinario_prestaciones=veterinario_prestaciones[veterinario_prestaciones["id_veterinario"].isin(staff_clinica["id_veterinario"])]
            #clinicas_filtrada_df = clinicas_filtrada_df.merge(
            #    veterinario_prestaciones[["id_veterinario", "id_vet_especialidad", "id_prestacion", "id_especialidad"]],
            #    left_on="id_veterinario",
            #    right_on="id_veterinario",
            #    how="left"
            #)
            print("clinicas_filtrada_df filtrada por nombre")
            print(clinicas_filtrada_df)

            #Le agregamos los precios
            #precios=pd.read_csv("data/precios.csv", sep=";")
            #clinicas_filtrada_df = clinicas_filtrada_df.merge(
            #    precios[["id_clinica", "id_especialidad", "valor"]],
            #    left_on=["id_clinica", "id_especialidad"],
            #    right_on=["id_clinica", "id_especialidad"],
            #    how="left"
            #)
            print("clinicas_filtrada_df filtrada por nombre con precios")
            print(clinicas_filtrada_df)

    else: # Indica que está buscando por id de la clínica
        
        if "id_clinica" in request.args:
            busqueda = request.args.get("id_clinica")
            print(f"INFO busqueda= {busqueda}")
            session["busqueda"] = busqueda
            print(f"tipo = {type(busqueda)}")
            #if isinstance(busqueda, str):
            #busqueda=int(busqueda)

            #print(f"isinstance(busqueda, int)={isinstance(busqueda, int)}")
        #if isinstance(busqueda, int):
        #    print(f"id_clinica={busqueda}")
            print(clinicas_filtrada_df.dtypes)
            print(f"int(busqueda)={int(busqueda)}")
            print(f"clinicas_filtrada_dfAAA=")
            clinicas_filtrada_df = veterinario_especialidades_df.copy()
            print(clinicas_filtrada_df["id_clinica"].unique())            
            clinicas_filtrada_df = clinicas_filtrada_df[clinicas_filtrada_df["id_clinica"] == int(busqueda)]
            print(f"clinicas_filtrada_dfxx=")
            print(clinicas_filtrada_df)
        
        else:
            print("Buscamos por comuna")
            clinicas_filtrada_df = clinicas_filtrada_df[clinicas_filtrada_df["dpa"]==int(comuna)]

    print(f"clinicas_filtrada_df")
    comunas= pd.read_csv("data/dpa.csv", sep=";")
    clinicas_filtrada_df = clinicas_filtrada_df.merge(
        comunas[["id_dpa", "Nombre_Comuna"]],
        left_on="dpa",
        right_on="id_dpa",
        how="left"
    )
    print(clinicas_filtrada_df)
    clinicas_filtrada_df.to_csv("data/clinicas_filtrada_df.csv", sep=";", index=False)


    ## FIN de preparamos el dataframe para clinicas_filtrada_df para entregarlo en la respuesta

    ###############
    ## Preparamos el dataframe para veterinario_prestaciones_filtrada_df para entregarlo en la respuesta

    veterinario_prestaciones_filtrada_df = veterinario_prestaciones_df.copy()
    if clinicas_filtrada_df.empty:
        jsonify({"error": "No se encontró la clínica buscada"}), 400

    # 1. Obtenemos el valor id_especialidad desde el primer registro de clinicas_filtrada_df
   # id_especialidad = clinicas_filtrada_df["id_especialidad"].values[0]

    # 2. filtramos veterinario_prestaciones_filtrada_df por el campo id_especialidad para el valor id_especialidad
    #veterinario_prestaciones_filtrada_df = veterinario_prestaciones_filtrada_df[veterinario_prestaciones_filtrada_df["id_especialidad"] == id_especialidad]
    veterinario_prestaciones_filtrada_df.to_csv("data/veterinario_prestaciones_filtrada_df.csv", sep=";", index=False)
    ###############
    #FIN de preparamos el dataframe para veterinario_prestaciones_filtrada_df para entregarlo en la respuesta

    ###############
    #INICIO filtrasmos reservas_df para la fecha de hoy
    reservas_filtradas_df = reservas_df.copy()
    #en reservas_filtradas_df nos quedamos con las columnas id_clinica,	fecha, hora, estado, medico_que_atendio
    reservas_filtradas_df = reservas_filtradas_df[["id_clinica", "fecha", "hora", "estado", "medico_que_atendio"]]
  

    reservas_filtradas_df = reservas_filtradas_df[reservas_filtradas_df["estado"] == 1]

    # Obtenemos la fecha de hoy
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    # Filtramos reservas_df por la fecha de hoy
    reservas_filtradas_df["fecha"] = pd.to_datetime(reservas_filtradas_df["fecha"], format='mixed', dayfirst=True, errors='coerce')

    reservas_filtradas_df = reservas_filtradas_df[reservas_filtradas_df["fecha"] == fecha_hoy]
    reservas_filtradas_df["hora_hhmm"] = reservas_filtradas_df["hora"].apply(lambda x: datetime.strptime(x, "%H:%M:%S").strftime("%H:%M"))
    print("reservas_filtradas_df_3:")
    print(reservas_filtradas_df)

    return clinicas_filtrada_df.to_dict(orient="records"), veterinario_prestaciones_filtrada_df.to_dict(orient="records"), reservas_filtradas_df.to_dict(orient="records")



@app.route("/api/reservas_veterinario")
def reservas_veterinario():
    fecha_str = request.args.get("fecha")
    id_clinica = int(request.args.get("id_clinica"))
    id_veterinario = int(request.args.get("id_veterinario"))

    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

    reservas_filtradas = reservas_df[
        (reservas_df["fecha"] == fecha) &
        (reservas_df["id_clinica"] == id_clinica) &
        (reservas_df["medico_que_atendio"] == id_veterinario)
    ]
    reservas_dict = reservas_filtradas.to_dict(orient="records")

    #return render_template("bloque_horas.html", reservas=reservas_dict)

    return jsonify({"reservas": reservas_dict})


@app.route('/api/reservas_por_fecha', methods=['POST'])
def reservas_por_fecha():
    data = request.get_json()
    fecha_str = data.get("fecha")
    print("fecha_str")
    print(fecha_str)
    print(type(fecha_str))

    try:
        #fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        #fecha = datetime.strptime(fecha_str, "%d-%m-%Y")

        #fecha = fecha.strftime("%Y-%m-%d")
        #fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        print("fecha")
        print(fecha_str)
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido"}), 400

    reservas_df = pd.read_csv("data/reservas.csv", sep=";")
    print(reservas_df.dtypes)
    reservas_df["fecha"] = reservas_df["fecha"].astype(str)
    reservas_df["hora"] = reservas_df["hora"].astype(str).str[:5]  # dejar sólo HH:MM
    # Asegurarse de que la columna 'fecha' sea de tipo datetime.date
    #reservas_df["fecha"] = pd.to_datetime(reservas_df["fecha"], dayfirst=True, errors="coerce").dt.date

    reservas_df["hora"] = pd.to_datetime(reservas_df["hora"], format="%H:%M", errors="coerce").dt.strftime("%H:%M")
    

    #print("reservas_df[fecha]=", reservas_df["fecha"])
    #print("reservas_df[hora]=", reservas_df["hora"])

    reservas_filtradas = reservas_df[reservas_df["fecha"] == fecha_str][["id_clinica", "fecha", "hora", "medico_que_atendio"]]
    
    print("reservas_filtradas=")
    print(reservas_filtradas)

    reservas_dict = reservas_filtradas.to_dict(orient="records")
    return jsonify({"reservas": reservas_dict})

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

@app.route("/api/clinicas_cercanas")
def clinicas_cercanas():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))

        df = clinicas_df.copy()
        df = df.merge(
            dpa_df[["id_dpa", "Nombre_Comuna"]],
            left_on="dpa",
            right_on="id_dpa",
            how="left"
        )

        # Asegurarse de que las columnas latitud y longitud son numéricas
        # Reemplazar ',' por '.' antes de convertir a float
        df["latitud"] = pd.to_numeric(df["latitud"].str.replace(",", "."), errors="coerce")
        df["longitud"] = pd.to_numeric(df["longitud"].str.replace(",", "."), errors="coerce")
        print("df clinicas lat y long:")
        print(df[["nombre", "latitud", "longitud", "Nombre_Comuna"]])
        # Eliminar filas con coordenadas inválidas
        df = df.dropna(subset=["latitud", "longitud"])   

        df["distancia"] = df.apply(lambda row: calcular_distancia(lat, lon, row["latitud"], row["longitud"]), axis=1)
        print("Distancias calculadas:")
        print(df[["nombre", "latitud", "longitud", "distancia"]].sort_values("distancia").head(5))

        df_ordenado = df.sort_values(by="distancia")

        resultado = df_ordenado[[
            "id_clinica", "nombre", "direccion", "dpa", "latitud", "longitud", "Nombre_Comuna", "calificacion", "n_calificaciones", "distancia"
        ]].to_dict(orient="records")

        return jsonify(resultado)
    except Exception as e:
        print("Error en /api/clinicas_cercanas:", e)
        return jsonify({"error": "Parámetros inválidos o error interno"}), 400


# Guardar datos que provienen de JS en la sesión de python
@app.route('/guardar_datos', methods=['POST'])
def guardar_datos():
    data = request.json

    print(f"Comuna geolocalizada: {data.get('comuna')}")
    session['comuna'] = data.get('comuna')
    if data.get('comuna') is not None:
        print(f"Sesión comuna geolocalizada: {session['comuna']}")
    session['id_clientes_mascotas'] = data.get('id_clientes_mascotas')

    #session['id_clinica'] = data.get('id_clinica')
    #si id_clinica está vacia, entonces le asignamos el valor de id_clinica de la url
    #if not session['id_clinica']:
    #    session['id_clinica'] = request.args.get('id_clinica')
    id_clinica = session.get('id_clinica')
    session['fechaSeleccionada'] = data.get('fechaSeleccionada')
    session['horaSeleccionada'] = data.get('horaSeleccionada')
    #session['mascotaSeleccionada'] = data.get('mascotaSeleccionada')
    #if existe id_clinica, entonces, buscamos el nombre de la clinica en la tabla data/clinicas y lo guardamos en la variabla nombre_clinica
    #print("id_clinica: ", id_clinica)
    if id_clinica is not None:
        df = pd.read_csv("data/clinicas.csv", delimiter=";")   
        filtered_df = df[df['id_clinica'] == int(id_clinica)]
        print(f"Valor de id_clinica en guardar_datos es: {id_clinica}")
        if not filtered_df.empty:
            print("filtro no vacío")
            session['nombre_clinica'] = filtered_df.iloc[0]['nombre']
        else:
            print("filtro vacío")
            session['nombre_clinica'] = None

    # Fin Guardar los datos en la sesión
    #retornamos el nombre de la clínica
    nombre_clinica = session.get('nombre_clinica')
    print(f"Valor de nombre_clinica en guardar_datos es: {nombre_clinica}")
    if nombre_clinica:
        return jsonify({'nombre_clinica': nombre_clinica}), 200
    else:
        return jsonify({'Datos guardados en la sesión'}), 200



@app.route("/guardar_variable_sesion", methods=["POST"])
def guardar_variable_sesion():
    data = request.json  # esperamos un JSON como { id: "mis_mascotas", valor: "2" }
    session[data['id']] = data['valor']
    print(f"Guardando variable de sesión, {data['id']} con valor {data['valor']}")
    print(f"session[data['id']]= {session[data['id']]}")
    return jsonify({"status": "ok", "mensaje": f"Guardado {data['id']} = {data['valor']}"})

def generate_nonce(length=16):
    """Genera un valor único para el nonce."""
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8')

# ✅ Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # Guarda la ruta actual completa, incluyendo parámetros
            session['next'] = request.full_path
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# 📌 Ruta de inicio de sesión con Google
@app.route("/login")
def login():
    # si request.full_path contiene agendar
    # entonces guardamos la ruta completa en la sesión
    # y redirigimos a la ruta de login
    #session.clear()
    #session['next'] = request.full_path
    tipo = request.args.get("tipo", "usuario")
    session['tipo_usuario'] = tipo
    print(f"[INFO] Tipo de usuario en el login: {tipo}")
    print(f"[INFO LOGIN] next: {request.full_path}")
    #verificamos si request.full_path contiene agendar
    #si request.full_path contiene agendar, entonces guardamos la ruta completa en la sesión
    redireccion = request.args.get('redirect')
    print(f"[INFO redireccionxx] next: {redireccion}")
    #if request.full_path.startswith("/agendar"):
    if redireccion in ["agendar", "finalizar_pago", "pawcarepro"]:
        session['next'] = f"/{redireccion}"

    if redireccion == None:
        print(f"[INFO redireccion] a la misma página desde donde fue invocado")
        session['next'] = "/"
    
    nonce = generate_nonce()
    session['nonce'] = nonce
    state = generate_token()  # Genera un token seguro
    session['oauth_state'] = state  # Guárdalo en la sesión
    print(f"[INFO] LOGIN oauth_state: {state}")
    
    
    fecha = request.args.get('fecha')
    hora = request.args.get('hora')
    id_veterinario = request.args.get('id_veterinario')
    
    # Guardar los parámetros en la sesión
    session['fecha'] = fecha
    session['hora'] = hora
    session['id_veterinario'] = id_veterinario

    session['fechaSeleccionada'] =fecha
    session['horaSeleccionada'] = hora
    id_clinica = request.args.get('id_clinica')
    if not id_clinica:
        id_clinica = session.get('id_clinica')
    else:
        session['id_clinica'] = id_clinica
    redirect_uri = url_for('callback', _external=True)
    return google.authorize_redirect(redirect_uri, state=state, nonce=nonce)


# 📌 Ruta de | (Google redirige aquí después de autenticación)
@app.route("/login/callback")
def callback():
    # Revisa que el state recibido sea igual al almacenado
    #stored_state = session.pop("oauth_state", None)
    stored_state = session.pop("oauth_state")
    print(f"[INFO] stored_state: {stored_state}")
    received_state = request.args.get("state")
    print(f"[INFO] received_state: {received_state}")

    if stored_state != received_state:
        return "Error: CSRF state no coincide", 400

    token = google.authorize_access_token()
    session['credentials'] = token 
    nonce = session.pop("nonce", None)

    if nonce is None:
        return "Error: Nonce missing", 400

    user_info = google.parse_id_token(token, nonce=nonce)
    if not user_info:
        return "Error: No se pudo obtener la información del usuario", 400

    session["user"] = user_info
    #guardamos en una variable de sesion llamada correo_cliente el correo del usuario
    session["correo_cliente"] = user_info.get("email")
    print(f"[INFO] Correo del usuario: {session['correo_cliente']}")

    
    # Recupera la ruta original (relativa) desde el decorador
    next_path = session.get("next", None)
    print(f"Ruta de redirección en el callback es: {next_path}")

    if next_path == "/agendar":
        return redirect(url_for("agendar"))
    elif next_path == "/":
        #return redirect(url_for("finalizar_pago"))  # usará GET y cargará los datos desde sesión
        return redirect("/finalizar_pago") 
    elif next_path == "/pawcarepro":
        #return redirect(url_for("finalizar_pago"))  # usará GET y cargará los datos desde sesión
        usuarios_df = pd.read_csv("data/usuarios.csv", delimiter=";")   
        
        usuarios_filtrado = usuarios_df[usuarios_df['correo_cliente'] == user_info.get("email")]
        if not usuarios_filtrado.empty:
            tipo_usuarios = pd.read_csv("data/tipo_usuarios.csv", delimiter=";")   
            print("usuarios_filtrado")
            print(usuarios_filtrado)
            tipo_usuarios_filtrado = tipo_usuarios[tipo_usuarios['id_tipo'] == int(usuarios_filtrado['id_tipo_usuario'].values[0])]
            if (not tipo_usuarios_filtrado.empty):
                session['id_tipo_usuario']=int(usuarios_filtrado['id_tipo_usuario'].values[0])
                session['tipo_usuario'] = tipo_usuarios_filtrado['tipo_usuario'].values[0]
                return redirect("/pawcarepro")     

    return redirect("/")

    # Si no existe next_path, redirige home
    if not next_path:
        # Alternativamente, puedes pasar un parámetro a /login?tipo=profesional (más limpio)
        tipo_usuario = session.pop("tipo_usuario", "usuario")
        #return redirect(url_for("/"))
        # Redirigir según selección
        print(f"[INFO] Tipo de usuario: {tipo_usuario}")
        if tipo_usuario == "profesional":
            return redirect(url_for("pawcarepro"))
        else:
            return redirect(url_for("index"))
        #return redirect(url_for("index"))

    # Si empieza con /agendar, redirige con url_for para asegurar parámetros
    parsed = urlparse(next_path)
#si parsed.path contiene /agendar, entonces redirigimos a la ruta de agendar
#muestrame ese código
    #parsed.path contiene /agendar y parsed.query contiene los parámetros id_clinica, fecha, hora y id_veterinario

    #y le pasamos los parámetros id_clinica, fecha, hora y id_veterinario


    #if parsed.path.startswith("/agendar"):
    if next_path and "redirect=agendar" in next_path:
        print("[INFO] Redirigiendo a agendar")
        params = parse_qs(parsed.query)
        return redirect(url_for(
            "agendar",
            #id_clinica es igual al valor de la variable de sesion id_clinica
            id_clinica=session.get("id_clinica"),
            #id_clinica=params.get("id_clinica", [None])[0],
            fecha=params.get("fecha", [None])[0],
            hora=params.get("hora", [None])[0],
            #id_veterinario=params.get("id_veterinario", [None])[0]
            id_veterinario=session.get("id_veterinario")
        ))
    elif next_path == "/finalizar_pago":
        print("[INFO] Redirigiendo a finalizar_pago")
        return redirect(url_for("finalizar_pago"))

    # Redirige a la ruta original completa con sus parámetros
    return redirect(next_path + ("?" + parsed.query if parsed.query else ""))


# 📌 Ruta de Dashboard (Solo accesible si está autenticado)
@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("index"), user=user)
    
    return f"Bienvenido {user['name']} ({user['email']})"

# 📌 Ruta de agendar
@app.route("/agendar")
def agendar():

    #session.clear()
    status_code = None
    id_clinica = request.args.get('id_clinica')
    if not id_clinica:
        id_clinica = session.get('id_clinica')
    else:
        session['id_clinica'] = id_clinica

    session['next'] = request.full_path
    print(f"[INFO] next Agendar: {request.full_path}")
    user = session.get("user", None)

    print(session.get("user"))
    if not user:
        return redirect(url_for("login"))    
    
    parametros = request.query_string.decode('utf-8')
    print(f"Parámetros de la URL: {parametros}")
    #si ac, c y r existenen la parametros, entonces ejecutamos confirmar_cita y retornamos a la web mis_citas
    #si no existen, entonces retornamos a la web agendar
    ac=request.args.get('ac') or None
    confirma=request.args.get('c') or None
    id_cita=request.args.get('r') or None

    if ac and confirma and id_cita:
        print("confirmar_cita")
        confirmar_cita(id_cita, confirma)
        #return redirect(url_for("mis_citas?c=1"))
        confirmada = 'True'
        precio = request.form.get('inputPrecio')
        #almacenamos precio en una variable de sesion
        session['precio'] = precio

        #del archivo reservas.csv, obtenemos el valor de la columna precio, para id_reserva=id_cita
        df_reservas = pd.read_csv("data/reservas.csv", sep=";")
        df_reservas = df_reservas[(df_reservas["id_clinica"] == int(id_clinica))]
        precio = df_reservas["precio"].values[0]


        #ejecutamos pagar y le pasamos como parametros id_cita, la variable de sesion de autenticación de google y el monto
        #pagar(id_cita, session['user'], precio)
        
        return render_template('mis_citas.html', confirmada = confirmada)

    #else:
    #    return redirect(url_for("agendar", id_clinica=id_clinica))



    print(f"Parámetros de la URL: {request.args}")
    # Verificar si el usuario está autenticado
    user_info = session.get('user')
    print(f"Información del usuario: {user_info}")
    user = session.get("user") 
    if user:
        print(f"correo del usuario: {user['email']}")

    id_veterinario = request.args.get('id_veterinario')
    if not id_veterinario:
        id_veterinario = session.get('id_veterinario')
    else:
        session['id_veterinario'] = id_veterinario

    #print(user_info)
    if user_info and parametros:
        # Recuperar los parámetros de la URL
        #id_clinica = request.args.get('id_clinica')
        id_clientes_mascotas=request.args.get('id_clientes_mascotas')
        #fecha = request.args.get('fecha')
        #hora = request.args.get('hora')
        #id_clinica = session.get('id_clinica')
        if id_clientes_mascotas:
            session['id_clientes_mascotas'] = id_clientes_mascotas
        fecha =session.get('fecha')
        hora = session.get('hora')  
        #si no existe la variable de sesion id_veterinario, entonces la creamos


        #if id_veterinario:
        #    session['id_veterinario'] = id_veterinario

        #print(id_clinica, fecha, hora,id_veterinario)
        # Verificar si los parámetros existen
        print("los parametros son clinica=",id_clinica, ", fecha=", fecha, " hora=", hora, " vet=", id_veterinario)
        if id_clinica and user_info['email'] and id_clientes_mascotas and fecha and hora:
            # Insertar la nueva reserva en el archivo CSV
            print("Insertar la nueva reserva en el archivo CSV")
            response, status_code = insert_reservation()
            if (status_code==200):
                print("Reserva creada")
                #return pagar()
                return render_template("agendar.html?ac=1")
            else:   
                print("Reserva no creada")
                return render_template("agendar.html?ac=99")      
              
    #preparamos el df_reservas y df_staff para la vista de agendar
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas["hora"] = df_reservas["hora"].apply(lambda h: f"{int(h.split(':')[0]):02d}:00")
    #pasamos fecha a formato dd/mm/aaaa
    #si fecha no existe o es vacia entonces la creamos con la fecha de hoy
    # Paso 1: Obtener la fecha desde los argumentos o sesión
    fecha_str = request.args.get("fecha") or session.get("fecha")

    # Si no se proporciona, usamos la fecha actual
    if not fecha_str:
        fecha = datetime.now()
        fecha_str = fecha.strftime("%d-%m-%Y")
    else:
        # Convertir el string a datetime (independientemente de cómo venga)
        try:
            fecha = datetime.strptime(fecha_str, "%d-%m-%Y")
        except ValueError:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            except ValueError:
                fecha = datetime.now()
        fecha_str = fecha.strftime("%d-%m-%Y")
    
    #si fecha es un string, entonces la convertimos a formato datetime
    #fecha = pd.to_datetime(fecha, format="%d/%m/%Y")

    #fecha = pd.to_datetime(fecha, format="%d-%m-%Y")
    # Paso 2: Convertimos la columna "fecha" a datetime (con múltiples formatos posibles)
    df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], format='mixed', dayfirst=True, errors='coerce')

    # Paso 3: Filtrar por fechas desde "fecha"
    df_reservas_filtrado = df_reservas[df_reservas["fecha"] >= fecha]

    df_reservas = df_reservas[(df_reservas["id_clinica"] == int(id_clinica))]
    print(f"df_staff: {df_reservas}")
    
    df_staff = pd.read_csv("data/staff_clinica.csv", sep=";")
    df_staff = df_staff[df_staff["id_clinica"] == int(id_clinica)]
    df_especialidades = pd.read_csv("data/especialidades.csv", sep=";")
    df_especialidades["id_especialidad"] = df_especialidades["id_especialidad"].astype(int)
    mapa_especialidades = dict(zip(
        df_especialidades["id_especialidad"],
        df_especialidades["especialidad"]
    ))
    # Paso 3: Traducir especialidades de cada veterinario
    def traducir_especialidades(cadena_ids):
        try:
            return [
                mapa_especialidades[int(i)]
                for i in str(cadena_ids).split(",")
                if i.isdigit() and int(i) != 0 and int(i) in mapa_especialidades
            ]
        except Exception as e:
            print(f"Error con la cadena: {cadena_ids} → {e}")
            return []

    df_staff["especialidades"] = df_staff["especialidades"].apply(traducir_especialidades)
    
    df_staff_all = pd.read_csv("data/staff.csv", sep=";")
    #en cada fila de df_staff_all, eliminamos los valores 0 de la columna especialidades
    

    print(f"df_staff: {df_staff}")

    df_staff = df_staff.merge(
        df_staff_all,
        left_on="id_veterinario",
        right_on="id_veterinario",
        how="left"
    )


    df_reservas = df_reservas.to_dict(orient="records")
    #df_staff = df_staff.to_dict(orient="records")
    #primero debo ver si status_code existe y esta definida
    #si no existe, entonces la reserva no fue creada

    #filtramos las mascotas del usuario donde el correo_cliente sea igual al correo del usuario
    df_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    email = user.get("email")
    df_mascotas = df_mascotas[df_mascotas["correo_cliente"] == email]
    #pasamos df_mascotas a formato JSON
    df_mascotas_json = df_mascotas.to_dict(orient="records")
    print(f"df_mascotas: {df_mascotas}")
    return render_template("agendar.html",
        df_staff=df_staff,
        df_staff_json=df_staff.to_dict(orient="records"),  # 🔹 aquí va el JSON
        df_reservas=df_reservas,
        mascotas=df_mascotas_json,
        user=user,
        status_code=status_code
                           )

    

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    id_token = token.get('id_token')
    claims = jwt.decode(id_token, options={"verify_signature": False})
    user = session.get("user")
    if claims['nonce'] != session['nonce']:
        return 'Error: Nonce no coincide'
    # Procesar el token y la sesión del usuario
    return redirect(url_for('mis_mascotas', user=user))


@app.route('/mis_mascotas')
def mis_mascotas():
    session['next'] = request.full_path
    print(f"[INFO] next mis_mascotas: {request.full_path}")
    user = session.get("user", None)

    print(session.get("user"))
    if not user:
        return redirect(url_for("login"))    
    email=user.get("email")
    df_mis_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    df_mis_mascotas = df_mis_mascotas[(df_mis_mascotas["correo_cliente"] == email)]

    if not df_mis_mascotas.empty:
        df_mis_mascotas["anos_edad"], df_mis_mascotas["meses_edad"] = zip(
            *df_mis_mascotas["fecha_nacimiento"].apply(calcular_edad)
        )
    else:
        df_mis_mascotas["anos_edad"] = []
        df_mis_mascotas["meses_edad"] = []

    #df_mis_mascotas["meses_edad"] = edad_meses

    # Leer clinicas.csv y unir por id_clinica
    df_especie_raza = pd.read_csv("data/especie_raza.csv", sep=";")
    df_mis_mascotas = df_mis_mascotas.merge(df_especie_raza[["id_especie_raza", "id_especie", "id_raza"]], on="id_especie_raza", how="left")

    df_razas= pd.read_csv("data/razas.csv", sep=";")
    df_mis_mascotas = df_mis_mascotas.merge(df_razas[["id_raza", "nombre_raza"]], on="id_raza", how="left")

    df_especies= pd.read_csv("data/especies.csv", sep=";")
    df_mis_mascotas = df_mis_mascotas.merge(df_especies[["id_especie", "especie"]], on="id_especie", how="left")


    # Convertir columna fecha a datetime
    df_mis_mascotas["fecha_nacimiento"] = pd.to_datetime(df_mis_mascotas["fecha_nacimiento"], format='mixed', dayfirst=True)

    #print(df_mis_mascotas)
    # Convertir dataframe a lista de diccionarios
    mis_mascotas = df_mis_mascotas.to_dict(orient="records")

    #######
    ## Código para crear citas para la página mis_macotas
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas = df_reservas[(df_reservas["correo_cliente"] == email) & (df_reservas["estado"] == 1)]
    
    # Leer clinicas.csv y unir por id_clinica
    df_clinicas = pd.read_csv("data/clinicas.csv", sep=";")
    df_reservas = df_reservas.merge(df_clinicas[["id_clinica", "nombre", "direccion", "dpa"]], 
                                    on="id_clinica", how="left")

    # Leer clientes_mascotas.csv y unir por correo_cliente y mascota = id_clientes_mascotas
    df_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    #print(df_mascotas)
    df_mascotas = df_mascotas[df_mascotas["correo_cliente"] == email]
    #print(df_mascotas)
    df_reservas = df_reservas.merge(
        df_mascotas[["id_clientes_mascotas", "nombre_mascota"]],
        left_on="mascota",
        right_on="id_clientes_mascotas",
        how="left"
    )

    # Leer dpa.csv y unir por dpa para obtener Nombre_Comuna
    df_dpa = pd.read_csv("data/dpa.csv", sep=";")
    df_reservas = df_reservas.merge(
        df_dpa[["id_dpa", "Nombre_Comuna"]],
        left_on="dpa",
        right_on="id_dpa",
        how="left"
    )
    # modificamos el campo medico_que_atendio a entero sin decimales
    df_reservas["medico_que_atendio"] = df_reservas["medico_que_atendio"].astype(int)


    df_staff = pd.read_csv("data/staff.csv", sep=";")
    df_reservas = df_reservas.merge(
        df_staff[["id_veterinario", "nombres", "apellidos"]],
        left_on="medico_que_atendio",
        right_on="id_veterinario",
        how="left"
    )
    # Convertir columna fecha a datetime
    #df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], format="%d-%m-%Y")
    df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], format='mixed', dayfirst=True)

    #ahora filtramos df_reservas para que solo contenga las reservas con fecha mayor o igual a hoy
    #hoy = datetime.now().strftime("%d-%m-%Y")
    # 2. Obtener fecha actual como datetime
    hoy = pd.to_datetime(datetime.now().date())
    #ordenamos desde la fecha más actual a la mas vieja
    df_reservas = df_reservas.sort_values(by=["fecha"], ascending=False)

    # 4. Filtrar por fecha
    df_reservas_futuras = df_reservas[df_reservas["fecha"] >= hoy].copy()
    df_reservas_pasadas = df_reservas[df_reservas["fecha"] < hoy].copy()
    # 5. Convertir fecha a string solo para mostrar/exportar
    df_reservas_futuras["fecha"] = df_reservas_futuras["fecha"].dt.strftime("%d-%m-%Y")
    df_reservas_pasadas["fecha"] = df_reservas_pasadas["fecha"].dt.strftime("%d-%m-%Y")
    #df_reservas["fecha"] = df_reservas["fecha"].dt.strftime("%d-%m-%Y")
    #df_reservas_pasadas=df_reservas
    #df_reservas = df_reservas[(df_reservas["fecha"] >= hoy)]
    #df_reservas_pasadas = df_reservas_pasadas[(df_reservas_pasadas["fecha"] < hoy)]
    #eliminamos los 00:00:00 del campo fecha
    #df_reservas["fecha"] = df_reservas["fecha"].dt.strftime("%d-%m-%Y")
    print("df_reservas próximas: ")
    print(df_reservas_futuras)
    print("df_reservas pasadas: ")
    print(df_reservas_pasadas)
    print("hoy=", hoy)
    
    #df_reservas_pasadas["fecha"] = df_reservas_pasadas["fecha"].dt.strftime("%d-%m-%Y")
    #eliminamos los segundos a los campos hora
    df_reservas_futuras["hora"] = df_reservas_futuras["hora"].str[:5]
    df_reservas_pasadas["hora"] = df_reservas_pasadas["hora"].str[:5]

    # Convertir dataframe a lista de diccionarios

    mis_citas = df_reservas_futuras.to_dict(orient="records")
    mis_citas_pasadas = df_reservas_pasadas.to_dict(orient="records")
    #print(df_reservas)

   # PAGINACIÓN
    page = request.args.get("page", default=1, type=int)
    per_page = 6
    start = (page - 1) * per_page
    end = start + per_page
    citas_paginadas = mis_citas_pasadas[start:end]
    total_paginas = (len(mis_citas_pasadas) + per_page - 1) // per_page


    return render_template("mis_mascotas.html", 
                            user=user, 
                            mis_mascotas=mis_mascotas, 
                            mis_citas=mis_citas, 
                            #mis_citas_pasadas=mis_citas_pasadas,
                            mis_citas_pasadas=citas_paginadas,
                            page=page,
                            total_paginas=total_paginas
                        )







def calcular_edad(fecha_nacimiento):

#hay que pasar fecha_nacimiento al mismo foromato de datetime.now()
    fecha_nacimiento = pd.to_datetime(fecha_nacimiento, format='mixed', dayfirst=True)
    # Obtener la fecha actual
    fecha_actual = datetime.now()

     # Calcular la diferencia en años y meses
    edad_anos = fecha_actual.year - fecha_nacimiento.year
    edad_meses = fecha_actual.month - fecha_nacimiento.month

    # Ajustar los años y meses si es necesario
    if edad_meses < 0:
        edad_anos -= 1
        edad_meses += 12

    return edad_anos, edad_meses
#
#



@app.route("/api/clinicas", methods=["GET"])
def obtener_clinicas():
    print("🚀 Iniciando la búsqueda de clínicas...")
    try:
        #imprimir en la consola todos los parámetros y valores de la url
        print("leyendo df clinicas")
        # 🔥 Cargar el CSV
        df = pd.read_csv("data/clinicas.csv", sep=";")
        df_dpa = pd.read_csv("data/dpa.csv", sep=";")
        df = df.merge(
            df_dpa[["id_dpa", "Nombre_Comuna"]],
            left_on="dpa",
            right_on="id_dpa",
            how="left"
        )
        
        # Verificar si hay un valor de búsqueda en la sesión
        busqueda = request.args.get("search", "").strip()
        session["busqueda"] = busqueda
        print(f"[INFO] Valor de búsqueda: '{busqueda}'")

        #vemos si en la url está el argumento comuna y si es distinto de vacio, 
        # entonces le asignamos a la variable comuna su valor
        if "comuna" in request.args and request.args.get("comuna") != "":
            session["comuna"] = request.args.get("comuna").strip()
            comuna= session["comuna"]
        else:
            comuna=session.get("comuna", None)  # Obtener el valor de la comuna de la sesión, si no existe, será None

        

        #imprimo el valor de busqueda y comuna
        print(f"Valor de busqueda: {busqueda}")

        print(f"Valor de comuna busqueda: {comuna}")
        
        # Filtrar por search si se proporciona
        if busqueda:
            print(f"BUSCANDO DENTRO DEL IF POR {busqueda}")
            df_nombre = df[df["nombre"].str.contains(busqueda, case=False, na=False)]
            #si df es vacio, entonces buscamos por el campo especialidades
            if df_nombre.empty:
                clinicas_especialidades = pd.read_csv("data/clinicas_especialidades.csv", sep=";")
                especialidades = pd.read_csv("data/especialidades.csv", sep=";")
                staff = pd.read_csv("data/staff.csv", sep=";")
                staff["nombre_completo"] = staff["nombres"].str.strip() + " " + staff["apellidos"].str.strip()
                staff_clinica = pd.read_csv("data/staff_clinica.csv", sep=";")


                # Unir las tablas para obtener especialidades
                clinicas_especialidades = clinicas_especialidades.merge(
                    especialidades[["id_especialidad", "especialidad"]],
                    left_on="id_especialidad",
                    right_on="id_especialidad",
                    how="left"
                )

                # a clinicas_especialidades le agregamos todos los campos de df donde id_clinica =O id_clinica
                clinicas_especialidades = clinicas_especialidades.merge(
                    df[["id_clinica", "nombre", "direccion", "dpa","calificacion", "estado", "n_calificaciones", "latitud", "longitud" ]],
                    left_on="id_clinica",
                    right_on="id_clinica",
                    how="left"
                )
                staff_clinica= staff_clinica.merge(
                staff[["id_veterinario", "nombre_completo"]],
                left_on="id_veterinario",
                right_on="id_veterinario",
                how="left"
                )
                           

                print(f"buscando dentro del if por {busqueda} en especialidades")
                #filtramos clinicas_especialidades por el campo especialidad = busqueda
                clinicas_especialidades_original = clinicas_especialidades
                clinicas_especialidades = clinicas_especialidades[clinicas_especialidades["especialidad"].str.contains(busqueda, case=False, na=False)]
                clinicas_especialidades["tipo"]= "especialidades"
                print("staff_clinica en buscar por especialildad")
                print(staff_clinica)
                print("clinicas_especialidades")
                print(clinicas_especialidades)
                # Filtrar: subset de staff_clinica con solo las clínicas presentes en clinicas_especialidades
                staff_filtrado = staff_clinica[staff_clinica["id_clinica"].isin(clinicas_especialidades["id_clinica"])]
                print("staff_filtrado")
                print(staff_filtrado)
                staff_json = staff_filtrado.to_dict(orient="records")
                if clinicas_especialidades.empty:
                    clinicas_especialidades = clinicas_especialidades_original
                    print("clinicas_especialidades:")
                    print(clinicas_especialidades)                     

                    staff_clinica = staff_clinica[staff_clinica["nombre_completo"] == busqueda]
                   
                    print(type(staff_clinica))
                    print(staff_clinica)
                    # 1. Asegurar que ambos campos sean del mismo tipo (int)
                    clinicas_especialidades["id_clinica"] = clinicas_especialidades["id_clinica"].astype(int)
                    staff_clinica["id_clinica"] = staff_clinica["id_clinica"].astype(int)
                    staff_json = staff_clinica.to_dict(orient="records")
                    # 2. Filtrar clinicas_especialidades según los ID presentes en clinicas
                    clinicas_especialidades = clinicas_especialidades[
                        clinicas_especialidades["id_clinica"].isin(staff_clinica["id_clinica"])
                    ]
                    clinicas_especialidades = clinicas_especialidades.drop_duplicates(subset="id_clinica", keep="first")
                    clinicas_especialidades["tipo"]= "veterinario"
                    print("filtrado")
                    print(clinicas_especialidades)

                clinicas_json = clinicas_especialidades.to_dict(orient="records")
                print("clinicas_json")
                print(clinicas_json)
                #if staff_clinica:
                #    staff_json = staff_clinica.to_dict(orient="records")


                return jsonify({"clinicas": clinicas_json, "staff_json": staff_json})                
            else:
                df = df_nombre
            # si no har search, entonces buscamos por comuna
        elif comuna:
            print("buscando por comuna", comuna)
            #imprimimos el tipo de dato de comuna
            print(f"Tipo de dato de comuna: {type(comuna)}")
            #pasamos la columna dpa a string
            df["dpa"] = df["dpa"].astype(str)
            #filtramos df por dpa=comuna
            df = df[df["dpa"] == comuna]
            clinicas_json = df.to_dict(orient="records")
            return jsonify({"clinicas": clinicas_json})


            #df["dpa"] = df["dpa"].astype(str)
            #df = df[df["dpa"].str.contains(comuna, case=False, na=False)]
        # 🔍 Convertir a JSON y devolver
        
        #si df es vacio, vemos si clinicas_especialidades es vacio
        if df.empty:
            if clinicas_especialidades.empty:
                print("❌ No se encontraron clínicas ni especialidades")
                return jsonify({"error": "No se encontraron clínicas"}), 404
            else:
                print("✅ Se encontraron clínicas por especialidades")
                print(clinicas_especialidades)
                clinicas_json = clinicas_especialidades.to_dict(orient="records")
        else:
            print("✅ Se encontraron clínicas por nombre")
            print(df)
            clinicas_json = df.to_dict(orient="records")

        return jsonify({"clinicas": clinicas_json})

    except Exception as e:
        print(f"❌ Error al obtener clínicas: {str(e)}")
        return jsonify({"error": str(e)}), 500




@app.route("/sugerencias", methods=["GET"])
def obtener_sugerencias():
    query = request.args.get("q", "").lower()  # Obtener el texto ingresado por el usuario
    query = remover_tildes(query)  # 🔥 Eliminar tildes de la búsqueda
    comuna = request.args.get("comuna", "")  # Obtener el valor del select comunas
    resultados = []
    print("Entrando a sugerencias")
    if query:
        print(f"🔍 Buscando sugerencias para: '{query}' en la comuna '{comuna}'")  # Depuración
    else:
        print("🔍 Buscando todas las especialidades disponibles")

    if query:
        try:
            print("📂 Intentando leer el archivo: data/clinicas.csv")  # Depuración
            df = pd.read_csv("data/clinicas.csv", sep=";")  # Leer el archivo CSV

            # Filtrar por la comuna seleccionada
            df["dpa"] = df["dpa"].astype(str)
            df_filtrado = df[df["dpa"].str.contains(comuna, case=False, na=False)]
            #clinicas = df_filtrado["nombre"].dropna().unique()  # Obtener nombres únicos
            clinicas = df["nombre"].dropna().unique()  # Obtener nombres únicos

            clinicas_especialidades = pd.read_csv("data/clinicas_especialidades.csv", sep=";")  # Leer el archivo CSV
            # le agregamos la dpa a clinicas_especialidades desde el df_filtrado
            clinicas_especialidades = clinicas_especialidades.merge(
                df_filtrado[["id_clinica", "dpa"]],
                on="id_clinica",
                how="left"
            )
            especialidades = pd.read_csv("data/especialidades.csv", sep=";")
            # Filtrar por la comuna seleccionada en clinicas_especialidades
            clinicas_especialidades = clinicas_especialidades[clinicas_especialidades["dpa"].str.contains(comuna, case=False, na=False)]
            #le agregamos la columna especialidad a clinicas_especialidades del especialidades
            clinicas_especialidades = clinicas_especialidades.merge(
                especialidades[["id_especialidad", "especialidad"]],
                left_on="id_especialidad",
                right_on="id_especialidad",
                how="left"
            )
            clinicas_especialidades = clinicas_especialidades["especialidad"].dropna().unique()  # Obtener nombres únicos
            print(f"clinicas_especialidades:")
            print(f"{clinicas_especialidades}")
            
            staff = pd.read_csv("data/staff.csv", sep=";")  # Leer el archivo CSV
            staff_clinicas = pd.read_csv("data/staff_clinica.csv", sep=";")  # Leer el archivo CSV
            print("staff:")
            print(staff)   
            print("staff_clinicas:")
            print(staff_clinicas)         
            staff_clinicas= staff_clinicas.merge(
                staff[["id_veterinario","nombres", "apellidos"]],
                left_on="id_veterinario",
                right_on="id_veterinario",
                how="left"
            )

            staff_clinicas["nombre_completo"] = staff_clinicas["nombres"].str.strip() + " " + staff_clinicas["apellidos"].str.strip()
            staff_clinicas = staff_clinicas[["id_clinica", "nombre_completo"]]

            
            print("Staff_clinicas merge")
            print(staff_clinicas)

            # Filtrar sugerencias que contengan el texto ingresado
            
            resultados_nombre = [c for c in clinicas if query in remover_tildes(c.lower())]
            if resultados_nombre:
                print("Se encontraron resultados en resultados_nombre")
                resultados_nombre.insert(0, "clinica")
            print(type(resultados_nombre))
            print("resultados_nombre")
            print(resultados_nombre)
            resultados_especialidades = [e for e in clinicas_especialidades if query in remover_tildes(e.lower())]
            if resultados_especialidades:
                print("Se encontraron resultados en resultados_especialidades")
                resultados_especialidades.insert(0, "especialidades")
            print("resultados_especialidades")
            print(resultados_especialidades)
            resultados_staff = [f for f in staff_clinicas["nombre_completo"] if query in remover_tildes(f.lower())]
            if resultados_staff:
                print("Se encontraron resultados en staff_clinicas")
                resultados_staff.insert(0, "veterinario")
            print("resultados_staff")
            print(resultados_staff)
            # Combinar resultados de nombres y especialidades
            resultados = list(set(resultados_nombre + resultados_especialidades + resultados_staff))

            # Filtrar sugerencias que contengan el texto ingresado
                          
        except Exception as e:
            print(f"❌ ERROR al leer el CSV: {str(e)}")  # Mostrar error en la terminal
            return jsonify({"error": f"Error al leer el CSV: {str(e)}"}), 500
    else:
        especialidades = pd.read_csv("data/especialidades.csv", sep=";")
        especialidades = especialidades["especialidad"].dropna().unique()  # Obtener nombres únicos
        especialidades = np.sort(especialidades)  # Ordenar alfabéticamente
        #with especialidades as f:
        #    reader = csv.DictReader(f)
        #    especialidades = sorted(set(row["especialidad"] for row in reader if row["especialidad"].strip()))
        resultados = list(especialidades)  # Solo muestra 10 por omisión
        print("resultados")
        print(resultados)

    return jsonify(resultados)  # Devolver sugerencias en formato JSON

def remover_tildes(texto):
    """Elimina las tildes de un texto"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn'
    )

@app.route("/cerrar_sesion")
def cerrar_sesion():
    session.clear()
    return redirect(url_for("index"))


@app.route("/api/reservas", methods=["GET"])
def obtener_reservas():
    try:
        #reservas = []
        #with open('data/reservas.csv', newline='', encoding='utf-8') as csvfile:
        #    reader = csv.DictReader(csvfile, delimiter=';')
        #    for row in reader:
        #        reservas.append(row)
        print(f"Abrir el archivo de reservas")  # Depuración
        df_reservas = pd.read_csv("data/reservas.csv", sep=";")
        
        # Convertir NaN en None para que jsonify no falle
        df_reservas = df_reservas.where(pd.notnull(df_reservas), None)
        df_reservas = df_reservas.replace({np.nan: None})
        reservas = df_reservas.to_dict(orient="records")
        return jsonify(reservas)
        #reservas = pd.read_csv('data/reservas.csv', parse_dates=['fecha'], dayfirst=True)
        #with open('data/reservas.csv', newline='', encoding='utf-8') as f:
        #    reader = csv.DictReader(f, delimiter=';')
        #    reservas = list(reader)
        #    for r in reservas:
        #        r['fecha'] = datetime.strptime(r['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y')  # aseguras formato

        print(f"Reservas: {df_reservas}")  # Depuración
        # Asegúrate de que reservas es un array
        #if not isinstance(reservas, list):
        #    reservas = [reservas]
        reservas = df_reservas.to_dict(orient="records")
        return jsonify(reservas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/staff_clinica", methods=["GET"])
def staff_clinica():
    user = session.get("user", None)
    #if hay usuario obtengo su correo
    if user:
        email = user.get("email")
    print("Entré a staff_clinica")
    #obtener el valor del argumento id_clinica y fecha de la url
    #id_clinica = request.args.get("id_clinica")
    id_clinica = session.get('id_clinica')
    fecha = request.args.get("fecha")
    #imprimir estos valores 
    #en la consola
    print(f"en staff_clinica: ID Clínica: {id_clinica}, Fecha: {fecha}")
    #id_clinica = request.args.get("id_clinica")
    #fecha = request.args.get("fecha")
    #print(f"en staff_clinica: ID Clínica: {id_clinica}, Fecha: {fecha}")

    #obtenemos las reservas de la clinica y la fecha seleccionada
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas = df_reservas[(df_reservas["id_clinica"] == int(id_clinica)) & (df_reservas["fecha"] == fecha)]

    df_staff_clinica = pd.read_csv("data/staff_clinica.csv", sep=";")

    #obtenemos el staff de veterinarios de la clínica
    df_staff = pd.read_csv("data/staff.csv", sep=";")
    #hacemos un merge de df_staff_clinica con df_staff por id_veterinario y id_vet
    df_staff_clinica = df_staff_clinica.merge(df_staff[["nombres", "apellidos", "sexo", "correo", "area_interes", "estado"]], on="id_veterinario", how="inner")
    #filtramos el staff_clinica por id_clinica
    df_staff_clinica = df_staff_clinica[df_staff_clinica["id_clinica"] == int(id_clinica)]
    
    df_especialidades = pd.read_csv("data/especialidades.csv", sep=";")
    #reemplazamos los valores de la columna especialides del df_staff_clinica por el nombre de la especialidad del df_especialidades
    espec_ids = [e for e in df_staff_clinica["especialidades"].split(",") if e != "0"]
    especialidades = df_especialidades[df_especialidades["id_especialidad"].astype(str).isin(espec_ids)]["especialidad"].tolist()
    # Convertir la lista de especialidades a una cadena separada por comas
    especialidades_str = ", ".join(especialidades)
    # Reemplazar la columna especialidades en df_staff_clinica
    df_staff_clinica["especialidades"] = especialidades_str
    #imprimimos el df_staff_clinica en la consola para ver el resultado
    print(df_staff_clinica)
    #retornamos el df_staff_clinica como un json
    # Convertir el DataFrame a una lista de diccionarios
    staff_clinica = df_staff_clinica.to_dict(orient="records")
    # Devolver el resultado como JSON
    return jsonify(staff_clinica), 200

#creamos una función fetch para obtener los datos de fetch('/api/seleccion_guardada' y los almacenamos en unas variables de sesión
@app.route("/api/guardar_vet_fecha_hora", methods=["POST"])
def guardar_vet_fecha_hora():
    try:
        data = request.get_json(force=True)
        print("Datos recibidos:", data)  # TEMPORAL para debug
        id_veterinario = data.get('id_veterinario')
        fechaSeleccionada = data.get('fechaSeleccionada')
        horaSeleccionada = data.get('horaSeleccionada')

        if not all([id_veterinario, fechaSeleccionada, horaSeleccionada]):
            return {"error": "Faltan datos"}, 400

        # Guardar en sesión
        session['id_veterinario'] = id_veterinario
        session['fechaSeleccionada'] = fechaSeleccionada
        session['horaSeleccionada'] = horaSeleccionada
        session['fecha'] = fechaSeleccionada
        session['hora'] = horaSeleccionada

        return {"mensaje": "Datos guardados correctamente"}, 200

    except Exception as e:
        print("Error en /api/guardar_vet_fecha_hora:", e)
        return {"error": str(e)}, 500

    


@app.route("/api/insertar_reservas_original", methods=["GET"])
#insertar una reserva
def insert_reservation_original():
    #imprimo en la consola todas las variables de sesión y sus valores
    print("Variables de sesión:")
    for key, value in session.items():  
        print(f"{key}: {value}")    

    reserva_en_proceso= session.get('reserva_en_proceso')
    
    # recuperamos las variables de sesion fechaSeleccionada, horaSeleccionada, mascotaSeleccionada, id_clinica y correo_cliente
    id_clinica = reserva_en_proceso['id_clinica'] 
    #correo_cliente corresponde al valor de email de la variavle de sesion user
    if(session.get('user')):
        print("Usuario LOGEADO")
        correo_cliente = session.get('user')['email']
        nombre_cliente = session.get('user')['name']
    else:
        print("Usuario invitado")
        correo_cliente = session.get('correo_cliente_invitado')
        print(f"Correo del usuasrio invitado es {session.get('correo_cliente_invitado')}")
        nombre_cliente = "Usuario invitado"
    id_veterinario = reserva_en_proceso['veterinario'] 
    mascotaSeleccionada = session.get('mascotaSeleccionada')

    if (not str(mascotaSeleccionada).isdigit()): # Quiere decir que es una nueva mascota que proviene desde el proceso de agendar en finalizar_pago
        with open('data/clientes_mascotas.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            clientes_mascotas = list(reader)
        
        nombre_mascota = mascotaSeleccionada
        clientes_mascotas_df = pd.DataFrame(clientes_mascotas)
        clientes_mascotas_df['id_clientes_mascotas'] = pd.to_numeric(clientes_mascotas_df['id_clientes_mascotas'], errors='coerce')
        
        id_clientes_mascotas = int(clientes_mascotas_df['id_clientes_mascotas'].max(skipna=True) or 0)   
        id_clientes_mascotas = id_clientes_mascotas+1
        session['mascotaSeleccionada'] = id_clientes_mascotas
        
        correo_cliente = session.get('correo_cliente')
   
        fecha_nacimiento = session.get('fecha_nacimiento')
        #especie = session.get('especie')
        id_especie_raza = session.get('raza')
        new_mascota = {
            'id_clientes_mascotas': (id_clientes_mascotas),
            'correo_cliente': correo_cliente,
            'nombre_mascota': nombre_mascota,
            'fecha_nacimiento': fecha_nacimiento,
            'sexo': 0,
            #transformamos peso a decimal con un decimal
            'peso': 0,  # Aseguramos que peso sea un número
            'id_especie_raza': int(id_especie_raza)
        }
        # Append the new reservation to the CSV file
        with open('data/clientes_mascotas.csv', 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_mascota.keys(), delimiter=';')
            writer.writerow(new_mascota)        

    if((not mascotaSeleccionada)):
       print("Mascota no seleccionada ya que usuario es invitado")
       session['mascotaSeleccionada']=0
       mascotaSeleccionada=0
    
    #si mascotaseleccionada==999, entonces la insertamos en la tabla clientes_mascotas
    #y después insertamos la reserva, ya que primero debemos actualizar el valor de mascotaSeleccionada
    print("en insertar reserva mascotaSeleccionada=", mascotaSeleccionada)
    print("los parametros de nueva_mascota son", session.get('nueva_mascota'))
    #si session['crear_nueva_mascota'] no existe entonces la creamos con valor 0
    if 'crear_nueva_mascota' not in session:
        session['crear_nueva_mascota'] = 0
    print("[DEBUG] el valor de crear_nueva_mascota es: ", session['crear_nueva_mascota'])
    if session['crear_nueva_mascota'] == 1:
        with open('data/clientes_mascotas.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            clientes_mascotas = list(reader)
        
        clientes_mascotas_df = pd.DataFrame(clientes_mascotas)
        print("Columnas detectadas:", clientes_mascotas_df.columns.tolist())  # Debug
        #clientes_mascotas_df['id_clientes_mascotas'] = clientes_mascotas_df['id_clientes_mascotas'].astype(int)
        clientes_mascotas_df['id_clientes_mascotas'] = pd.to_numeric(clientes_mascotas_df['id_clientes_mascotas'], errors='coerce')

        max_id_clientes_mascotas = int(clientes_mascotas_df['id_clientes_mascotas'].max(skipna=True) or 0)

        mascotaSeleccionada= max_id_clientes_mascotas + 1
        session['mascotaSeleccionada'] = mascotaSeleccionada
        #Almacenamos max_id_reserva en una variable de seción
        session['max_id_clientes_mascotas'] = int(max_id_clientes_mascotas)
        #obtenemos el nombre de la mascota desde la variable de sesion
        
        nombre_mascota = session.get('nueva_mascota').get('nombre_mascota')
        #obtenemos la especie y raza de la mascota desde las variables de sesion
        id_especie_raza = session.get('nueva_mascota').get('raza_mascota')
        #obtenemos la fecha de nacimiento de la mascota desde la variable de sesion
        fecha_nacimiento = session.get('nueva_mascota').get('fecha_nacimiento')
        #pasamos fecha_nacimiento a formato dd/mm/aaaa sin horas
        #fecha_nacimiento = pd.to_datetime(fecha_nacimiento, format="%d-%m-%Y").strftime("%d-%m-%Y")
        #fecha_nacimiento = pd.to_datetime(fecha_nacimiento, format='mixed', dayfirst=True)
        #obtenemos el sexo
        sexo = session.get('nueva_mascota').get('sexo_mascota')
        peso= session.get('nueva_mascota').get('peso_mascota')
        new_mascota = {
            'id_reservaid_clientes_mascotas': (max_id_clientes_mascotas + 1),
            'correo_cliente': correo_cliente,
            'nombre_mascota': nombre_mascota,
            'fecha_nacimiento': fecha_nacimiento,
            'sexo': sexo,
            #transformamos peso a decimal con un decimal
            'peso': float(peso) if peso else 0.0,  # Aseguramos que peso sea un número
            'id_especie_raza': int(id_especie_raza)
        }
        # Append the new reservation to the CSV file
        with open('data/clientes_mascotas.csv', 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_mascota.keys(), delimiter=';')
            writer.writerow(new_mascota)
    
    fechaSeleccionada = reserva_en_proceso['fecha'] 

    cargoServicio = int(session.get('cargoServicio', 0))
    cargoTotal = int(session.get('cargoTotal', 0))
    precio = int(reserva_en_proceso['valor'] )
 
    print(f"Precio: {precio}")
    token = session.get('token')
    #si fechaSeleccionada está vacia, entonces le asignamos el valor de fechaSeleccionada de la url
    if not fechaSeleccionada:
        fechaSeleccionada = session.get('fecha')
    horaSeleccionada = reserva_en_proceso['hora'] 
    if not horaSeleccionada:
        horaSeleccionada = session.get('hora')    
#si el largo de horaSeleccionada es 5, entonces le agregamos un 0 al final
    if len(horaSeleccionada) == 5:
        horaSeleccionada += ":00"

    print(f"Insertando reserva: {id_clinica}, {correo_cliente}, {mascotaSeleccionada}, {fechaSeleccionada}, {horaSeleccionada}, {precio}")
    with open('data/reservas.csv', 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        reservations = list(reader)
     
    #transformar reservations en un data frame
    reservations_df = pd.DataFrame(reservations)
    #obtener el valor maximo de la columna id_reserva del data frame
    #
    reservations_df['id_reserva'] = reservations_df['id_reserva'].astype(int)
    max_id_reserva = reservations_df['id_reserva'].max()
    print("IDENTIFICANDO EL NÚMERO DE LA RESERVA MÁXIMA}}")
    print(f"max_id_reserva={max_id_reserva}")
    #Almacenamos max_id_reserva en una variable de seción
    session['max_id_reserva'] = int(max_id_reserva)
    print(f"session['max_id_reserva'] ={int(max_id_reserva)}")
    # Creamos el objeto con los datos de la nueva reserva
    session_id = session.get('session_id')

    new_reservation = {
        'id_reserva': (max_id_reserva + 1),
        'id_clinica': id_clinica,
        'correo_cliente': correo_cliente,
        'mascota': mascotaSeleccionada,
        'fecha': fechaSeleccionada,
        'hora': horaSeleccionada,
        'precio': precio, #Precio de la consulta
        'cargo_servicio': cargoServicio, #3% del precio de la consulta
        'valor_pagado': cargoTotal, #valor efectivamente pagado
        'estado': 1, # 0 = pendiente, 1 = pagado, 2 = cancelado
        'fecha_agrega_reserva': pd.Timestamp.now().strftime('%Y-%m-%d'),
        'hora_agrega_reserva': pd.Timestamp.now().strftime('%H:%M:%S'),
        'medico_que_atendio' : int(id_veterinario),
        'session_id': session_id,
        'token_pago': token
    }
    
    # Append the new reservation to the CSV file
    with open('data/reservas.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_reservation.keys(), delimiter=';')
        writer.writerow(new_reservation)
    
    ###############################
    ## Enviar correo al usuario con datos de la reserva
    datos_correo = {
    "nombresvet": reserva_en_proceso['nombresvet'] ,
    "apellidosvet": reserva_en_proceso['apellidosvet'] ,
    "fecha": reserva_en_proceso['hora'] ,
    "hora": reserva_en_proceso['hora'] ,
    "centro": reserva_en_proceso['clinica'] ,
    "direccion": reserva_en_proceso['direccion'] ,
    "comuna": reserva_en_proceso['comuna'] ,
    "reserva": session.get('max_id_reserva'),
    "valor": session.get('precio'),
    "tarjeta": session.get('numero_tarjeta')
    }
    print(f"Daros para el correo: {datos_correo}")
    enviar_correo_reserva(correo_cliente, datos_correo)
    
    return jsonify({"message": "Reserva creada exitosamente"}), 200


@app.route("/api/insertar_reservas", methods=["GET", "POST"])
def insert_reservation(estado_pago=None, medio_pago=None):
    # ---- DEBUG: variables de sesión
    print("Variables de sesión:")
    for key, value in session.items():
        print(f"{key}: {value}")

    # ---- Reserva en proceso (requerida)
    reserva_en_proceso = session.get('reserva_en_proceso')
    if not reserva_en_proceso:
        return jsonify({"message": "No hay reserva en proceso en la sesión."}), 400

    # ---- Identificación de usuario
    if session.get('user'):
        print("Usuario LOGEADO")
        correo_cliente = session.get('user')['email']
        nombre_cliente = session.get('user')['name']
    else:
        print("Usuario invitado")
        correo_cliente = session.get('correo_cliente_invitado') or session.get('correo_cliente')
        nombre_cliente = "Usuario invitado"
        if not correo_cliente:
            return jsonify({"message": "No hay correo para el usuario invitado."}), 400

    # ---- Datos base desde sesión
    id_clinica = reserva_en_proceso['id_clinica']
    id_veterinario = reserva_en_proceso['veterinario']
    mascotaSeleccionada = session.get('mascotaSeleccionada')

    # ---- Crear nueva mascota si corresponde (cuando la selección no es numérica)
    if (not str(mascotaSeleccionada).isdigit()):  # viene nombre directo
        with open('data/clientes_mascotas.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            clientes_mascotas = list(reader)

        nombre_mascota = mascotaSeleccionada
        clientes_mascotas_df = pd.DataFrame(clientes_mascotas)
        clientes_mascotas_df['id_clientes_mascotas'] = pd.to_numeric(
            clientes_mascotas_df.get('id_clientes_mascotas', pd.Series(dtype='float')),
            errors='coerce'
        )
        id_clientes_mascotas = int(clientes_mascotas_df['id_clientes_mascotas'].max(skipna=True) or 0) + 1
        session['mascotaSeleccionada'] = id_clientes_mascotas

        fecha_nacimiento = session.get('fecha_nacimiento')
        id_especie_raza = session.get('raza')

        new_mascota = {
            'id_clientes_mascotas': id_clientes_mascotas,   # <- corrige nombre de columna
            'correo_cliente': correo_cliente,
            'nombre_mascota': nombre_mascota,
            'fecha_nacimiento': fecha_nacimiento,
            'sexo': 0,
            'peso': 0,
            'id_especie_raza': int(id_especie_raza) if id_especie_raza else 0
        }
        with open('data/clientes_mascotas.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=new_mascota.keys(), delimiter=';')
            # No escribimos header aquí para evitar duplicarlo si ya existe
            writer.writerow(new_mascota)

    # ---- Si no hay mascota (invitado sin registrar), forzar 0
    if not mascotaSeleccionada:
        print("Mascota no seleccionada ya que usuario es invitado")
        session['mascotaSeleccionada'] = 0
        mascotaSeleccionada = 0

    # ---- Crear nueva mascota si flag crear_nueva_mascota == 1
    if 'crear_nueva_mascota' not in session:
        session['crear_nueva_mascota'] = 0
    print("[DEBUG] crear_nueva_mascota =", session['crear_nueva_mascota'])

    if session['crear_nueva_mascota'] == 1:
        with open('data/clientes_mascotas.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            clientes_mascotas = list(reader)

        clientes_mascotas_df = pd.DataFrame(clientes_mascotas)
        clientes_mascotas_df['id_clientes_mascotas'] = pd.to_numeric(
            clientes_mascotas_df.get('id_clientes_mascotas', pd.Series(dtype='float')),
            errors='coerce'
        )
        max_id_clientes_mascotas = int(clientes_mascotas_df['id_clientes_mascotas'].max(skipna=True) or 0)

        mascotaSeleccionada = max_id_clientes_mascotas + 1
        session['mascotaSeleccionada'] = mascotaSeleccionada
        session['max_id_clientes_mascotas'] = int(max_id_clientes_mascotas)

        nueva = session.get('nueva_mascota', {})
        nombre_mascota = nueva.get('nombre_mascota', 'Mascota')
        id_especie_raza = nueva.get('raza_mascota', 0)
        fecha_nacimiento = nueva.get('fecha_nacimiento')
        sexo = nueva.get('sexo_mascota', 0)
        peso = nueva.get('peso_mascota')

        new_mascota = {
            'id_clientes_mascotas': (max_id_clientes_mascotas + 1),   # <- corrige nombre de columna
            'correo_cliente': correo_cliente,
            'nombre_mascota': nombre_mascota,
            'fecha_nacimiento': fecha_nacimiento,
            'sexo': sexo,
            'peso': float(peso) if peso else 0.0,
            'id_especie_raza': int(id_especie_raza) if id_especie_raza else 0
        }
        with open('data/clientes_mascotas.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=new_mascota.keys(), delimiter=';')
            writer.writerow(new_mascota)

    # ---- Montos/fechas/horas
    fechaSeleccionada = reserva_en_proceso.get('fecha') or session.get('fecha')
    horaSeleccionada = reserva_en_proceso.get('hora') or session.get('hora')

    cargoServicio = int(session.get('cargoServicio', 0))
    cargoTotal = int(session.get('cargoTotal', 0))
    precio = int(reserva_en_proceso.get('valor', 0))

    token = session.get('token')

    # Normalizar hora a HH:MM:SS
    if horaSeleccionada and len(horaSeleccionada) == 5:
        horaSeleccionada += ":00"

    # ---- Determinar medio y estado de pago
    medio_from_req = None
    if request.method == "POST" and request.is_json:
        medio_from_req = (request.get_json() or {}).get('medio_pago')
    medio_from_qs = request.args.get('medio_pago')

    pago_confirmado = bool(session.get('pago_confirmado'))


    # Normaliza lo que venga por request (si llamas esta ruta vía HTTP directamente)
    medio_from_req = None
    if request.method in ("POST", "GET"):
        if request.is_json:
            medio_from_req = (request.get_json(silent=True) or {}).get("medio_pago")
        else:
            medio_from_req = request.args.get("medio_pago")

    # Si recibimos argumentos explícitos en la llamada Python, tienen prioridad
    if (estado_pago is not None) or (medio_pago is not None):
        medio_pago = (medio_pago or "EFECTIVO").upper()
        estado_pago = int(estado_pago) if estado_pago is not None else (1 if medio_pago == "WEBPAY" else 0)
        valor_pagado = cargoTotal if estado_pago == 1 else 0
    else:
        # Si no hay args, usamos sesión / request
        if pago_confirmado:
            estado_pago = 1
            medio_pago = "WEBPAY"
            valor_pagado = cargoTotal
        else:
            if (session.get("medio_pago", "").upper() == "EFECTIVO") or (medio_from_req and medio_from_req.upper() == "EFECTIVO"):
                estado_pago = 0
                medio_pago = "EFECTIVO"
                valor_pagado = 0
            else:
                # Por defecto, si no hay pago confirmado, tratamos como EFECTIVO (pendiente)
                estado_pago = 0
                medio_pago = "EFECTIVO"
                valor_pagado = 0

    print(f"[PAGO] medio_pago={medio_pago} | estado_pago={estado_pago} | valor_pagado={valor_pagado}")

    # ---- Leer CSV de reservas para obtener max id
    path_csv = 'data/reservas.csv'
    sep = ';'
    if not os.path.exists(path_csv):
        # Si no existe, creamos un DF vacío con columnas base
        df_res = pd.DataFrame(columns=[
            'id_reserva','id_clinica','correo_cliente','mascota','fecha','hora',
            'precio','cargo_servicio','valor_pagado','estado','fecha_agrega_reserva',
            'hora_agrega_reserva','medico_que_atendio','session_id','token_pago',
            'estado_pago','medio_pago'
        ])
        max_id_reserva = 0
    else:
        df_res = pd.read_csv(path_csv, sep=sep, dtype=str)
        if 'id_reserva' not in df_res.columns:
            return jsonify({"message": "El archivo reservas.csv no tiene columna id_reserva."}), 500

        df_res['id_reserva'] = pd.to_numeric(df_res['id_reserva'], errors='coerce').fillna(0).astype(int)
        max_id_reserva = int(df_res['id_reserva'].max(skipna=True) or 0)

    # ---- Nuevo ID y guardar en sesión (para Transbank buy_order)
    new_id_reserva = max_id_reserva + 1
    session['max_id_reserva'] = int(new_id_reserva)  # <- ahora consistente con buy_order

    session_id = session.get('session_id')

    new_reservation = {
        'id_reserva': new_id_reserva,
        'id_clinica': id_clinica,
        'correo_cliente': correo_cliente,
        'mascota': mascotaSeleccionada,
        'fecha': fechaSeleccionada,
        'hora': horaSeleccionada,
        'precio': precio,                     # Precio de la consulta
        'cargo_servicio': cargoServicio,      # 3% u otro
        'valor_pagado': valor_pagado,         # 0 si efectivo
        'estado': 1,                          # 1 = activa (ajusta si tu semántica es distinta)
        'fecha_agrega_reserva': pd.Timestamp.now().strftime('%Y-%m-%d'),
        'hora_agrega_reserva': pd.Timestamp.now().strftime('%H:%M:%S'),
        'medico_que_atendio': int(id_veterinario),
        'session_id': session_id,
        'token_pago': token if token else '',
        'estado_pago': estado_pago,           # <-- NUEVO
        'medio_pago': medio_pago              # <-- NUEVO
    }

    # ---- Asegurar columnas y escribir reescribiendo archivo (seguro)
    df_res = df_res.copy()

    # Asegurar columnas nuevas en DF
    for col in new_reservation.keys():
        if col not in df_res.columns:
            df_res[col] = ""

    # Verificación de duplicado lógico (opcionalmente estricta)
    dup = df_res[
        (df_res['id_clinica'].astype(str) == str(id_clinica)) &
        (df_res['correo_cliente'].astype(str) == str(correo_cliente)) &
        (df_res['mascota'].astype(str) == str(mascotaSeleccionada)) &
        (df_res['fecha'].astype(str) == str(fechaSeleccionada)) &
        (df_res['hora'].astype(str) == str(horaSeleccionada)) &
        (df_res['medico_que_atendio'].astype(str) == str(id_veterinario)) &
        (df_res['estado'].astype(str) == "1")
    ]
    if not dup.empty:
        return jsonify({"message": "La reserva ya existe."}), 409

    # Concatenar y guardar
    df_out = pd.concat([df_res, pd.DataFrame([new_reservation])], ignore_index=True)
    df_out.to_csv(path_csv, sep=sep, index=False, encoding='utf-8')

    # ---- Envío de correo (corrige fecha/hora)
    datos_correo = {
        "nombresvet": reserva_en_proceso.get('nombresvet'),
        "apellidosvet": reserva_en_proceso.get('apellidosvet'),
        "fecha": reserva_en_proceso.get('fecha'),
        "hora": reserva_en_proceso.get('hora'),
        "centro": reserva_en_proceso.get('clinica'),
        "direccion": reserva_en_proceso.get('direccion'),
        "comuna": reserva_en_proceso.get('comuna'),
        "reserva": new_id_reserva,                     # id recién asignado
        "valor": session.get('precio', precio),
        "tarjeta": session.get('numero_tarjeta') if pago_confirmado else None
    }
    print(f"Datos para el correo: {datos_correo}")
    try:
        enviar_correo_reserva(correo_cliente, datos_correo)
    except Exception as e:
        print(f"[WARN] Error enviando correo: {e}")

    return jsonify({"message": "Reserva creada exitosamente", "id_reserva": new_id_reserva, "medio_pago": medio_pago, "estado_pago": estado_pago}), 200


@app.route("/limpiar_sesion_parcial")
def limpiar_sesion_parcial():
    claves_a_conservar = {"user", 
                          "correo_cliente_invitado", 
                          "max_id_reserva",
                          "reserva_en_proceso",
                          "nombre_mascota",
                          "cargoServicio",
                          "cargoTotal",
                          "numero_tarjeta",
                          "nombre_cliente"}

    claves_actuales = list(session.keys())

    for clave in claves_actuales:
        if clave not in claves_a_conservar:
            session.pop(clave)

    return "Sesión limpiada (excepto user y correo_cliente_invitado)"

@app.route('/api/estado_autenticacion')
def estado_autenticacion():
    autenticado = 'user' in session
    return jsonify({'autenticado': autenticado})

#Define la ruta para servir archivos estáticos desde la carpeta 'data'
@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('data', filename)

@app.route("/api/parametros", methods=["GET"])
def parametros():
    try:
        #Recuperar los parametros de la URL
        id_clinica = request.args.get('id_clinica')
        id_clientes_mascotas = request.args.get('id_clientes_mascotas')
        fecha = request.args.get('fecha')
        hora = request.args.get('hora')
        # Crear un diccionario con los parámetros
        params = {
            'id_clinica': id_clinica,
            'id_clientes_mascotas': id_clientes_mascotas,
            'fecha': fecha,
            'hora': hora
        }
        # Devolver los parámetros como JSON
        return jsonify(params)   

    except Exception as e:
        return jsonify({"error": str(e)}), 500




# Cache simple en memoria para no golpear tanto a Nominatim (1 hora)
_reverse_cache = {}  # key: (lat_round, lon_round) -> {"ts": unix, "data": {...}}
_CACHE_TTL = 3600  # 1 hora

def _round_coord(x):
    # redondeo a 4 decimales (~11m): sube/baja si lo necesitas
    return round(float(x), 4)

def _pick_comuna(addr: dict) -> str | None:
    """
    Intenta extraer un nombre de comuna desde las llaves más comunes de Nominatim.
    Evita usar 'county' si viene como 'Provincia de ...'.
    """
    candidates = [
        "city", "town", "village", "municipality",
        "city_district", "suburb", "neighbourhood"
    ]
    for k in candidates:
        v = addr.get(k)
        if v:
            return v

    county = addr.get("county")
    if county and not county.lower().startswith("provincia de"):
        return county

    return None

@app.get("/api/reverse")
def reverse_geocode():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "Parámetros 'lat' y 'lon' son requeridos"}), 400

    try:
        latf = float(lat)
        lonf = float(lon)
    except ValueError:
        return jsonify({"error": "Parámetros 'lat' y/o 'lon' inválidos"}), 400

    key = (_round_coord(latf), _round_coord(lonf))
    now = time.time()
    # cache
    hit = _reverse_cache.get(key)
    if hit and now - hit["ts"] < _CACHE_TTL:
        return jsonify(hit["data"])

    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "jsonv2",
        "lat": latf,
        "lon": lonf,
        "addressdetails": 1,
        "accept-language": "es",
        "zoom": 14
    }
    headers = {
        "User-Agent": "PawCare/1.0 (contacto: alhen1970@gmail.com)"  # IDENTIFÍCATE
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            return jsonify({"error": f"Nominatim {r.status_code}"}), r.status_code
        data = r.json()
        addr = data.get("address", {})
        comuna = _pick_comuna(addr) or "Comuna no encontrada"

        # Plan B: si no encontramos comuna en zoom 14, probamos un zoom distinto
        if comuna == "Comuna no encontrada":
            params_b = params | {"zoom": 12}
            rb = requests.get(url, params=params_b, headers=headers, timeout=10)
            if rb.status_code == 200:
                addr_b = rb.json().get("address", {})
                comuna_b = _pick_comuna(addr_b)
                if comuna_b:
                    comuna = comuna_b

        payload = {
            "comuna": comuna,
            "display_name": data.get("display_name"),
            "address": addr,
            "lat": data.get("lat"),
            "lon": data.get("lon")
        }
        _reverse_cache[key] = {"ts": now, "data": payload}
        return jsonify(payload)

    except requests.RequestException as e:
        return jsonify({"error": f"Fallo consultando Nominatim: {e}"}), 502

def _norm(s: str) -> str:
    s = (s or "").strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold()

@app.route("/api/insertar_comunas", methods=["POST"])
def insertar_comunas():
    print("DEBUG ENTRANDO A INSERTAR COMUNAS")
    data = request.json or {}
    comuna_input = data.get("comuna", "")

    # Si existe sesión 'comuna2', sobrescribe
    comuna2 = session.get('comuna2')
    print("Comuna recibida desde la url:", comuna2)
    if comuna2:
        comuna_input = comuna2

    comuna_str = str(comuna_input).strip()
    print("Comuna recibida:", comuna_str)

    # Lee el archivo data/dpa.csv y lo convierte a un dataframe
    # Se asume columnas: Region (código o id), Comuna (código), Nombre_Comuna (string)
    df = pd.read_csv("data/dpa.csv", delimiter=";")

    # Detectar si es código numérico (aunque venga como string con espacios)
    es_codigo = comuna_str.isdigit()
    if not es_codigo:
        # permitir "13101", "13101 " etc
        es_codigo = comuna_str.replace(" ", "").isdigit()

    filtered_df = pd.DataFrame()

    if es_codigo:
        try:
            comuna_code = int(comuna_str.replace(" ", ""))
            filtered_df = df[df['Comuna'] == comuna_code]
        except Exception:
            pass
    else:
        # Comparación robusta por nombre (sin acentos/case)
        nombre_norm = _norm(comuna_str)
        df = df.copy()
        df["__nombre_norm__"] = df["Nombre_Comuna"].fillna("").apply(_norm)

        # 1) match exacto normalizado
        filtered_df = df[df["__nombre_norm__"] == nombre_norm]

        # 2) si no hay exacto, intenta contención (por ej. "santiago centro" -> "santiago")
        if filtered_df.empty and nombre_norm:
            # busca que una de las palabras principales esté contenida
            # tomamos la primera palabra fuerte (no artículos muy cortos)
            tokens = [t for t in re.split(r"\s+", nombre_norm) if len(t) > 2]
            if tokens:
                pat = r"|".join(re.escape(t) for t in tokens)
                mask = df["__nombre_norm__"].str.contains(rf"\b({pat})\b", regex=True)
                filtered_df = df[mask]

    # Si sigue vacío, usa fallback (13101) como tenías
    if filtered_df.empty:
        filtered_df = df[df['Comuna'] == 13101]

    if not filtered_df.empty:
        # Obtiene la región del primer match y lista todas las comunas de esa región
        region = filtered_df.iloc[0]['Region']
        df_region = df[df['Region'] == region].copy()

        # Determinar cuál debe ir 'selected'
        selected_code = None
        if es_codigo:
            selected_code = int(str(comuna_str).replace(" ", ""))
        else:
            # si nos llegó nombre, tomamos el primer match
            selected_code = int(filtered_df.iloc[0]['Comuna'])

        # Construir options
        options = []
        for _, row in df_region.iterrows():
            sel = "selected" if int(row['Comuna']) == selected_code else ""
            options.append(f"<option value='{int(row['Comuna'])}' {sel}>{row['Nombre_Comuna']}</option>")

        return "".join(options)

    return "<option value=''>No se encontraron comunas</option>"

@app.route("/api/especialidades_teleconsulta", methods=["GET"])
def obtener_especialidades_teleconsulta():
    try:
        # Leer el archivo especialidades.csv
        df = pd.read_csv("data/especialidades.csv", sep=";")
        # Filtrar las especialidades que contienen la palabra "telemedicina" en el campo tipo
        df_filtrado = df[df["tipo"].str.contains("telemedicina", case=False, na=False)]
        # Crear las opciones para el select
        options = ""
        for index, row in df_filtrado.iterrows():
            options += f"<option value='{row['id_especialidad']}'>{row['especialidad']}</option>"
        return options
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 📌 Ruta de iniciar sesión
@app.route("/iniciar_sesion")
def iniciar_sesion():
    #primero debo ver si status_code existe y esta definida
    #si no existe, entonces la reserva no fue creada
    user = session.get("user", None)
    return render_template("iniciar_sesion.html", user = user)

# 📌 Ruta de iniciar sesión
@app.route("/favoritos")
#@login_required
def favoritos():
    session['next'] = request.full_path
    print(f"[INFO] next favoritos: {request.full_path}")
    user = session.get("user", None)

    print(session.get("user"))
    if not user:
        return redirect(url_for("login"))    
    return render_template("favoritos.html", user=user)

    #user = session.get("user", None)
    #si no hay usuario, entonces redirigimos a la página de inicio de sesión
    #session['next'] = request.full_path
    #print(f"[INFO] next: {request.full_path}")
    #if not user:
    #    return redirect(url_for("login"))
    #return render_template("favoritos.html", user=user)


# 📌 Ruta de Mis Citas
@app.route("/mis_citas")
#@login_required
def mis_citas():
#    user = session.get("user")

    #si no hay usuario, entonces redirigimos a la página de inicio de sesión
    session['next'] = request.full_path
    print(f"[INFO] next mis_citas: {request.full_path}")
    user = session.get("user", None)
    print(f"[INFO] user mis_citas: {user}")
    #si no hay usuario, entonces redirigimos a la página de inicio de sesión
    if not user:
        return redirect(url_for("login"))
    # Leer reservas.csv
    email = user.get("email")
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas = df_reservas[(df_reservas["correo_cliente"] == email)]
    df_reservas = df_reservas[(df_reservas["mascota"] >0)]

    #si el campo estado==1 lo cambiamos por Confirmada, si es -1 lo cambiamos por Cancelada, si es 0 lo cambiamos por Confirmar
    df_reservas["estado"] = df_reservas["estado"].replace({1: "Confirmada", -1: "Cancelada", 0: "Confirmar"})


    # Leer clinicas.csv y unir por id_clinica
    df_clinicas = pd.read_csv("data/clinicas.csv", sep=";")
    df_reservas = df_reservas.merge(df_clinicas[["id_clinica", "nombre", "direccion", "dpa"]], on="id_clinica", how="left")

    # Leer clientes_mascotas.csv y unir por correo_cliente y mascota = id_clientes_mascotas
    df_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    print(df_mascotas)
    df_mascotas = df_mascotas[df_mascotas["correo_cliente"] == email]
    print(df_mascotas)
    df_reservas = df_reservas.merge(
        df_mascotas[["id_clientes_mascotas", "nombre_mascota"]],
        left_on="mascota",
        right_on="id_clientes_mascotas",
        how="left"
    )
    #si la mascota de df_reservas no existe en df_mascotas, entonces al campo nombre mascota le ponemos "Nueva Mascotta"
    df_reservas["nombre_mascota"] = df_reservas["nombre_mascota"].fillna("Nueva Mascota")

    # Leer dpa.csv y unir por dpa para obtener Nombre_Comuna
    df_dpa = pd.read_csv("data/dpa.csv", sep=";")
    df_reservas = df_reservas.merge(
        df_dpa[["id_dpa", "Nombre_Comuna"]],
        left_on="dpa",
        right_on="id_dpa",
        how="left"
    )

#obtenemos los datos del veterinario de staff.csv
    df_staff = pd.read_csv("data/staff.csv", sep=";")
    #pasamos df_reservas["medico_que_atendio"] a int
    df_reservas["medico_que_atendio"] = df_reservas["medico_que_atendio"].astype(int)   
    
    df_reservas = df_reservas.merge(
        df_staff[["id_veterinario", "nombres", "apellidos"]],
        left_on="medico_que_atendio",
        right_on="id_veterinario",
        how="left"
    )    


    # Convertir columna fecha a datetime
    df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], format='mixed', dayfirst=True)
    df_reservas["hora_am_pm"] = (
    pd.to_datetime(df_reservas["hora"], errors="coerce")
      .dt.strftime("%I:%M %p")
      .str.lstrip("0")   # quita cero a la izquierda (09:30 -> 9:30)
    )

    df_reservas = df_reservas.sort_values(by=["fecha"], ascending=False)
    print("[INFO] DataFrame de reservas después de la unión:")
    print(df_reservas)
    # Convertir dataframe a lista de diccionarios
    mis_citas = df_reservas.to_dict(orient="records")
    if not user:
        return redirect(url_for("login"))    
    return render_template("mis_citas.html", user=user, mis_citas=mis_citas)




@app.route('/cancelar_cita', methods=["POST"])
def cancelar_cita():
    #data = request.get_json(silent=True)
    data = request.get_json()
    if data is None:
        print("[ERROR] No se recibió un cuerpo JSON válido en /cancelar_cita")
        return jsonify({"success": False, "error": "JSON inválido o vacío"}), 400    
    print(f"[INFO] Datos recibidos en cancelar_cita: {data}")
    user = session.get("user", None)
    #si no hay usuario, entonces redirigimos a la página de inicio de sesión
    session['next'] = request.full_path
    print(f"[INFO] next: {request.full_path}")
    if not user:
        return redirect(url_for("login"))    
    #data = request.json

    id_reserva = data.get("id_reserva")
    
    print(f"[INFO] Datos recibidos en cancelar_cita: {id_reserva}")
    try:
        df = pd.read_csv("data/reservas.csv", sep=";")
        #filtramos df por id_reserva
        id_reserva = int(id_reserva)
        df = df[df["id_reserva"] == id_reserva]
        if df.empty:
            return jsonify({"success": False, "error": "Reserva no encontrada."}), 404
        # cambiamos el estado de la reserva a -1 (cancelada)
        df.loc[df["id_reserva"] == id_reserva, "estado"] = -1
        df.to_csv("data/reservas.csv", sep=";", index=False)
        return jsonify({"success": True}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/confirmar_cita', methods=["POST"])
#@login_required
def confirmar_cita(id_cita, confirma):
    print("Entré a confirmar_cita")
    print(f"[INFO] Datos recibidos en confirmar_cita: {id_cita}, {confirma}")
    #data = request.get_json(silent=True)
    #if data is None:
    #    print("[ERROR] No se recibió un cuerpo JSON válido en /confirmar_cita")
    #    return jsonify({"success": False, "error": "JSON inválido o vacío"}), 400    
    #print(f"[INFO] Datos recibidos en confirmar_cita: {data}")
    user = session.get("user", None)
    #si no hay usuario, entonces redirigimos a la página de inicio de sesión
    session['next'] = request.full_path
    print(f"[INFO] next en confirmar_cita: {request.full_path}")
    if not user:
        return redirect(url_for("login"))    
    
    #id_cita = int(data["id_cita"])
    id_cita = int(id_cita)

    correo_cliente= user.get("email")
    nombre_cliente = user.get("name")
    #print(f"[INFO] Datos recibidos en cancelar_cita: {id_cita}")
    try:
        df = pd.read_csv("data/reservas.csv", sep=";")
        print(f"[INFO] DataFrame cargado: {df.head()}")
        mask = (
            (df["id_reserva"] == id_cita)
        )
        print(f"[INFO] Máscara de filtro: {mask}")

        if mask.any():
            df.loc[mask, "estado"] = 1
            df.to_csv("data/reservas.csv", sep=";", index=False)
            id_clinica=df.loc[mask, "id_clinica"].values[0]
            fechaSeleccionada=df.loc[mask, "fecha"].values[0]
            horaSeleccionada=df.loc[mask, "hora"].values[0]
            id_reserva = df.loc[mask, "id_reserva"].values[0]            
            msg = Message("Tu hora ha sido confirmada",
                        sender="alhen1970@gmail.com",
                        recipients=[correo_cliente])
            msg.html = f"""
            
            <p>Hola, {nombre_cliente}, gracias por confirmar una hora para tu mascota en:</p>
            <p><b><li>Clínica veterinaria:</b> {id_clinica}</p>
            <p><b><li>Fecha:</b> {fechaSeleccionada}</p>
            <p><b><li>Hora:</b> {horaSeleccionada}</p>
            <p><b><li>Reserva Número:</b> {id_reserva}</p>
            <p>Atte.,</p>
            <p>El equipo de PawCare</p>

            """
            mail.send(msg)
            correo_enviado=True


            if correo_enviado:
                # Mostrar una ventana del tipo alert, con el título "Confirmación aceptada" y el mensaje "Reserva confirmada y correo enviado"
                #alert("Confirmación aceptada", "Reserva confirmada y correo enviado")




                return jsonify({"message": "Reserva confirmada y correo enviado"}), 200
            else:
                return jsonify({"error": "No se pudo enviar el correo"}), 500

            #return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Reserva no encontrada."}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/receta', methods=["GET"])
#@login_required
def receta():
    user = session.get("user", None)
    if not user:
        session['next'] = request.full_path
        return redirect(url_for("login"))

    # Obtener id de la receta desde la URL
    id_reserva = request.args.get("id_cita", type=int)
    if not id_reserva:
        return "ID de reserva no especificado", 400

    try:
        df = pd.read_csv("data/reservas.csv", sep=";")

        # Buscar la reserva correspondiente
        reserva = df[df["id_reserva"] == id_reserva]

        if reserva.empty:
            return "Reserva no encontrada", 404

        receta = reserva.iloc[0].get("receta")
        if not receta or receta.strip() == "":
            return "No hay receta registrada para esta cita", 404

        # Crear PDF en memoria
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, receta)

        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        # Devolver el PDF como archivo descargable
        return send_file(
            pdf_output,
            mimetype="application/pdf",
            download_name=f"receta_{id_reserva}.pdf",
            as_attachment=True
        )

    except Exception as e:
        print(f"[ERROR] Error al generar receta: {e}")
        return "Error interno del servidor", 500


@app.route("/evaluar_cita", methods=["POST"])
def evaluar_cita():
    try:
        data = request.get_json()
        id_reserva = int(data["reserva"])
        general = int(data.get("general", 0))
        puntualidad = int(data.get("puntualidad", 0))
        precio_calidad = int(data.get("precio_calidad", 0))

        df = pd.read_csv("data/reservas.csv", sep=";")
        if id_reserva in df["id_reserva"].astype(int).values:
            mask = df["id_reserva"] == id_reserva
            df.loc[mask, "general"] = general
            df.loc[mask, "puntualidad"] = puntualidad
            df.loc[mask, "precio-calidad"] = precio_calidad
            correo_cliente = df.loc[mask, "correo_cliente"].values[0]
            df.to_csv("data/reservas.csv", sep=";", index=False)

            # Enviar correo
            msg = Message("Tu evaluación a la clínica",
                          sender="alhen1970@gmail.com",
                          recipients=[correo_cliente])
            msg.body = f"""
Muchas gracias por aportar con tu evaluación, de esta forma nos ayudas a prestar una mejor atención a nuestros clientes.

Evaluación General: {general}
Puntualidad: {puntualidad}
Precio Calidad: {precio_calidad}

Atte.,
Tu equipo de PawCare

            """
            mail.send(msg)

            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Reserva no encontrada"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/pawcarepro')
def pawcarepro():
    session['next'] = request.full_path
    print(f"[INFO] next pawcarepro: {request.full_path}")
    user = session.get("user", None)

    print(session.get("user"))
    if not user:
        return redirect(url_for("login"))    
    email=user.get("email")
    id_tipo_usuario = session.get("id_tipo_usuario")
    id_tipo_usuario=int(id_tipo_usuario)
    if id_tipo_usuario!= 1:
        tipo_usuario = session.get("tipo_usuario")
        df_adm_clinica = pd.read_csv("data/adm_clinica.csv", sep=";")
        df_adm_clinica = df_adm_clinica[(df_adm_clinica["correo_cliente"] == email)]        
        id_clinica_adm = df_adm_clinica['id_clinica'].values[0]
        session['id_clinica_adm'] = id_clinica_adm
        df_clinicas = pd.read_csv("data/clinicas.csv", sep=";")
        df_clinicas_filtradas = df_clinicas[df_clinicas["id_clinica"] == id_clinica_adm]
        print("INFO df_clinicas_filtradas")
        print(df_clinicas_filtradas)
        clinicas_filtradas = df_clinicas_filtradas.to_dict(orient="records")
        del df_clinicas_filtradas
        del df_clinicas
        del df_adm_clinica

    else:
        #es un usuario cliente, por lo que no debe estar acá
        #lo redirigimos al home
        return render_template("/")

    df_veterinario = pd.read_csv("data/staff.csv", sep=";")
    df_veterinario = df_veterinario[(df_veterinario["correo"] == email)]
    #si df_vaterinario está vacío, entonces redirigimos a la página de inicio de sesión
    if df_veterinario.empty:
        print("[ERROR] No se encontró el veterinario en el staff")
        return redirect(url_for("login"))
    #print(f"[INFO] Datos del veterinario:")
    #print(f"{df_veterinario}")
    id_veterinario = df_veterinario["id_veterinario"].values[0]

    #Ahora generamos los datos para mostrar la agenda del veterinario
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], dayfirst=True, errors="coerce")
    hoy = pd.to_datetime(datetime.today().date())

    print(f"DEBUG: id_veterinario=", id_veterinario)
    df_filtradas = df_reservas[
        (df_reservas["medico_que_atendio"] == id_veterinario)
    ]


    df_clientes_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    #a df_filtradas le agregamos los datos de clientes_mascotas, donde id_clientes_mascotas == mascota
    df_filtradas = df_filtradas.merge(
        df_clientes_mascotas[["id_clientes_mascotas", "nombre_mascota", "sexo", "id_especie_raza"]],
        left_on="mascota",
        right_on="id_clientes_mascotas",
        how="left"
    )

    #cerramos o eliminamos df_clientes_mascotas de la memoria de python
    del df_clientes_mascotas

    df_razas = pd.read_csv("data/razas.csv", sep=";")
    #a df_filtradas le agregamos los datos de razas, donde id_especie_raza == id_especie_raza

    df_filtradas = df_filtradas.merge(
        df_razas[["id_raza", "nombre_raza"]],
        left_on="id_especie_raza",
        right_on="id_raza",
        how="left"
    )
    del df_razas

    df_especie_raza = pd.read_csv("data/especie_raza.csv", sep=";")
    #a df_filtradas le agregamos los datos de especie_raza, donde id_especie_raza == id_especie_raza
    df_filtradas = df_filtradas.merge(
        df_especie_raza[["id_especie_raza", "id_especie"]],
        left_on="id_especie_raza",
        right_on="id_especie_raza",
        how="left"
    )  
    del df_especie_raza

    df_especies = pd.read_csv("data/especies.csv", sep=";")
    #a df_filtradas le agregamos los datos de especies, donde id_especie == id_especie
    df_filtradas = df_filtradas.merge(
        df_especies[["id_especie", "especie", "icono"]],
        left_on="id_especie",
        right_on="id_especie",
        how="left"
    )
    del df_especies

    print(f"[DEBUG] df_filtradas:")
    print(df_filtradas)
    df_agenda = df_filtradas[
        (df_filtradas["fecha"] >= hoy)
    ]
    #ordenamos df_agenda por fecha y hora desde lo más actual a lo más antiguo
    df_agenda = df_agenda.sort_values(by=["fecha", "hora"], ascending=[False, False])
    
    
    #calculamos las horas faltantes para la próxima cita, considerando el campo hora

    # Convertir columnas
    df_agenda["hora2"] = pd.to_datetime(df_agenda["hora"], errors="coerce").dt.time
    df_agenda["fecha2"] = pd.to_datetime(df_agenda["fecha"], dayfirst=True, errors="coerce")
    # Combinar fecha y hora en una nueva columna datetime completa
    df_agenda["fecha_hora"] = df_agenda.apply(
        lambda row: datetime.combine(row["fecha2"], row["hora2"]) if pd.notnull(row["fecha2"]) and pd.notnull(row["hora2"]) else None,
        axis=1
    )
    # Calcular el tiempo faltante en horas
    df_agenda["tiempo_faltante_horas"] = df_agenda["fecha_hora"].apply(
        lambda dt: (dt - datetime.now()).total_seconds() / 3600 if dt else None
    )

    # Formatear el tiempo restante
    df_agenda["tiempo_faltante_horas"] = df_agenda["tiempo_faltante_horas"].apply(
        lambda x: f"{int(x // 24)} días, {int(x % 24)} horas, {int((x % 1) * 60)} minutos" if x and x > 0 else "Ya pasó"
    )


    df_agenda["fecha"] = df_agenda["fecha"].dt.strftime("%d/%m/%Y")
    df_agenda["hora"] = pd.to_datetime(df_agenda["hora"], errors="coerce").dt.strftime("%H:%M")

    print(f"[DEBUG] df_agenda:")
    print(df_agenda)
    agenda = df_agenda.to_dict(orient="records")


    df_agenda_historica = df_filtradas[
        (df_filtradas["fecha"] < hoy)
    ]

    df_agenda_historica = df_agenda_historica.sort_values(by=["fecha", "hora"], ascending=[False, False])

    df_agenda_historica["fecha"] = df_agenda_historica["fecha"].dt.strftime("%d/%m/%Y")
    df_agenda_historica["hora"] = pd.to_datetime(df_agenda_historica["hora"], errors="coerce").dt.strftime("%H:%M")

    # filtramos df_agenda_historica para cada "mascota" solo aparezca una vez con la fecha más reciente
    #df_agenda_historica = df_agenda_historica.sort_values(by=["mascota", "fecha"], ascending=[True, False])
    df_agenda_historica = df_agenda_historica.drop_duplicates(subset=["mascota"], keep="first")

    agenda_historica = df_agenda_historica.to_dict(orient="records")

    print(f"[DEBUG] df_filtradas final:")
    print(f"{df_filtradas.head()}")

    

    del df_filtradas
    del df_agenda
    del df_agenda_historica

    datos_veterinario = df_veterinario.to_dict(orient="records")
    del df_veterinario

    print(f"tipo_usuario= {tipo_usuario}")

    return render_template("pawcarepro.html", 
                            user = user , 
                            datos_veterinario = datos_veterinario,
                            agenda = agenda,
                            agenda_historica = agenda_historica,
                            clinicas_filtradas = clinicas_filtradas,
                            tipo_usuario = tipo_usuario
    )


@app.route('/mis_pacientes')
def mis_pacientes():
    session['next'] = request.full_path
    print(f"[INFO] next pawcarepro: {request.full_path}")
    user = session.get("user", None)

    print(session.get("user"))
    if not user:
        return redirect(url_for("login"))    
    email=user.get("email")
    df_veterinario = pd.read_csv("data/staff.csv", sep=";")
    df_veterinario = df_veterinario[(df_veterinario["correo"] == email)]
    #si df_vaterinario está vacío, entonces redirigimos a la página de inicio de sesión
    if df_veterinario.empty:
        print("[ERROR] No se encontró el veterinario en el staff")
        return redirect(url_for("login"))
    #print(f"[INFO] Datos del veterinario:")
    #print(f"{df_veterinario}")
    id_veterinario = df_veterinario["id_veterinario"].values[0]

    #Ahora generamos los datos para mostrar la agenda del veterinario
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], dayfirst=True, errors="coerce")
    hoy = pd.to_datetime(datetime.today().date())

    df_filtradas = df_reservas[
        (df_reservas["medico_que_atendio"] == id_veterinario)
    ]
    print("DEBUG mis_pacientes df_filtradas 1")
    print(df_filtradas)
    #creamos un data frame que contenga todos los email unicos de df_filtradas
    df_filtradas = df_filtradas.drop_duplicates(subset="correo_cliente")

    print("DEBUG mis_pacientes df_filtradas 2")
    print(df_filtradas)
    df_clientes_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    #a df_filtradas le agregamos los datos de clientes_mascotas, donde id_clientes_mascotas == mascota
    df_filtradas = df_filtradas.merge(
        df_clientes_mascotas[["id_clientes_mascotas", "nombre_mascota", "sexo", "id_especie_raza"]],
        left_on="mascota",
        right_on="id_clientes_mascotas",
        how="left"
    )

    #cerramos o eliminamos df_clientes_mascotas de la memoria de python
    del df_clientes_mascotas

    df_pacientes = df_filtradas
    del df_filtradas

    df_razas = pd.read_csv("data/razas.csv", sep=";")
    #a df_filtradas le agregamos los datos de razas, donde id_especie_raza == id_especie_raza

    df_pacientes = df_pacientes.merge(
        df_razas[["id_raza", "nombre_raza"]],
        left_on="id_especie_raza",
        right_on="id_raza",
        how="left"
    )
    del df_razas

    df_especie_raza = pd.read_csv("data/especie_raza.csv", sep=";")
    #a df_filtradas le agregamos los datos de especie_raza, donde id_especie_raza == id_especie_raza
    df_pacientes = df_pacientes.merge(
        df_especie_raza[["id_especie_raza", "id_especie"]],
        left_on="id_especie_raza",
        right_on="id_especie_raza",
        how="left"
    )  
    del df_especie_raza

    df_especies = pd.read_csv("data/especies.csv", sep=";")
    #a df_filtradas le agregamos los datos de especies, donde id_especie == id_especie
    df_pacientes = df_pacientes.merge(
        df_especies[["id_especie", "especie", "icono"]],
        left_on="id_especie",
        right_on="id_especie",
        how="left"
    )
    del df_especies

    
    print("DEBUG mis_pacientes df_veterinario")
    print(df_veterinario)   
    
    datos_veterinario = df_veterinario.to_dict(orient="records")
    del df_veterinario

    print("DEBUG mis_pacientes df_pacientes")
    print(df_pacientes)
    pacientes = df_pacientes.to_dict(orient="records")
    del df_pacientes

    return render_template("mis_pacientes.html", 
                            user=user, 
                            datos_veterinario=datos_veterinario,
                            pacientes=pacientes
    )



@app.route("/api/precios")
def api_precios():

    id_clinica = session.get('id_clinica')
    # Leer los datos
    especialidades = pd.read_csv("data/especialidades.csv", sep=";")
    prestaciones = pd.read_csv("data/prestaciones.csv", sep=";")
    precios_raw = pd.read_csv("data/precios.csv", sep=";")
    precios_raw = precios_raw[precios_raw['id_clinica'] == int(id_clinica)]
    precios_raw = precios_raw.merge(
        prestaciones,
        left_on="id_prestacion",
        right_on="id_prestacion",
        how="left"
    )

    precios_raw = precios_raw.merge(
        especialidades,
        left_on="id_especialidad",
        right_on="id_especialidad",
        how="left"
    )
    # creamos un sub conjunto de precios_raw y lo llamaremos especialidades_unicas, que contenga id_especialidad y especialidad unicos
    #especialidades_unicas = precios_raw[["id_especialidad", "especialidad"]].drop_duplicates()
    #print(especialidades_unicas)
    precios_raw = jsonify(precios_raw.to_dict(orient="records"))
    #especialidades_unicas = jsonify(especialidades_unicas.to_dict(orient="records"))

    return precios_raw



@app.route("/api/especialidades_clinica")
def especialidades_clinica():

    id_clinica = session.get('id_clinica')
    id_veterinario = request.args.get('id_veterinario')
    #si id_veterinario es vacio o nulo, le asignamos el valor de la variable de sesion id_veterinario
    if not id_veterinario:
        id_veterinario = session.get('id_veterinario')
    
    # Leer los datos
    veterinario_prestaciones = pd.read_csv("data/veterinario_prestaciones.csv", sep=";")
    veterinario_prestaciones = veterinario_prestaciones[veterinario_prestaciones['id_veterinario'] == int(id_veterinario)]

    #prestaciones = pd.read_csv("data/prestaciones.csv", sep=";")
    #Filtramos prestaciones por id_prestacion de especialidades_prestaciones
    #prestaciones = prestaciones[prestaciones['id_prestacion'].isin(veterinario_prestaciones['id_prestacion'])]
    especialidades = pd.read_csv("data/especialidades.csv", sep=";")
    #especialidades = especialidades[especialidades['id_especialidad'].isin(prestaciones['id_especialidad'])]
    veterinario_prestaciones = veterinario_prestaciones.merge(
        especialidades,
        left_on="id_especialidad",
        right_on="id_especialidad",
        how="left"
    )    
    #eliminamos de veterinario_prestaciones las filas repetidas del campo id_especialidad
    veterinario_prestaciones = veterinario_prestaciones.drop_duplicates(subset=["id_especialidad"])
    
    print(f"especialidades: {especialidades}")


    veterinario_prestaciones = jsonify(veterinario_prestaciones.to_dict(orient="records"))

    return veterinario_prestaciones



@app.route("/api/prestaciones_clinica")
def prestaciones_clinica():

    id_clinica = session.get('id_clinica')
    id_especialidad = request.args.get('id_especialidad')
    id_veterinario = request.args.get('id_veterinario')
    # Leer los datos
    veterinario_prestaciones = pd.read_csv("data/veterinario_prestaciones.csv", sep=";")
    veterinario_prestaciones = veterinario_prestaciones[veterinario_prestaciones['id_veterinario'] == int(id_veterinario)]
    veterinario_prestaciones = veterinario_prestaciones[veterinario_prestaciones['id_especialidad'] == int(id_especialidad)]

    prestaciones = pd.read_csv("data/prestaciones.csv", sep=";")
    #Filtramos prestaciones por id_especialidad
    prestaciones = prestaciones[prestaciones['id_especialidad'] == int(id_especialidad)]

    #A veterinario_prestaciones le agregamos las columnas de prestaciones, donde id_prestacion de prestaciones == id_prestacion de veterinario_prestaciones, excepto el campo id_especialidad
    veterinario_prestaciones = veterinario_prestaciones.merge(
        prestaciones,
        left_on="id_prestacion",
        right_on="id_prestacion",
        how="left"
    )
    
    
    # Eliminar el campo 'id_especialidad' después del merge
    veterinario_prestaciones = veterinario_prestaciones.drop(columns=['id_especialidad_y'])
    #renombrar el campo 'id_especialidad_x' a 'id_especialidad'
    veterinario_prestaciones = veterinario_prestaciones.rename(columns={'id_especialidad_x': 'id_especialidad'})   
    
    #Filtramos veterinario_prestaciones por id_especialidad igual a id_especialidad
    #veterinario_prestaciones = veterinario_prestaciones[veterinario_prestaciones['id_especialidad'] == int(id_especialidad)]
    print("veterinario_prestaciones")
    print(veterinario_prestaciones)
    
    precios = pd.read_csv("data/precios.csv", sep=";")

    
    #filtramos los precios por id_veterinario y id_clinica
    precios = precios[precios['id_clinica'] == int(id_clinica)]
    #print("precios")
    #print(precios)
    #A veterinario_prestaciones le agregamos sólo la columna "valor" de precios, donde id_prestacion de precios == id_prestacion de veterinario_prestaciones

    veterinario_prestaciones = veterinario_prestaciones.merge(
        precios[['id_prestacion', 'valor']],
        left_on="id_prestacion",
        right_on="id_prestacion",
        how="left"
    )
    print("veterinario_prestaciones FINAL")
    print(veterinario_prestaciones)
        
    veterinario_prestaciones = jsonify(veterinario_prestaciones.to_dict(orient="records"))
    
    return veterinario_prestaciones


@app.route("/api/prestaciones_clinica_respaldo")
def prestaciones_clinica_respaldo():

    id_clinica = session.get('id_clinica')
    id_especialidad = request.args.get('id_especialidad')
    id_veterinario = request.args.get('id_veterinario')
    # Leer los datos
    veterinario_prestaciones = pd.read_csv("data/veterinario_prestaciones.csv", sep=";")
    veterinario_prestaciones = veterinario_prestaciones[veterinario_prestaciones['id_veterinario'] == int(id_veterinario)]

    prestaciones = pd.read_csv("data/prestaciones.csv", sep=";")

    #A veterinario_prestaciones le agregamos las columnas de prestaciones, donde id_prestacion de prestaciones == id_prestacion de veterinario_prestaciones
    veterinario_prestaciones = veterinario_prestaciones.merge(
        prestaciones,
        left_on="id_prestacion",
        right_on="id_prestacion",
        how="left"
    )
    #Filtramos veterinario_prestaciones por id_especialidad igual a id_especialidad
    veterinario_prestaciones = veterinario_prestaciones[veterinario_prestaciones['id_especialidad'] == int(id_especialidad)]
    

    especialidades = pd.read_csv("data/especialidades.csv", sep=";")
    #nos quedamos solo con las especialidades que tienen id_especialidad == id_especialidad
    especialidades = especialidades[especialidades['id_especialidad'] == int(id_especialidad)]

    precios_raw = pd.read_csv("data/precios.csv", sep=";")
    precios_raw = precios_raw[precios_raw['id_clinica'] == int(id_clinica)]
    precios_raw = precios_raw.merge(
        prestaciones,
        left_on="id_prestacion",
        right_on="id_prestacion",
        how="left"
    )

    precios_raw = precios_raw.merge(
        especialidades,
        left_on="id_especialidad",
        right_on="id_especialidad",
        how="left"
    )
    # creamos un sub conjunto de precios_raw y lo llamaremos especialidades_unicas, que contenga id_especialidad y especialidad unicos
    prestaciones_unicas = precios_raw[["id_prestacion", "prestacion"]].drop_duplicates()
    print(prestaciones_unicas)
    prestaciones_unicas = jsonify(prestaciones_unicas.to_dict(orient="records"))

    return prestaciones_unicas

@app.template_filter('formato_miles')
def formato_miles(valor):
    try:
        session['precio']=int(valor)+int(int(valor)*0.03)
        return f"{int(valor):,}".replace(",", ".")
    except:
        return valor

@app.route('/api/pagar', methods=['GET'])
def api_pagar():
    try:
        # Datos necesarios para crear la transacción
        #buy_order = str(uuid.uuid4())[:10]
        buy_order = str(session.get('max_id_reserva'))  # Obtener el ID de la reserva
        session['buy_order'] = buy_order
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        #pasamos session.get('precio', 1000) a vormato decimal con 0 decimal


        print("Variables de sesión en api/pagar:")
        for key, value in session.items():  
            print(f"{key}: {value}")  

        amount = int(session.get('cargoTotal'))
        print(f"cargoTotal={session.get('cargoTotal')}")
        #amount = int(session.get('precio', 1000))
        return_url = url_for('respuesta_pago', _external=True)

        transaction = Transaction()
        response = transaction.create(
            buy_order=buy_order,
            session_id=session_id,
            amount=amount,
            return_url=return_url
        )
        return redirect(f"{response['url']}?token_ws={response['token']}")
    except Exception as e:
        return f"Error al iniciar pago: {str(e)}", 500



@app.route('/respuesta_pago', methods=['GET', 'POST'])
def respuesta_pago():
    token = request.values.get('token_ws')
    if not token:
        return "<script>alert('Error: token_ws no recibido'); window.location.href='/';</script>"

    try:
        transaction = Transaction()
        response = transaction.commit(token)

        if response['status'] == 'AUTHORIZED':
            print("[Transbank] Pago exitoso")
            session['pago_confirmado'] = True
            session['token'] = token
            session['numero_tarjeta'] = response['card_detail']['card_number']
            session['card_detail'] = response['card_detail']
            
            print("response['card_detail']=", response['card_detail'])
            return redirect(url_for('cita_pagada'))
        else:
            print("[Transbank] Pago rechazado:", response)
            return f"<script>alert('Pago rechazado: {response['response_code']}'); window.location.href='/agendar';</script>"
    except Exception as e:
        return f"<script>alert('Error al confirmar pago: {str(e)}'); window.location.href='/agendar';</script>"


@app.route('/cita_pagada')
def cita_pagada():
    print("Variables de sesión en /cita_pagada:")
    for key, value in session.items():  
        print(f"{key}: {value}")    

    if not session.get('pago_confirmado'):
        return "<script>alert('No puedes reservar sin pagar'); window.location.href='/';</script>"
    
    reserva_en_proceso= session.get('reserva_en_proceso')
    user=session.get("user", None)
    print(f"User en cita_pagada= {user}" )
    print(f"correo_cliente_invitado= {session.get('correo_cliente_invitado')}" )
    if (not user) and (not session.get('correo_cliente_invitado')):
         return "<script>alert('No puedes reservar sin pagar'); window.location.href='/';</script>"    #
    elif not session.get('pago_confirmado'):
        return redirect(url_for("finalizar_pago"))
    elif user:
        email=user.get("email")
    else:
        email=session.get('correo_cliente_invitado')

    response, status_code = insert_reservation()

    id_clinica= int(reserva_en_proceso['id_clinica'] )
    fecha= reserva_en_proceso['fecha'] 
    hora= reserva_en_proceso['hora'] 
    id_veterinario= int(reserva_en_proceso['veterinario'] )
    id_mascota= int(session.get('mascotaSeleccionada'))
    token   = session.get('token')
    numero_tarjeta = session.get('numero_tarjeta')

    

    df_clinica = pd.read_csv("data/clinicas.csv", sep=";")
    df_clinica = df_clinica[(df_clinica["id_clinica"] == id_clinica)]
    nombre_clinica = reserva_en_proceso['clinica']     
    direccion_clinica = reserva_en_proceso['direccion'] 
    session['nombre_clinica'] = nombre_clinica
    session['direccion_clinica'] = direccion_clinica
    #si id_mascota != 999
    #si id_mascota es 999, entonces no hay mascota seleccionada
    if (id_mascota != 999 and id_mascota !=0):
        df_mis_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
        df_mis_mascotas = df_mis_mascotas[(df_mis_mascotas["id_clientes_mascotas"] == id_mascota)]
        nombre_mascota = df_mis_mascotas.iloc[0]["nombre_mascota"]
    else:
        nombre_mascota = "Nueva mascota"
    session['nombre_mascota'] = nombre_mascota
    df_veterinario = pd.read_csv("data/staff.csv", sep=";")
    df_veterinario = df_veterinario[(df_veterinario["id_veterinario"] == id_veterinario)]
    nombres_veterinario = reserva_en_proceso['nombresvet'] 
    apellidos_veterinario = reserva_en_proceso['apellidosvet'] 
    session['nombres_veterinario'] = nombres_veterinario
    session['apellidos_veterinario'] = apellidos_veterinario
    
    if status_code == 200:
        limpiar_sesion_parcial()
        return render_template("cita_pagada.html", 
                user=user, 
                correo=email,
                nombre_clinica = nombre_clinica,
                direccion_clinica = direccion_clinica,
                nombre_mascota=nombre_mascota, 
                nombres_veterinario=nombres_veterinario,
                apellidos_veterinario=apellidos_veterinario,
                numero_tarjeta=numero_tarjeta,
                fecha=fecha,
                hora= hora
            )
    else:
        return "<script>alert('La cita ya existe, no recargue la página después de haber pagado.'); window.location.href='/mis_citas';</script>"


@app.route('/api/reservar_cash', methods=['POST'])
def api_reservar_cash():
    try:
        # Forzamos el flujo de efectivo
        session['pago_confirmado'] = False
        session['medio_pago'] = 'EFECTIVO'

        # Llamamos a insert_reservation con argumentos (YA PERMITIDOS)
        resp, status = insert_reservation(estado_pago=0, medio_pago="EFECTIVO")
        if status == 200:
            return jsonify({"ok": True, "redirect": url_for('cita_reservada_cash')}), 200
        else:
            return resp, status
    except Exception as e:
        return jsonify({"message": f"Error al reservar en efectivo: {str(e)}"}), 500


@app.route('/cita_reservada_cash')
def cita_reservada_cash():
    # Puedes reutilizar parte de la lógica de cita_pagada para armar el contexto:
    print("DEBUG: Entrando a cita_reservada_cash")

    reserva_en_proceso = session.get('reserva_en_proceso')
    if not reserva_en_proceso:
        return "<script>alert('No hay reserva en proceso.'); window.location.href='/';</script>"

    user = session.get("user", None)
    if user:
        email = user.get("email")
    else:
        email = session.get('correo_cliente_invitado')

    id_clinica = int(reserva_en_proceso['id_clinica'])
    fecha = reserva_en_proceso['fecha']
    hora = reserva_en_proceso['hora']
    id_veterinario = int(reserva_en_proceso['veterinario'])
    id_mascota = int(session.get('mascotaSeleccionada', 0))
    nombre_clinica = reserva_en_proceso['clinica']
    direccion_clinica = reserva_en_proceso['direccion']

    # nombre_mascota como en cita_pagada
    if (id_mascota != 999 and id_mascota != 0):
        df_mis_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
        df_mis_mascotas = df_mis_mascotas[(df_mis_mascotas["id_clientes_mascotas"] == id_mascota)]
        nombre_mascota = df_mis_mascotas.iloc[0]["nombre_mascota"] if not df_mis_mascotas.empty else "Mascota"
    else:
        nombre_mascota = "Nueva mascota"

    # Veterinario
    nombres_veterinario = reserva_en_proceso.get('nombresvet', '')
    apellidos_veterinario = reserva_en_proceso.get('apellidosvet', '')

    # (Opcional) limpiar sesión parcial como haces en cita_pagada
    # limpiar_sesion_parcial()

    return render_template(
        "cita_reservada_cash.html",
        user=user,
        correo=email,
        nombre_clinica=nombre_clinica,
        direccion_clinica=direccion_clinica,
        nombre_mascota=nombre_mascota,
        nombres_veterinario=nombres_veterinario,
        apellidos_veterinario=apellidos_veterinario,
        fecha=fecha,
        hora=hora
    )


@app.route('/almacenar_precio', methods=['POST'])
def procesar_pago():
    data = request.get_json()
    precio = data.get('precio')
    # almacenamos precio en una variable de sesion
    session['precio'] = precio
    print("Precio recibido:", precio)

    # Aquí podrías crear la transacción y devolver la URL de pago
    return jsonify({"mensaje": "recibido", "precio": precio})





@app.route('/almacenar_mascota', methods=['POST'])
def almacenar_mascota():
    data = request.get_json()
    mascotaSeleccionada = data.get('mascotaSeleccionada')
    # almacenamos precio en una variable de sesion
    session['mascotaSeleccionada'] = mascotaSeleccionada
    print("mascotaSeleccionada recibida:", mascotaSeleccionada)

    # Aquí podrías crear la transacción y devolver la URL de pago
    return jsonify({"mensaje": "recibido", "mascotaSeleccionada": mascotaSeleccionada})



@app.route('/generar_pdf', methods=['GET', 'POST'])
def generar_pdf():
    reserva = session.get('reserva_en_proceso')
    nombre_mascota = session.get('nombre_mascota', '')

    cargoServicio = int(session.get('cargoServicio', 0))
    cargoServicio = f"${cargoServicio:,}".replace(",", ".")
    cargoTotal = int(session.get('cargoTotal', 0))
    cargoTotal = f"${cargoTotal:,}".replace(",", ".")   
    precio = int(reserva['valor'])
    precio = f"${precio:,}".replace(",", ".")     

    numero_tarjeta = session.get('numero_tarjeta')
    hora = session.get('hora', '08:40')
    id_reserva = session.get('max_id_reserva')
    print(f"En generar PDF id_reserva={id_reserva}")
    id_reserva = int(id_reserva) + 1
    cliente = session.get('nombre_cliente', 'Estimado/a Cliente')

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    x_margin = inch
    y = height - inch


    # === ENCABEZADO CON FONDO CELESTE ===
    alto_encabezado = 80
    y_encabezado = height - alto_encabezado

    c.setFillColorRGB(0.87, 0.94, 0.98)  # celeste suave
    c.rect(0, y_encabezado, width, alto_encabezado, fill=True, stroke=0)

    # Logo dentro del encabezado
    c.drawImage(
        "static/images/icono paw care/android-chrome-192x192.png",
        x_margin,
        y_encabezado + 10,
        width=60,
        height=60,
        preserveAspectRatio=True,
        mask='auto'
    )

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(x_margin + 120, y+20, "PawCare")

    # Actualizar posición de Y para el resto del contenido
    y = y_encabezado - 30  # bajar contenido general bajo el encabezado

    ##==== CUERPO ===
    # Título
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    texto = "Confirmación de reserva"
    x_centro = width / 2
    y_texto = y

    # Dibujar el texto centrado
    c.drawCentredString(x_centro, y_texto, texto)

    # Calcular ancho del texto para subrayado
    ancho_texto = c.stringWidth(texto, "Helvetica-Bold", 16)
    x_inicio = x_centro - (ancho_texto / 2)
    x_final = x_centro + (ancho_texto / 2)
    y_linea = y_texto - 2  # 2 puntos debajo del texto

    # Dibujar la línea de subrayado
    c.setLineWidth(1)
    c.line(x_inicio, y_linea, x_final, y_linea)

    y -= 40

    # Cuerpo del mensaje
    c.setFont("Helvetica", 12)
    c.drawString(x_margin, y, f"{cliente},")
    y -= 20

    c.drawString(x_margin, y, f"Su cita se agendó correctamente con el/la especialista: {reserva['nombresvet']} {reserva['apellidosvet']}.")
    y -= 20
    #c.setFont("Helvetica-Bold", 12)
    #c.drawString(x_margin, y, f"Dr. {reserva['nombresvet']}")
    #y -= 20

    c.setFont("Helvetica", 12)
    c.drawString(x_margin, y, f"El día {reserva['fecha']} a las {reserva['hora']} horas.")
    y -= 20
    c.drawString(x_margin, y, f"En el centro de atención: {reserva['clinica']}.")
    y -= 20
    c.drawString(x_margin, y, f"Dirección: {reserva['direccion']}, {reserva['comuna']}.")
    y -= 30

    # Detalles
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Nº de reserva:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, f"{id_reserva}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Valor pagado:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, f"{cargoTotal}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Cargo por servicio pagado:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, f"{cargoServicio}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Valor de la consulta:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, f"{precio}")
    y -= 20    

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Tarjeta utilizada terminada en:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, numero_tarjeta)
    y -= 40

    # Recomendaciones
    c.setFont("Helvetica", 12)
    c.drawString(x_margin, y, "Le solicitamos llegar 20 minutos antes de la hora de su cita para una mejor atención.")
    y -= 30

    c.drawString(x_margin, y, "Agradecemos su preferencia en nuestros servicios.")
    y -= 40
    
    c.drawString(x_margin, y, "Atentamente,")
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "El equipo de PawCare")
    y -= 60

    # Línea separadora
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.line(x_margin, y, width - x_margin, y)
    y -= 25

        # === PIE CON FONDO CELESTE ===
    alto_pie = 110
    y_pie = 0
    c.setFillColorRGB(0.87, 0.94, 0.98)  # celeste suave
    c.rect(0, y_pie, width, alto_pie, fill=True, stroke=0)

    # Texto del encabezado del pie
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y_pie + alto_pie - 20, "Si tienes alguna pregunta o requieres asistencia adicional, contáctanos")

    # Subtítulos
    c.setFont("Helvetica", 12)
    c.drawString(x_margin, y_pie + alto_pie - 50, "Teléfono")
    c.drawString(x_margin + 120, y_pie + alto_pie - 50, "Dirección")
    c.drawString(x_margin + 420, y_pie + alto_pie - 50, "Síguenos en")

    # Datos
    c.drawString(x_margin, y_pie + alto_pie - 70, "2 2520 5900")
    c.drawString(x_margin + 120, y_pie + alto_pie - 70, "Av. Luis Pasteur 5917. Vitacura")

    # Redes sociales
    redes = [
        ("facebook.png", "https://www.facebook.com/pawcare_oficial"),
        ("instagram.png", "https://www.instagram.com/pawcare_oficial"),
        ("x.png", "https://twitter.com/pawcare_oficial")
    ]
    x_icon = x_margin + 400
    y_icon = y_pie + alto_pie - 90  # alineado con texto

    for icon_file, url in redes:
        icon_path = f"static/images/social/{icon_file}"
        c.linkURL(url, (x_icon, y_icon, x_icon + 32, y_icon + 32))
        c.drawImage(icon_path, x_icon, y_icon, width=32, height=32, mask='auto')
        x_icon += 40  # espacio entre íconos

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reserva_cita.pdf",
        mimetype="application/pdf"
    )


@app.route('/generar_pdf_cash', methods=['GET', 'POST'])
def generar_pdf_cash():
    reserva = session.get('reserva_en_proceso')
    nombre_mascota = session.get('nombre_mascota', '')

    cargoServicio = int(session.get('cargoServicio', 0))
    cargoServicio = f"${cargoServicio:,}".replace(",", ".")
    cargoTotal = 0 #en pago cash so se cobra el cargo por servicio
    cargoTotal = f"${cargoTotal:,}".replace(",", ".")   
    precio = int(reserva['valor'])
    precio = f"${precio:,}".replace(",", ".")     

    numero_tarjeta = "N/A"
    hora = session.get('hora', '08:40')
    id_reserva = session.get('max_id_reserva')
    print(f"En generar PDF id_reserva={id_reserva}")
    id_reserva = int(id_reserva) + 1
    cliente = session.get('nombre_cliente', 'Estimado/a Cliente')

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    x_margin = inch
    y = height - inch


    # === ENCABEZADO CON FONDO CELESTE ===
    alto_encabezado = 80
    y_encabezado = height - alto_encabezado

    c.setFillColorRGB(0.87, 0.94, 0.98)  # celeste suave
    c.rect(0, y_encabezado, width, alto_encabezado, fill=True, stroke=0)

    # Logo dentro del encabezado
    c.drawImage(
        "static/images/icono paw care/android-chrome-192x192.png",
        x_margin,
        y_encabezado + 10,
        width=60,
        height=60,
        preserveAspectRatio=True,
        mask='auto'
    )

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(x_margin + 120, y+20, "PawCare")

    # Actualizar posición de Y para el resto del contenido
    y = y_encabezado - 30  # bajar contenido general bajo el encabezado

    ##==== CUERPO ===
    # Título
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    texto = "Confirmación de reserva"
    x_centro = width / 2
    y_texto = y

    # Dibujar el texto centrado
    c.drawCentredString(x_centro, y_texto, texto)

    # Calcular ancho del texto para subrayado
    ancho_texto = c.stringWidth(texto, "Helvetica-Bold", 16)
    x_inicio = x_centro - (ancho_texto / 2)
    x_final = x_centro + (ancho_texto / 2)
    y_linea = y_texto - 2  # 2 puntos debajo del texto

    # Dibujar la línea de subrayado
    c.setLineWidth(1)
    c.line(x_inicio, y_linea, x_final, y_linea)

    y -= 40

    # Cuerpo del mensaje
    c.setFont("Helvetica", 12)
    c.drawString(x_margin, y, f"{cliente},")
    y -= 20

    c.drawString(x_margin, y, f"Su cita se agendó correctamente con el/la especialista: {reserva['nombresvet']} {reserva['apellidosvet']}.")
    y -= 20
    #c.setFont("Helvetica-Bold", 12)
    #c.drawString(x_margin, y, f"Dr. {reserva['nombresvet']}")
    #y -= 20

    c.setFont("Helvetica", 12)
    c.drawString(x_margin, y, f"El día {reserva['fecha']} a las {reserva['hora']} horas.")
    y -= 20
    c.drawString(x_margin, y, f"En el centro de atención: {reserva['clinica']}.")
    y -= 20
    c.drawString(x_margin, y, f"Dirección: {reserva['direccion']}, {reserva['comuna']}.")
    y -= 30

    # Detalles
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Nº de reserva:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, f"{id_reserva}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Valor pagado:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, f"{cargoTotal}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Cargo por servicio pagado:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, f"{cargoServicio}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Valor de la consulta:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, f"{precio}")
    y -= 20    

    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "Tarjeta utilizada terminada en:")
    c.setFont("Helvetica", 12)
    c.drawString(x_margin + 180, y, numero_tarjeta)
    y -= 40

    # Recomendaciones
    c.setFont("Helvetica", 12)
    c.drawString(x_margin, y, "Le solicitamos llegar 20 minutos antes de la hora de su cita para una mejor atención.")
    y -= 30

    c.drawString(x_margin, y, "Agradecemos su preferencia en nuestros servicios.")
    y -= 40
    
    c.drawString(x_margin, y, "Atentamente,")
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y, "El equipo de PawCare")
    y -= 60

    # Línea separadora
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.line(x_margin, y, width - x_margin, y)
    y -= 25

        # === PIE CON FONDO CELESTE ===
    alto_pie = 110
    y_pie = 0
    c.setFillColorRGB(0.87, 0.94, 0.98)  # celeste suave
    c.rect(0, y_pie, width, alto_pie, fill=True, stroke=0)

    # Texto del encabezado del pie
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x_margin, y_pie + alto_pie - 20, "Si tienes alguna pregunta o requieres asistencia adicional, contáctanos")

    # Subtítulos
    c.setFont("Helvetica", 12)
    c.drawString(x_margin, y_pie + alto_pie - 50, "Teléfono")
    c.drawString(x_margin + 120, y_pie + alto_pie - 50, "Dirección")
    c.drawString(x_margin + 420, y_pie + alto_pie - 50, "Síguenos en")

    # Datos
    c.drawString(x_margin, y_pie + alto_pie - 70, "2 2520 5900")
    c.drawString(x_margin + 120, y_pie + alto_pie - 70, "Av. Luis Pasteur 5917. Vitacura")

    # Redes sociales
    redes = [
        ("facebook.png", "https://www.facebook.com/pawcare_oficial"),
        ("instagram.png", "https://www.instagram.com/pawcare_oficial"),
        ("x.png", "https://twitter.com/pawcare_oficial")
    ]
    x_icon = x_margin + 400
    y_icon = y_pie + alto_pie - 90  # alineado con texto

    for icon_file, url in redes:
        icon_path = f"static/images/social/{icon_file}"
        c.linkURL(url, (x_icon, y_icon, x_icon + 32, y_icon + 32))
        c.drawImage(icon_path, x_icon, y_icon, width=32, height=32, mask='auto')
        x_icon += 40  # espacio entre íconos

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reserva_cita.pdf",
        mimetype="application/pdf"
    )


@app.route('/enviar-cita-calendario', methods=['POST'])
def enviar_cita_calendario():
    # Variables desde sesión
    reserva_en_proceso = session.get('reserva_en_proceso')
    user=session.get('user')
    direccion = reserva_en_proceso['direccion']
    correo = user['email']
    fecha = reserva_en_proceso['fecha']  # formato: YYYY-MM-DD
    hora = reserva_en_proceso['hora']  # formato: HH:MM
    print(f"Datos recibidos en enviar_cita_calendario: {direccion}, {correo}, {fecha}, {hora}")
    if not all([direccion, correo, fecha, hora]):
        return jsonify({"success": False, "message": "Faltan datos"}), 400

    # Construir datetime con zona horaria
    timezone = "America/Santiago"
    start_str = f"{fecha}T{hora}"  # hora debería ser: "10:00:00" o "10:00"
    print(f"[DEBUG_1] fecha={fecha}, hora={hora}, start_str={start_str}")
    try:
        # intenta con segundos
        start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        # si falla, intenta sin segundos
        start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
    start = pytz.timezone(timezone).localize(start)
    print(f"[DEBUG_2] fecha={fecha}, hora={hora}, start_str={start_str}, , start={start}")
    end = start + timedelta(hours=1)

    # Autenticación con servicio
    credentials_path = os.path.join('static', 'credenciales_pawcare_calendar.json')  # ajusta si está en otra carpeta
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/calendar']
    )

    service = build('calendar', 'v3', credentials=credentials)

    event = {
        'summary': 'Cita en clinica veterinaria',
        'location': direccion,
        'description': 'Reserva automática realizada desde PawCare.',
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': timezone,
        },
        'attendees': [{'email': correo}],
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'email', 'minutes': 60 * 24}]
        }
    }

    calendar_id = 'primary'  # o el ID de un calendario específico
    created_event = service.events().insert(calendarId=calendar_id, body=event, sendUpdates='all').execute()

    return jsonify({"success": True, "correo": correo})

@app.route('/api/seleccion_guardada')
def seleccion_guardada():
    return jsonify({
        "id_veterinario": session.get("id_veterinario"),
        "fechaSeleccionada": session.get("fechaSeleccionada"),
        "horaSeleccionada": session.get("horaSeleccionada")
    })


@app.route("/actualizar_peso_mascota", methods=["POST"])
def actualizar_peso_mascota():
    data = request.get_json()
    id_mascota = int(data.get("id_mascota"))
    nuevo_peso = float(data.get("nuevo_peso"))

    df = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    if id_mascota in df["id_clientes_mascotas"].values:
        df.loc[df["id_clientes_mascotas"] == id_mascota, "peso"] = nuevo_peso
        df.to_csv("data/clientes_mascotas.csv", index=False, sep=";")
        return jsonify(success=True)
    else:
        return jsonify(success=False), 404


@app.route("/subir_foto_mascota", methods=["POST"])
def subir_foto_mascota():
    if "foto" not in request.files or "id_mascota" not in request.form:
        return jsonify(success=False), 400

    archivo = request.files["foto"]
    id_mascota = request.form["id_mascota"]

    if archivo.filename == "":
        return jsonify(success=False), 400

    ruta_destino = os.path.join("static", "images", "mascotas", f"m_{id_mascota}.jpg")
    archivo.save(ruta_destino)
    return jsonify(success=True)


@app.route("/descarga_diagnostico/<int:id_cita>")
def descarga_diagnostico(id_cita):
    # Leer datos desde los archivos CSV
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    df_staff = pd.read_csv("data/staff.csv", sep=";")
    df_clinicas = pd.read_csv("data/clinicas.csv", sep=";")

    # Obtener la cita
    cita = df_reservas[df_reservas["id_reserva"] == id_cita].iloc[0]
    id_mascota = cita["mascota"]
    id_veterinario = cita["medico_que_atendio"]
    #Pasamos id_veterinario a entero sin decimales
    id_veterinario = int(id_veterinario)
    id_clinica = cita["id_clinica"]

    mascota = df_mascotas[df_mascotas["id_clientes_mascotas"] == id_mascota].iloc[0]
    vet = df_staff[df_staff["id_veterinario"] == id_veterinario].iloc[0]
    clinica = df_clinicas[df_clinicas["id_clinica"] == id_clinica].iloc[0]

    # Crear PDF en memoria
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    # Margen izquierdo y derecho: 2cm
    margen_izq = 2 * cm
    margen_der = width - 2 * cm

    # Insertar imagen
    img_path = os.path.join("static", "images", "cabecera_diagnostico.png")
#dibujamos img_path con un ancho de 592px y 61px de alto, centrado en la hoja
    #c.drawImage(img_path, 0, height - 2 * cm - 50, width=width, height=61, mask='auto')


    c.drawImage(img_path, margen_izq - 2 * cm, height - 2 * cm - 50, width=width, height=51, preserveAspectRatio=True, mask='left')

    # Dejar espacio: 3 cm debajo de imagen
    y = height - 2 * cm - 50 - 3 * cm

    # Dibujar tabla
    datos = [
        ("Nombre paciente", mascota["nombre_mascota"]),
        ("Fecha de atención", cita["fecha"]),
        ("Veterinario", f"{vet['nombres']} {vet['apellidos']}"),
        ("Clínica", clinica["nombre"]),
        ("Diagnóstico", cita["diagnostico"])
    ]

    row_height = 20
    col1_width = 3 * cm
    col2_width = width - 4 * cm - col1_width  # margen izq y der incluidos

    for label, valor in datos:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margen_izq, y, label)
        c.setFont("Helvetica", 10)
        c.drawString(margen_izq + col1_width + 0.5 * cm, y, str(valor))
        c.setStrokeColorRGB(0.7, 0.7, 0.7)  # gris claro
        c.line(margen_izq, y - 5, margen_der, y - 5)
        y -= row_height

    # Dejar 2 cm de espacio antes del mensaje final
    y -= 2 * cm
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(margen_izq, y, "Atte., el equipo de PawCare")

    c.showPage()
    c.save()
    buffer.seek(0)

    filename = f"diagnostico_{id_cita}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@app.route('/api/especies')
def api_especies():
    df = pd.read_csv('data/especies.csv', sep=";")
    return jsonify(df.to_dict(orient='records'))


@app.route("/api/razas_por_especie/<int:id_especie>")
def razas_por_especie(id_especie):
    try:
        df = pd.read_csv('data/especie_raza.csv', sep=";")
        df_filtrado = df[df["id_especie"] == id_especie]
        df_razas = pd.read_csv('data/razas.csv', sep=";")

        df_filtrado = df_filtrado.merge(
            df_razas[['id_raza', 'nombre_raza']],
            left_on="id_raza",
            right_on="id_raza",
            how="left"
        )
        df_filtrado['nombre_raza'] = df_filtrado['nombre_raza'].str.title()
        df_filtrado = df_filtrado.sort_values(by='nombre_raza', ascending=True)
        razas = df_filtrado["nombre_raza"].dropna().unique().tolist()
        return jsonify(razas)
    except Exception as e:
        return jsonify([]), 500


@app.route('/api/razas')
def api_razas():
    id_especie = request.args.get('id_especie')
    print("[DEBUG] id_especie:", id_especie)
    especie_raza = pd.read_csv('data/especie_raza.csv', sep=";")
    # Filtramos df_join por id_especie
    if not id_especie:
        return jsonify({"error": "id_especie is required"}), 400
    especie_raza = especie_raza[especie_raza['id_especie'] == int(id_especie)]

    df_razas = pd.read_csv('data/razas.csv', sep=";")

    especie_raza = especie_raza.merge(
        df_razas[['id_raza', 'nombre_raza']],
        left_on="id_raza",
        right_on="id_raza",
        how="left"
    )
    #ordenamos especie_raza por el campo nombre_raza de la a a la z
    especie_raza = especie_raza.sort_values(by='nombre_raza', ascending=True)
    #ponemos en mayúscula la primera letra de cada palabra del campo nombre_raza
    especie_raza['nombre_raza'] = especie_raza['nombre_raza'].str.title()

    print("[DEBUG] especie_raza:", especie_raza)
    #ids = df_join[df_join['id_especie'] == int(id_especie)]['id_raza']
    #razas = df_razas[df_razas['id_raza'].isin(ids)]
    return jsonify(especie_raza.to_dict(orient='records'))

@app.route('/api/sesion/nueva_mascota', methods=['POST'])
def guardar_nueva_mascota():
    datos = request.get_json()
    campo = datos['campo']
    valor = datos['valor']
    if 'nueva_mascota' not in session:
        session['nueva_mascota'] = {}
    session['nueva_mascota'][campo] = valor
    session.modified = True
    #imprimir todo el contenido de session['nueva_mascota']
    print("[DEBUG] Nueva mascota en sesión:", session['nueva_mascota'])
    return jsonify({"estado": "ok"})

@app.route('/api/crea_variable_sesion_mascota', methods=['POST'])
def crea_variable_sesion_mascota():
    datos = request.get_json()
    if 'crear_nueva_mascota' not in session:
        session['crear_nueva_mascota'] = datos['crear_mascota']
    session.modified = True
    #imprimir todo el contenido de session['nueva_mascota']
    print("[DEBUG] crear_nueva_mascota:", session['crear_nueva_mascota'])
    return jsonify({"estado": "ok"})


@app.route("/api/agenda/<int:id_veterinario>")
def obtener_agenda(id_veterinario):
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], dayfirst=True, errors="coerce")
    hoy = pd.to_datetime(datetime.today().date())

    df_filtradas = df_reservas[
        (df_reservas["medico_que_atendio"] == id_veterinario) &
        (df_reservas["fecha"] >= hoy)
    ]

    df_filtradas["fecha"] = df_filtradas["fecha"].dt.strftime("%d/%m/%Y")
    df_filtradas["hora"] = pd.to_datetime(df_filtradas["hora"], errors="coerce").dt.strftime("%H:%M")

    return jsonify(df_filtradas.to_dict(orient="records"))


@app.route("/ficha_mascotas", methods=["GET", "POST"])
def ficha_mascotas():
    session['next'] = request.full_path
    print(f"[INFO] next pawcarepro: {request.full_path}")
    user = session.get("user", None)

    print(session.get("user"))
    if not user:
        return redirect(url_for("login"))    
    email=user.get("email")
    df_veterinario = pd.read_csv("data/staff.csv", sep=";")
    df_veterinario = df_veterinario[(df_veterinario["correo"] == email)]
    #si df_vaterinario está vacío, entonces redirigimos a la página de inicio de sesión
    if df_veterinario.empty:
        print("[ERROR] No se encontró el veterinario en el staff")
        return redirect(url_for("login"))
    #print(f"[INFO] Datos del veterinario:")
    #print(f"{df_veterinario}")
    id_veterinario = df_veterinario["id_veterinario"].values[0]
    del df_veterinario
    session["id_veterinario"] = id_veterinario


    mascota = request.args.get("mascota")
    id_reserva = request.args.get("id_reserva")

    if request.method == "POST":
        print(f"[DEBUG] Datos recibidos en ficha_mascotas: {request.form}")
        datos = {
            "mascota": int(request.form["mascota"]),
            "id_reserva": request.form["id_reserva"],
            "frecuencia_cardiaca": request.form.get("frecuencia_cardiaca"),
            "frecuencia_respiratoria": request.form.get("frecuencia_respiratoria"),
            "temperatura": request.form.get("temperatura"),
            "peso": request.form.get("peso"),
            "razon_consulta": request.form.get("razon_consulta"),
            "epicrisis": request.form.get("epicrisis"),
            "observaciones": request.form.get("observaciones"),
            "fecha": pd.to_datetime(datetime.today().date()).strftime("%d-%m-%Y"),  # Formato dd-mm-YYYY
            #en la variable hora almacenamos la hora actual en formato HH:MM
            "hora": pd.to_datetime(datetime.now()).strftime("%H:%M"),  # Formato HH:MM

            "medico": id_veterinario
        }
        print(f"[DEBUG] Datos a guardar: {datos}")

        #si id_reserva no existe en ficha_mascotas.csv, entonces insertamos una nueva fila con los valores de datos
        df_ficha_mascotas = pd.read_csv("data/ficha_mascotas.csv", sep=";")
        #df_ficha_mascotas["id_reserva"] = df_ficha_mascotas["id_reserva"].astype(str)  # Aseguramos que id_reserva sea str
        if int(request.form["id_reserva"]) not in df_ficha_mascotas["id_reserva"].values:
            # Si no existe, agregamos una nueva fila
            df_ficha_mascotas = df_ficha_mascotas._append(datos, ignore_index=True)
            print(f"[DEBUG] Se agregó una nueva fila a ficha_mascotas.csv con id_reserva: {datos['id_reserva']}")
        else:
            # Si existe, actualizamos la fila correspondiente
            df_ficha_mascotas.loc[df_ficha_mascotas["id_reserva"] == int(datos["id_reserva"]), datos.keys()] = datos.values()   
            print(f"[DEBUG] Se actualizó la fila en ficha_mascotas.csv con id_reserva: {datos['id_reserva']}")

        # Guardar en el CSV
        with open("data/ficha_mascotas.csv", "a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=datos.keys(), delimiter=";")
            if f.tell() == 0:  # Si el archivo está vacío, escribe el encabezado
                writer.writeheader()
            writer.writerow(datos)

        return redirect(url_for("pawcarepro"))

        # Buscar el nombre de la mascota
    df_mis_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    # Aseguramos que la columna también sea tipo entero
    df_mis_mascotas["id_clientes_mascotas"] = df_mis_mascotas["id_clientes_mascotas"].astype(int)
    mascota=int(mascota)
    print(f"[DEBUG] df_mis_mascotas_1: {df_mis_mascotas.head()}")
    df_mis_mascotas = df_mis_mascotas[(df_mis_mascotas["id_clientes_mascotas"] == mascota)]
    print(f"[DEBUG] df_mis_mascotas_2: {df_mis_mascotas.head()}")
    
    print(f"[DEBUG] Buscando mascota: {mascota}")
    
    name_mascota = df_mis_mascotas.iloc[0]["nombre_mascota"] if not df_mis_mascotas.empty else "Mascota no encontrada"

    df_fichas = pd.read_csv("data/ficha_mascotas.csv", sep=";")
    #asignamos a peso, el valor de peso de la mascota donde id_reserva sea el mayor para mascota=mascota
    df_fichas["mascota"] = df_fichas["mascota"].astype(int)
    df_fichas_mascota = df_fichas[(df_fichas["mascota"] == int(mascota))]
    #buscamos el peso de la mascota si df_fichas no está vacío
    print(f"[DEBUG] Buscando fichas para la mascota: {mascota}")

    if not df_fichas_mascota.empty:
        #ordemanos df_fichas por id_reserva de forma descendente
        df_fichas_mascota = df_fichas_mascota.sort_values(by="id_reserva", ascending=False)
        #obtenemos el peso de la última reserva
        peso = df_fichas_mascota.iloc[0]["peso"]   
        
    else:
        #obtenemos el peso de la mascota desde df_mis_mascotas
        print(f"[DEBUG] No se encontraron fichas para la mascota {mascota}, obteniendo peso desde df_mis_mascotas")
        peso = df_mis_mascotas.iloc[0]["peso"]
    
    #Vemos si ya existe la reserva en las fichas, si es así, entonces el veterinario 
    #está actualizando los datos de la ficha de esa reserva
    df_fichas_reserva = df_fichas[(df_fichas["id_reserva"] == int(id_reserva))]
    frecuencia_cardiaca = None
    frecuencia_respiratoria = None
    temperatura = None
    razon_consulta = None
    epicrisis = None
    observaciones = None
    peso_ficha = None
    
    # Si hay una reserva, obtenemos los datos de la ficha
    if not df_fichas_reserva.empty: 
        frecuencia_cardiaca = df_fichas_reserva.iloc[0]["frecuencia_cardiaca"]
        frecuencia_respiratoria = df_fichas_reserva.iloc[0]["frecuencia_respiratoria"]
        temperatura = df_fichas_reserva.iloc[0]["temperatura"]
        razon_consulta = df_fichas_reserva.iloc[0]["razon_consulta"]
        epicrisis = df_fichas_reserva.iloc[0]["epicrisis"]
        observaciones = df_fichas_reserva.iloc[0]["observaciones"]
        peso_ficha = df_fichas_reserva.iloc[0]["peso"]
    del df_fichas_reserva
    del df_fichas
    del df_fichas_mascota


    print(f"[DEBUG] Peso de la mascota: {peso}")
    
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas = df_reservas[(df_reservas["id_reserva"] == int(id_reserva))]
    id_veterinario = df_reservas.iloc[0]["medico_que_atendio"]
    df_veterinario = pd.read_csv("data/staff.csv", sep=";")
    df_veterinario = df_veterinario[(df_veterinario["id_veterinario"] == id_veterinario)]
    datos_veterinario = df_veterinario.to_dict(orient="records")
    del df_veterinario

    id_especie_raza= df_mis_mascotas.iloc[0]["id_especie_raza"]
    df_especie_raza = pd.read_csv("data/especie_raza.csv", sep=";")
    df_especie_raza = df_especie_raza[(df_especie_raza["id_especie_raza"] == id_especie_raza)]
    id_especie = df_especie_raza.iloc[0]["id_especie"]
    df_especies = pd.read_csv("data/especies.csv", sep=";")
    df_especies = df_especies[(df_especies["id_especie"] == id_especie)]
    especie = df_especies.iloc[0]["especie"] if not df_especies.empty else "Especie no encontrada"
    print(f"[DEBUG] Especie encontrada: {especie}")
    id_raza = df_especie_raza.iloc[0]["id_raza"]
    df_razas = pd.read_csv("data/razas.csv", sep=";")
    df_razas = df_razas[(df_razas["id_raza"] == id_raza)]
    raza = df_razas.iloc[0]["nombre_raza"] if not df_razas.empty else "Raza no encontrada"
    print(f"[DEBUG] Raza encontrada: {raza}")

    del df_especies
    del df_especie_raza
    del df_razas
    del df_mis_mascotas
    del df_reservas

    print(f"[DEBUG] Nombre de la mascota: {name_mascota}")
    return render_template("ficha_mascotas.html", 
                           mascota=mascota, 
                           id_reserva=id_reserva, 
                           nombre_mascota=name_mascota, 
                           datos_veterinario=datos_veterinario, 
                           especie=especie, 
                           raza=raza, 
                           peso=peso, 
                           peso_ficha=peso_ficha,
                           frecuencia_cardiaca=frecuencia_cardiaca, 
                           frecuencia_respiratoria=frecuencia_respiratoria, 
                           temperatura=temperatura, 
                           razon_consulta=razon_consulta, 
                           epicrisis=epicrisis, 
                           observaciones=observaciones, 
                           user=user)

# 📌 Ruta de Ayuda
@app.route("/ayuda")
#@login_required
def ayuda():
    user = session.get("user", None)

    return render_template("ayuda.html", user=user)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/subir_certificado', methods=['POST'])
def subir_certificado():
    if 'user' not in session:
        return jsonify(success=False, error="No autenticado"), 403

    email = session['user']['email']
    nombre_certificado = request.form.get('nombre_certificado')
    archivo = request.files.get('archivo')

    if not nombre_certificado or not archivo:
        return jsonify(success=False, error="Datos incompletos"), 400

    if archivo and allowed_file(archivo.filename):
        nombre_archivo = secure_filename(archivo.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_guardado = f"{email}_{timestamp}_{nombre_archivo}"
        ruta = os.path.join(app.config['UPLOAD_FOLDER'], nombre_guardado)
        archivo.save(ruta)

        # Guardar en CSV
        nueva_fila = pd.DataFrame([{
            "email_usuario": email,
            "nombre_certificado": nombre_certificado,
            "nombre_archivo": nombre_guardado,
            "fecha_subida": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])

        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE, sep=';')
            df = pd.concat([df, nueva_fila], ignore_index=True)
        else:
            df = nueva_fila

        df.to_csv(CSV_FILE, index=False, sep=';', encoding='utf-8')
        return jsonify(success=True)
    else:
        return jsonify(success=False, error="Formato de archivo no permitido"), 400

@app.route("/api/obtener_dpa", methods=["GET"])
def obtener_dpa():
    nombre_comuna = request.args.get("nombre_comuna", "").strip().lower()
    print("[DEBUG] Nombre de comuna recibido obtener_dpa:", nombre_comuna)

    if not nombre_comuna:
        return jsonify({"error": "Nombre de comuna no especificado"}), 400

    try:
        df_dpa = pd.read_csv("data/dpa.csv", sep=";")

        df_dpa["Nombre_Comuna"] = df_dpa["Nombre_Comuna"].str.lower()
        print("[DEBUG] DataFrame df_dpa:", df_dpa)
        fila = df_dpa[df_dpa["Nombre_Comuna"] == nombre_comuna]

        if fila.empty:
            return jsonify({"error": "Comuna no encontrada"}), 404

        id_dpa = int(fila.iloc[0]["Comuna"])
        print("[DEBUG] ID DPA encontrado:", id_dpa)
        return jsonify({"id_dpa": id_dpa})
        #return id_dpa

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/obtener_comuna/<int:id_dpa>")
def obtener_nombre_comuna(id_dpa):
    try:
        print(f"[DEBUG] Obteniendo comuna para id_dpa: {id_dpa}")
        df_dpa = pd.read_csv("data/dpa.csv", sep=";")
        
        df_dpa = df_dpa.dropna(subset=["id_dpa", "Nombre_Comuna"])
        print("df_dpa:", df_dpa)
        resultado = df_dpa[df_dpa["id_dpa"] == id_dpa]

        if not resultado.empty:
            nombre_comuna = resultado.iloc[0]["Nombre_Comuna"]
            return jsonify({"nombre_comuna": nombre_comuna})
        else:
            return jsonify({"error": "Comuna no encontrada"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 📌 Ruta de agendar
@app.route("/reservar")
def reservar():


    return render_template("reservar.html", user=session.get("user", None), next=session.get("next", None))


# Cargar plantilla HTML desde archivo
def cargar_plantilla():
    with open("templates/plantilla_correo_reserva.html", "r", encoding="utf-8") as f:
        return f.read()

# Enviar correo
def enviar_correo_reserva(destinatario, datos):
    # Datos dinámicos para el correo
    html_template = cargar_plantilla()
    cuerpo_html = render_template_string(html_template, **datos)

    msg = Message(
            subject="Confirmación de reserva - PawCare",
            sender="alhen1970@gmail.com",
            recipients=[destinatario],
            html=cuerpo_html
        )

    try:
        mail.send(msg)
        print("Correo enviado correctamente.")
    except Exception as e:
        print("Error al enviar el correo:", e)


@app.route('/api/especies')
def obtener_especies():
    especies = []
    with open('data/species.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            especies.append({
                'id_especie': row['id_especie'],
                'especie': row['especie'],
                'icono': row['icono']
            })
    return jsonify(especies)


@app.route('/api/especie_raza')
def especie_raza():
    razas_df = pd.read_csv("data/razas.csv", sep=";")
    especie_raza_df = pd.read_csv("data/especie_raza.csv", sep=";")


    # 1. A veterinario_especialidades_df le unimos los datos del veterinario
    especie_raza_df = especie_raza_df.merge(
        razas_df[["id_raza", "nombre_raza"]],
        left_on="id_raza",
        right_on="id_raza",
        how="left"    
    )

    resultado = especie_raza_df[[
        "id_especie", "id_raza", "nombre_raza"
    ]].to_dict(orient="records")

    return jsonify(resultado)


#Fetch que recibe el correo del cliente y retorna sus mascotas
@app.route('/api/clientes_mascotas_por_correo', methods=['POST'])
def clientes_mascotas_por_correo():
    data = request.get_json()
    correo = data.get('correo')

    if not correo:
        return jsonify({'error': 'Correo no proporcionado'}), 400

    clientes_mascotas_df = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    clientes_mascotas_df = clientes_mascotas_df[clientes_mascotas_df['correo_cliente']==correo]
    print("clientes_mascotas_df:" , clientes_mascotas_df)

    resultados = clientes_mascotas_df[[
        "id_clientes_mascotas", "correo_cliente", "nombre_mascota"
    ]].to_dict(orient="records")
    print("Resultados:", resultados)

    return jsonify({'clientes_mascotas': resultados})




@app.route('/api/enviar_rcaptcha', methods=['POST'])
def enviar_rcaptcha():
    data = request.get_json()
    recaptcha_token = data.get('recaptcha_token')
    print("recaptcha_token recibido", recaptcha_token)

    if not recaptcha_token:
        print("no recaptcha_token recibido")
        return jsonify({'error': 'Token reCAPTCHA no enviado'}), 400

    secret_key = "6LfZ0YwrAAAAABVknM9pNQlgcOADOnyKFFLyrEdW"
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': secret_key,
            'response': recaptcha_token
        }
    )

    result = response.json()

    if not result.get('success') or result.get('score', 1) < 0.5:
        return jsonify({'error': 'Falló reCAPTCHA'}), 403



    return jsonify({'mensaje': 'Formulario recibido correctamente'})


@app.route('/api/enviar_rcaptcha_login', methods=['POST'])
def enviar_rcaptcha_login():
    data = request.get_json()
    recaptcha_token = data.get('recaptcha_token')
    print("recaptcha_token recibido", recaptcha_token)

    if not recaptcha_token:
        print("no recaptcha_token recibido")
        return jsonify({'error': 'Token reCAPTCHA no enviado'}), 400

    secret_key = "6LfZ0YwrAAAAABVknM9pNQlgcOADOnyKFFLyrEdW"
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': secret_key,
            'response': recaptcha_token
        }
    )

    result = response.json()

    if not result.get('success') or result.get('score', 1) < 0.5:
        return jsonify({'error': 'Falló reCAPTCHA'}), 403

    #Validamos al usuario
    df_usuarios = pd.read_csv("data/usuarios.csv", sep=";")
    print(f"df_usuarios={df_usuarios}")
    correo = data.get('correo')
    password = data.get('password')
    password = str(password)
    print(f"correo={correo} y contr={password}")
    df_usuarios_filtrado=df_usuarios[
        (df_usuarios['correo_cliente']== correo) &
        (df_usuarios['contrasenia']== password)]   
    
    print(f"df_usuarios_filtrado={df_usuarios_filtrado}")
    if not df_usuarios_filtrado.empty:
        # Usuario válido
        nombre = df_usuarios_filtrado["nombres"].str.strip().iloc[0]
        apellido = df_usuarios_filtrado["apellidos"].str.strip().iloc[0]
        mombre_completo = f"{nombre} {apellido}"
        session["user"] = {
            "email": correo,
            "name": mombre_completo,
            "picture": "static/images/default_avatar.png"
        }
        session["correo_cliente"] = correo

        user = session.get('user')

        clientes_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
        clientes_mascotas = clientes_mascotas[clientes_mascotas["correo_cliente"]==correo]

        print(f"clientes_mascotas{clientes_mascotas}")

        print(f"user en enviar_rcaptcha_login es {user}")

        clientes_mascotas=clientes_mascotas.to_dict(orient="records")  

        return jsonify({
            'user': user,
            'clientes_mascotas': clientes_mascotas
        })  
 
    else:
        df_usuarios_filtrado=df_usuarios[
            (df_usuarios['correo_cliente']== correo)]  
        if df_usuarios_filtrado.empty:
            # Usuario no encontrado
            return jsonify({'error': 'El usuario no existe'}), 401
        else:
            # La combinación usuario contraseña no existe
            return jsonify({'error': 'La combinación usuario contraseña no existe'}), 401            

    return jsonify({'mensaje': 'Formulario recibido correctamente'})





@app.route('/clear_sesion')
def clear_sesion():
    session.clear()
    return "Sesión borrada"


@app.route("/registro_usuario")
def registro_usuario():
    return render_template("registro_usuario.html")



@app.route("/api/registrar_usuario", methods=["POST"])
def registrar_usuario():
    data = request.json
    nombres = data.get("nombres", "").strip()
    apellidos = data.get("apellidos", "").strip()
    correo = data.get("correo", "").strip()
    password = data.get("password", "").strip()
    recaptcha_token = data.get("recaptcha_token", "")

    if not all([nombres, apellidos, correo, password, recaptcha_token]):
        return jsonify({"success": False, "error": "Todos los campos son obligatorios"})

    archivo_path = "data/usuarios.csv"

    # Si el archivo no existe, creamos uno vacío con encabezados
    if not os.path.exists(archivo_path):
        df = pd.DataFrame(columns=["id_cliente", "nombres", "apellidos", "correo_cliente", "contrasenia"])
        df.to_csv(archivo_path, sep=";", index=False)

    # Leer y calcular nuevo ID
    df = pd.read_csv(archivo_path, sep=";")
    nuevo_id = int(df["id_cliente"].max(skipna=True) or 0) + 1

    # Crear nuevo registro
    nuevo_usuario = pd.DataFrame([{
        "id_cliente": nuevo_id,
        "nombres": nombres,
        "apellidos": apellidos,
        "correo_cliente": correo,
        "contrasenia": password
    }])

    # Agregar y guardar
    df = pd.concat([df, nuevo_usuario], ignore_index=True)
    df.to_csv(archivo_path, sep=";", index=False)

    # Guardar sesión como autenticado
    session["user"] = {
        "name": f"{nombres} {apellidos}",
        "email": correo,
        "picture": "/static/images/default_avatar.png"
    }
    session["correo_cliente"] = correo

    return jsonify({"success": True})


@app.route('/calendario')
def calendario():
    user = session.get("user", None)

    print(session.get("user"))
    if not user:
        return redirect(url_for("login"))    
    email=user.get("email")

    df_reservas = pd.read_csv("data/reservas.csv", sep=";")

    df_staff = pd.read_csv("data/staff.csv", sep=";")
    #a df_filtradas le agregamos los datos de clientes_mascotas, donde id_clientes_mascotas == mascota
    df_reservas = df_reservas.merge(
        df_staff[["id_veterinario", "nombres", "apellidos", "sexo", "correo"]],
        left_on="medico_que_atendio",
        right_on="id_veterinario",
        how="left"
    )

    df_reservas = df_reservas[df_reservas['correo'] == email]
    #df_reservas.to_csv("data/df_reservas.csv", sep=";", index=False)
    
    clientes_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    df_reservas = df_reservas.merge(
        clientes_mascotas[["id_clientes_mascotas", "nombre_mascota", "fecha_nacimiento", "sexo", "id_especie_raza"]],
        left_on="mascota",
        right_on="id_clientes_mascotas",
        how="left"
    )
    
    especie_raza = pd.read_csv("data/especie_raza.csv", sep=";")
    df_reservas = df_reservas.merge(
        especie_raza[["id_especie_raza", "id_especie", "id_raza"]],
        left_on="id_especie_raza",
        right_on="id_especie_raza",
        how="left"
    )

    
    especies = pd.read_csv("data/especies.csv", sep=";")
    df_reservas = df_reservas.merge(
        especies[["id_especie", "especie", "icono"]],
        left_on="id_especie",
        right_on="id_especie",
        how="left"
    )  

    razas = pd.read_csv("data/razas.csv", sep=";")
    df_reservas = df_reservas.merge(
        razas[["id_raza", "nombre_raza"]],
        left_on="id_raza",
        right_on="id_raza",
        how="left"
    ) 

              
    print("DEBUG df_reservas")
    print(df_reservas)

    #calculamos la cantidad de mascotas nuevas
    hoy = datetime.now().date()
    df_reservas['fecha2'] = pd.to_datetime(df_reservas['fecha']).dt.date
    
    # Mascotas con citas futuras
    # Separar en futuras y pasadas
    df_futuras = df_reservas[df_reservas['fecha2'] >= hoy]
    df_pasadas = df_reservas[df_reservas['fecha2'] < hoy]

    # Mascotas en pasado
    ids_pasados = df_pasadas['mascota'].unique()

    # Filtrar futuras que no estén en pasadas
    nuevas_mascotas = df_futuras[~df_futuras['mascota'].isin(ids_pasados) & (df_futuras['mascota'] != -88)]
    print("Mascotas futuras:", nuevas_mascotas['mascota'].nunique())

    #Estimamos los ingresos del mes actual
    df_reservas['fecha2'] = pd.to_datetime(df_reservas['fecha'], errors='coerce', dayfirst=True)
    df_actual = df_reservas[(df_reservas['fecha2'].dt.month == hoy.month) & 
                                (df_reservas['fecha2'].dt.year == hoy.year)]

    # Convertir precios a numérico
    df_actual['precio'] = pd.to_numeric(df_actual['precio'], errors='coerce')

    # Sumar precios válidos
    ingresos_estimados = df_actual['precio'].sum()

    #eliminamos el campo auxiliar
    df_reservas = df_reservas.drop(columns=['fecha2'])

    #calculamos las notas promedios del mèdico
    # Asegurar que 'notas_medico' sea numérico
    df_reservas['notas_medico'] = pd.to_numeric(df_reservas['notas_medico'], errors='coerce')

    # Calcular el promedio, ignorando valores nulos
    promedio_notas_medico = (df_reservas['notas_medico'].mean()/5)
    promedio_precio_calidad = (df_reservas['precio-calidad'].mean()/5)
    promedio_puntualidad = (df_reservas['puntualidad'].mean()/5)

    df_reservas['hora'] = pd.to_datetime(
        df_reservas['hora'], errors='coerce').dt.strftime('%H:%M')

    reservas=df_reservas.to_dict(orient="records")  

    #GENERAR DATOS PARA LA RESERVA
    # Fecha base desde query param o se agisna la fecha do hoy por defecto
    fecha_base_str = request.args.get("fecha")
    if fecha_base_str:
        fecha_base = datetime.strptime(fecha_base_str, "%Y-%m-%d")
    else:
        fecha_base = datetime.today()

    # Calcular inicio y fin de semana
    lunes = fecha_base - timedelta(days=fecha_base.weekday())
    semana = [lunes + timedelta(days=i) for i in range(7)]
    semana_str = [d.strftime("%Y-%m-%d") for d in semana]

    # Filtrar reservas solo de esta semana
    df_reservas_filtrada = df_reservas[df_reservas["fecha"].isin(semana_str)].copy()
    df_reservas_filtrada = df_reservas_filtrada.sort_values(["fecha", "hora"])
    print("DEBUG df_reservas_filtrada")
    print(df_reservas_filtrada)
    # Formatear para frontend
    reservas_filtrada = df_reservas_filtrada.to_dict(orient="records")

    # Citas hoy
    hoy_str = datetime.today().strftime("%d-%m-%Y")
    print("DEBUG hoy_str fecha de hoy")
    print(hoy_str)    
    print("DEBUG df_reservas asntes del filtrar por fecha de hoy")
    print(df_reservas)
    citas_hoy = df_reservas[(df_reservas["fecha"] == hoy_str) & (df_reservas["mascota"] !=-88)]
    print("DEBUG citas_hoy")
    print(citas_hoy)    
    total_citas_hoy = len(citas_hoy)

    horas_bloqueadas = df_reservas[(df_reservas["mascota"] ==-88)]


    # Horas libres (suponiendo 14 bloques por día)
    horas_libres = 13 - len(citas_hoy) - len(horas_bloqueadas)

    # Próximas 3 reservas
    ahora = datetime.now()
    df_reservas["datetime"] = pd.to_datetime(df_reservas["fecha"] + " " + df_reservas["hora"])
    proximas = df_reservas[df_reservas["datetime"] > ahora].sort_values("datetime").head(3).to_dict(orient="records")

    semana_anterior = (lunes - timedelta(days=7)).strftime("%Y-%m-%d")
    semana_siguiente = (lunes + timedelta(days=7)).strftime("%Y-%m-%d")
    now = datetime.today()

    return render_template("calendario.html", 
                            user=user,
                            reservas=reservas,
                            id_clinica=df_reservas.iloc[0]["id_clinica"],  # primer registro
                            medico_que_atendio=df_reservas.iloc[0]["medico_que_atendio"], 
                            reservas_filtrada=reservas_filtrada,
                            semana=semana,
                            lunes=lunes.strftime("%Y-%m-%d"),
                            now=now,
                            semana_anterior=semana_anterior,
                            semana_siguiente=semana_siguiente,
                            citas_hoy=total_citas_hoy,
                            horas_libres=horas_libres,
                            proximas=proximas,
                            nuevas_mascotas=nuevas_mascotas['mascota'].nunique(),
                            ingresos_estimados=ingresos_estimados,
                            promedio_notas_medico = promedio_notas_medico,
                            promedio_precio_calidad = promedio_precio_calidad,
                            promedio_puntualidad = promedio_puntualidad
                        )

#Funciones para sincronizar reservas con google calendar
def crear_evento_google_calendar(service, reserva):


    # Definir valores
    resumen = f"Reserva de {reserva['nombre_mascota']}"
    #fecha_hora_inicio = f"{reserva['fecha']}T{reserva['hora']}:00"
    #fecha_hora_fin = f"{reserva['fecha']}T{reserva['hora_fin']}:00"

    # Agrega zona horaria correcta
    tz = pytz.timezone("America/Santiago")
    inicio_dt = tz.localize(datetime.strptime(f"{reserva['fecha']} {reserva['hora']}", "%Y-%m-%d %H:%M"))
    fin_dt = tz.localize(datetime.strptime(f"{reserva['fecha']} {reserva['hora_fin']}", "%Y-%m-%d %H:%M"))

    # Convertir a string ISO con zona horaria
    fecha_hora_inicio = inicio_dt.isoformat()
    fecha_hora_fin = fin_dt.isoformat()
    # Buscar eventos existentes en ese rango exacto
    eventos = service.events().list(
        calendarId='primary',
        timeMin=fecha_hora_inicio,
        timeMax=fecha_hora_fin,
        q=resumen,
        singleEvents=True,
        orderBy="startTime"
    ).execute().get("items", [])

    if eventos:
        print("Evento ya existente, no se crea duplicado.")
        return None  # o retorna eventos[0] si quieres

    # Si no existe, se crea
    evento = {
        'summary': resumen,
        'location': reserva['direccion_clinica'],
        'description': f"Atiende: {reserva['nombre_veterinario']}. Motivo: {reserva['motivo_reserva']}",
        'start': {
            'dateTime': fecha_hora_inicio,
            'timeZone': 'America/Santiago',
        },
        'end': {
            'dateTime': fecha_hora_fin,
            'timeZone': 'America/Santiago',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 60},
            ],
        },
    }

    evento_creado = service.events().insert(calendarId='primary', body=evento).execute()
    print(f"Evento creado: {evento_creado.get('htmlLink')}")
    return evento_creado


@app.route('/api/sincronizar_reservas', methods=['POST'])
@login_required  # si quieres que solo funcione autenticado
def sincronizar_reservas():
   # from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    user = session.get("user", None)

    # 1. Autenticación y credenciales
    if 'credentials' not in session:
        return jsonify({'error': 'No autenticado con Google'}), 401

    creds = construir_google_credentials(session['credentials'])
    service = build('calendar', 'v3', credentials=creds)
    print("DEBUG sincronizar_reservas creds")    
    print(creds)
    print("DEBUG sincronizar_reservas service")    
    print(service)    
    calendars = service.calendarList().list().execute()
    for cal in calendars['items']:
        print(cal['summary'], cal['id'])

    # 2. Obtener reservas futuras (puede ser desde CSV o MySQL)
    df_reservas = pd.read_csv("data/reservas.csv", sep=';')  # o query desde MySQL
    df_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    df_reservas = df_reservas.merge(
        df_mascotas[["id_clientes_mascotas", "nombre_mascota"]],
        left_on="mascota",
        right_on="id_clientes_mascotas",
        how="left" )   
    del df_mascotas


    hoy = pd.Timestamp.now().date()
    df_reservas['fecha'] = pd.to_datetime(df_reservas['fecha']).dt.date
    reservas_futuras = df_reservas[df_reservas['fecha'] >= hoy]

    print("DEBUG sincronizar_resarvas reservas_futuras")
    print(reservas_futuras)

    # 3. Recorrer y sincronizar
    for _, reserva in reservas_futuras.iterrows():
        hora_inicio = str(reserva['hora'])[:5]  # por si viene como "12:30:00"
        hora_fin = calcular_fin_hora(hora_inicio)

        crear_evento_google_calendar(service, {
            'nombre_mascota': reserva['nombre_mascota'],
            'direccion_clinica': obtener_direccion_clinica(reserva['id_clinica']),
            'nombre_veterinario': obtener_nombre_veterinario(reserva['medico_que_atendio']),
            'motivo_reserva': reserva.get('motivo', 'Consulta Veterinaria'),
            'fecha': str(reserva['fecha']),
            'hora': hora_inicio,
            'hora_fin': hora_fin,
        })
    # guardamos la hora de la última sincronización
    correo_usuario = user.get("email")
    if correo_usuario:
        df = pd.read_csv("data/usuarios.csv", sep=';')
        print("DEBUG sincronizar_reservas df=")
        print(df)
        df.loc[df["correo_cliente"] == correo_usuario, "ultima_sincronizacion_calendario"] = datetime.now().isoformat()
        df.to_csv("data/usuarios.csv", sep=';', index=False)
    
    #actualizar el estado de la reserva en la pantalla
    
    return jsonify({"mensaje": "Reservas sincronizadas con Google Calendar"})

def obtener_direccion_clinica(id_clinica):
    clinicas = pd.read_csv("data/clinicas.csv", sep=';')
    return clinicas.loc[clinicas['id_clinica'] == int(id_clinica), 'direccion'].values[0]

def obtener_nombre_veterinario(id_vet):
    staff = pd.read_csv("data/staff.csv", sep=';')
    fila = staff.loc[staff['id_veterinario'] == int(id_vet)]
    return fila['nombres'].values[0] if not fila.empty else "Veterinario/a"

def calcular_fin_hora(hora_str):
    from datetime import datetime, timedelta
    hora_str = str(hora_str).strip()[:5]  # e.g., "12:30:00" → "12:30"
    print(f"hora_str= {hora_str}")
    try:
        inicio = datetime.strptime(hora_str, "%H:%M")
        fin = inicio + timedelta(minutes=30)
        return fin.strftime("%H:%M")
    except ValueError:
        raise ValueError(f"Hora inválida: {hora_str}")

#usada para mostrar el mensaje de tiempo transcurrido desde la última sincronización del calendar
@app.route('/api/ultima_sincronizacion')
def obtener_ultima_sincronizacion():
    user = session.get("user", None)
    correo_usuario = user.get("email")
    #correo_usuario = session.get("user", {}).get("email")
    if not correo_usuario:
        return jsonify({"error": "Usuario no autenticado"}), 401

    df = pd.read_csv("data/usuarios.csv", sep=';')
    print("correo_usuario=", correo_usuario)
    print("df")
    print(df)
    fila = df[df["correo_cliente"] == correo_usuario]
    print("fila")
    print(fila)    
    if fila.empty:
        return jsonify({"timestamp": None})

    fecha_str = fila.iloc[0]["ultima_sincronizacion_calendario"]
    return jsonify({"timestamp": fecha_str if pd.notna(fecha_str) and fecha_str != "" else None})





# Proceso para leer el calendario de google calendar y luego poner una marca en el calendario
# de la aplicación que indique que el evento está sincronizado
@app.route("/api/eventos_sincronizados")
def eventos_sincronizados():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from datetime import datetime
    import pytz

    token = session.get('credentials')
    if not token:
        return jsonify({"error": "No autenticado con Google"}), 401

    creds = Credentials(
        token=token['access_token'],
        refresh_token=token.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/calendar']
    )

    service = build("calendar", "v3", credentials=creds)

    ahora = datetime.utcnow().isoformat() + "Z"  # formato requerido

    eventos_result = service.events().list(
        calendarId="primary",
        timeMin=ahora,
        maxResults=100,
        singleEvents=True,
        orderBy="startTime"
    ).execute()


    eventos = eventos_result.get("items", [])

    sincronizados = []
    for evento in eventos:
        inicio = evento.get("start", {}).get("dateTime")
        if inicio:
            sincronizados.append(inicio)  # ISO 8601

    return jsonify({"sincronizados": sincronizados})

#########################
## Bloquear fechas y horas en calendario
# app.py (extracto)
import os
from datetime import datetime, timedelta
import pandas as pd
from flask import request, jsonify, session

# -------- Helpers --------
def generar_slots(hora_inicio: str, hora_fin: str, duracion_min: int):
    """Devuelve lista de strings HH:MM en [inicio, fin) cada 'duracion_min'."""
    if not hora_inicio or not hora_fin:
        return []
    fmt = "%H:%M:%S"  # incluye segundos
    t0 = datetime.strptime(hora_inicio, "%H:%M")
    t1 = datetime.strptime(hora_fin, "%H:%M")
    if t1 <= t0:
        return []
    out, cur = [], t0
    while cur < t1:
        out.append(cur.strftime(fmt))
        cur += timedelta(minutes=duracion_min)
    return out

def fechas_en_rango(fecha_inicio: str, fecha_fin: str):
    """Lista de fechas YYYY-MM-DD entre inicio y fin, ambas incluidas."""
    di = datetime.strptime(fecha_inicio, "%d-%m-%Y").date()
    df = datetime.strptime(fecha_fin, "%d-%m-%Y").date()
    if df < di:
        return []
    out = []
    cur = di
    while cur <= df:
        out.append(cur.strftime("%d-%m-%Y"))
        cur += timedelta(days=1)
    return out

# -------- Endpoint --------
@app.route('/api/bloquear_horario', methods=['POST'])
def api_bloquear_horario():
    # 1) Requiere sesión (sin reCAPTCHA)
    print("entrando a api_bloquear_horario")

    if 'user' not in session or not session['user'].get('email'):
        return jsonify({"error":"No autenticado"}), 401

    data = request.get_json(silent=True) or {}

    id_medico = str(data.get('id_medico', '')).strip()
    id_clinica = str(data.get('id_clinica', '')).strip()
    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')
    bloqueo_dia_completo = bool(data.get('bloqueo_dia_completo'))
    hora_inicio = data.get('hora_inicio') or "09:00"
    hora_fin = data.get('hora_fin') or "18:00"
    duracion_min = int(data.get('duracion_min') or 45)
    motivo = (data.get('motivo') or '').strip()
    print("hora inicio =", hora_inicio, " hora fin =", hora_fin, " duracion=", duracion_min)

    # 2) Validaciones básicas
    if not (id_medico and id_clinica and fecha_inicio and fecha_fin):
        return jsonify({"error":"Parámetros incompletos"}), 400

    if fecha_fin < fecha_inicio:
        return jsonify({"error":"La fecha fin no puede ser menor a la fecha inicio"}), 400

    # No permitir pasado
    hoy = datetime.now().date()
    if datetime.strptime(fecha_inicio, "%d-%m-%Y").date() < hoy:
        return jsonify({"error":"No se puede bloquear en fechas pasadas"}), 400

    # Ajuste para día completo
    if bloqueo_dia_completo:
        hora_inicio, hora_fin = "09:00", "19:00"
        if duracion_min < 30:
            duracion_min = 45  # menos filas

    fechas = fechas_en_rango(fecha_inicio, fecha_fin)
    if not fechas:
        return jsonify({"error":"Rango de fechas no válido"}), 400

    slots = generar_slots(hora_inicio, hora_fin, duracion_min)
    print("DEBUG slots=")
    print(slots)

    if not slots:
        return jsonify({"error":"El rango horario no genera slots"}), 400

    # 3) Leer CSV
    path_csv = 'data/reservas.csv'
    sep = ';'
    try:
        df = pd.read_csv(path_csv, sep=sep, dtype=str)
    except FileNotFoundError:
        df = pd.DataFrame()

    cols = df.columns.tolist()
    # Columnas mínimas si el CSV aún no existe
    if df.empty and not cols:
        cols = ['id_reserva','id_clinica','correo_cliente','mascota',
                'fecha','hora','medico_que_atendio','estado','creado_en','observacion']

    # 4) Preparar duplicados/conflictos
    existentes = set()
    conflictos_set = set()

    if not df.empty:
        df_med = df[df.get('medico_que_atendio', '') == id_medico]

        # Bloqueos existentes (mascota = -88)
        df_blk = df_med[df_med.get('mascota','') == "-88"]
        for _, r in df_blk.iterrows():
            existentes.add((r.get('fecha'), r.get('hora')))

        # Reservas reales (mascota != -88)
        df_real = df_med[df_med.get('mascota','') != "-88"]
        for _, r in df_real.iterrows():
            conflictos_set.add((r.get('fecha'), r.get('hora')))
        print("DEBUD conflictos_set=")
        print(conflictos_set)

    # 5) Generar filas
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insertados, duplicados = 0, 0
    conflictos = []
    nuevas_filas = []

    # siguiente id_reserva
    next_id = 1
    if 'id_reserva' in cols and not df.empty:
        try:
            next_id = int(pd.to_numeric(df['id_reserva'], errors='coerce').fillna(0).max()) + 1
        except:
            next_id = 1

    user_email = session['user']['email'].strip()

    # (Opcional) límite de filas para evitar abusos accidentales
    max_filas = 1000

    for f in fechas:
        for h in slots:
            if (f, h) in conflictos_set:
                conflictos.append({"fecha": f, "hora": h})
                continue
            if (f, h) in existentes:
                duplicados += 1
                continue

            row = {c: '' for c in cols}
            if 'id_reserva' in cols: row['id_reserva'] = str(next_id); next_id += 1
            if 'id_clinica' in cols: row['id_clinica'] = id_clinica
            if 'correo_cliente' in cols: row['correo_cliente'] = user_email
            if 'mascota' in cols: row['mascota'] = "-88"              # marca de bloqueo
            if 'fecha' in cols: row['fecha'] = f
            if 'hora' in cols: row['hora'] = h 
            if 'medico_que_atendio' in cols: row['medico_que_atendio'] = id_medico
            if 'estado' in cols: row['estado'] = '1'                  # ocupado
            if 'creado_en' in cols: row['creado_en'] = now_str
            if 'observacion' in cols: row['observacion'] = f"BLOQUEO: {motivo}" if motivo else "BLOQUEO"

            nuevas_filas.append(row)
            insertados += 1

            if insertados >= max_filas:
                break
        if insertados >= max_filas:
            break

    # 6) Guardar CSV
    if insertados > 0:
        df_out = pd.concat([df, pd.DataFrame(nuevas_filas, columns=cols)], ignore_index=True) if not df.empty \
                 else pd.DataFrame(nuevas_filas, columns=cols)
        os.makedirs(os.path.dirname(path_csv), exist_ok=True)
        df_out.to_csv(path_csv, sep=sep, index=False)

    return jsonify({
        "insertados": insertados,
        "duplicados": duplicados,
        "conflictos": conflictos,
        "limitado_por_max": insertados >= max_filas
    }), 200




## FIN Bloqear fechas y horas en calendario


if __name__ == "__main__":
    app.run(debug=True)

