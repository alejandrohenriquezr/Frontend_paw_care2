from flask import Flask, send_file, abort, redirect, url_for, session, request, jsonify, render_template, send_from_directory
from authlib.integrations.flask_client import OAuth
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
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Para Transbank
#from flask import Flask, render_template, redirect, url_for, request
from transbank.webpay.webpay_plus.transaction import Transaction
from docx import Document
from io import BytesIO
#from docx2pdf import convert

import os
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






#configuración de la APP
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.urandom(24)

#Configuración del correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'alhen1970@gmail.com'
app.config['MAIL_PASSWORD'] = 'ptjt fgco uoia jgyx'

mail = Mail(app)

# Configuración de OAuth
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
    comuna = request.args.get("comuna", "")
    if comuna:
        session["comuna"] = comuna
        print(f"[INFO] Comuna obtenida de la URL: {comuna}")
    busqueda = request.args.get("search", "")
    if busqueda:
        session["busqueda"] = busqueda
        print(f"[INFO] busqueda obtenida de la URL: {busqueda}")        

    user=session.get("user", None)
    print(f"[INFO] user: {user}")
    # Verificar si el usuario está autenticado
    #si el usuario está autenticado, entonces redirigie a intex.html y entregar los datos del usuario
    if user:
        print(f"[INFO] usuario autenticado: {user}")
        # Redirigir a la página de inicio de sesión
        return render_template("index.html", user=user)
    else:
        print(f"[INFO] usuario no autenticado: {user}")
        # Redirigir a la página de inicio de sesión
        return render_template(("index.html"))
    #return render_template("index.html", user=user)
    

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
    session['mascotaSeleccionada'] = data.get('mascotaSeleccionada')
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

    #return 'Datos guardados en la sesión', 200




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
    print(f"[INFO LOGIN] next: {request.full_path}")
    #verificamos si request.full_path contiene agendar
    #si request.full_path contiene agendar, entonces guardamos la ruta completa en la sesión
    redireccion = request.args.get('redirect')
    print(f"[INFO redireccion] next: {redireccion}")
    #if request.full_path.startswith("/agendar"):
    if redireccion=="agendar":
        session['next'] = request.full_path
    
    nonce = generate_nonce()
    session['nonce'] = nonce
     
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
    return google.authorize_redirect(redirect_uri, nonce=nonce)


# 📌 Ruta de | (Google redirige aquí después de autenticación)
@app.route("/login/callback")
def callback():
    token = google.authorize_access_token()
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
    # Si no existe next_path, redirige home
    if not next_path:
        return redirect(url_for("/"))

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

    # Redirige a la ruta original completa con sus parámetros
    return redirect(next_path + ("?" + parsed.query if parsed.query else ""))


# 📌 Ruta de Dashboard (Solo accesible si está autenticado)
@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("home"), user=user)
    
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
    return render_template("agendar.html",
        df_staff=df_staff,
        df_staff_json=df_staff.to_dict(orient="records"),  # 🔹 aquí va el JSON
        df_reservas=df_reservas,
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

@app.route('/sitio_privado')
def sitio_privado():
    user = session.get("user")
    print(session.get("user"))
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template('mis_mascotas.html', user=user)


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

    df_mis_mascotas["anos_edad"], df_mis_mascotas["meses_edad"] = zip(*df_mis_mascotas["fecha_nacimiento"].apply(calcular_edad))

    #df_mis_mascotas["meses_edad"] = edad_meses

    # Leer clinicas.csv y unir por id_clinica
    df_especie_raza = pd.read_csv("data/especie_raza.csv", sep=";")
    df_mis_mascotas = df_mis_mascotas.merge(df_especie_raza[["id_especie_raza", "id_especie", "id_raza"]], on="id_especie_raza", how="left")

    df_razas= pd.read_csv("data/razas.csv", sep=";")
    df_mis_mascotas = df_mis_mascotas.merge(df_razas[["id_raza", "nombre_raza"]], on="id_raza", how="left")

    df_especies= pd.read_csv("data/especies.csv", sep=";")
    df_mis_mascotas = df_mis_mascotas.merge(df_especies[["id_especie", "especie"]], on="id_especie", how="left")


    # Convertir columna fecha a datetime
    df_mis_mascotas["fecha_nacimiento"] = pd.to_datetime(df_mis_mascotas["fecha_nacimiento"], format="%d-%m-%Y")

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
    df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], format="%d-%m-%Y")

    #ahora filtramos df_reservas para que solo contenga las reservas con fecha mayor o igual a hoy
    hoy = datetime.now().strftime("%d-%m-%Y")
    #ordenamos desde la fecha más actual a la mas vieja
    df_reservas = df_reservas.sort_values(by=["fecha"], ascending=False)
    df_reservas_pasadas=df_reservas
    df_reservas = df_reservas[(df_reservas["fecha"] >= hoy)]
    df_reservas_pasadas = df_reservas_pasadas[(df_reservas_pasadas["fecha"] < hoy)]
    #eliminamos los 00:00:00 del campo fecha
    df_reservas["fecha"] = df_reservas["fecha"].dt.strftime("%d-%m-%Y")
    df_reservas_pasadas["fecha"] = df_reservas_pasadas["fecha"].dt.strftime("%d-%m-%Y")
    #eliminamos los segundos a los campos hora
    df_reservas["hora"] = df_reservas["hora"].str[:5]
    df_reservas_pasadas["hora"] = df_reservas_pasadas["hora"].str[:5]

    # Convertir dataframe a lista de diccionarios

    mis_citas = df_reservas.to_dict(orient="records")
    mis_citas_pasadas = df_reservas_pasadas.to_dict(orient="records")
    print(df_reservas)

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
    fecha_nacimiento = pd.to_datetime(fecha_nacimiento, format="%d-%m-%Y")
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

        # 🔥 Cargar el CSV
        df = pd.read_csv("data/clinicas.csv", sep=";")
        
        # 🔥 Renombrar columnas para evitar espacios en blanco
        df.columns = df.columns.str.strip()
        #busqueda es el valor del parámetro search de la url
        busqueda = session["busqueda"]  # Obtener el valor del input de búsqueda
        # Comuna es el valor del parámetro comuna de la url
        comuna = session.get("comuna", "")  # Obtener el valor del select comunas
        #imprimo el valor de busqueda y comuna
        print(f"Valor de busqueda: {busqueda}")

        print(f"Valor de comuna busqueda: {comuna}")
        
        # Filtrar por search si se proporciona
        if busqueda:
            print(f"buscando dentro del if por {busqueda}")
            df_nombre = df[df["nombre"].str.contains(busqueda, case=False, na=False)]
            #si df es vacio, entonces buscamos por el campo especialidades
            if df_nombre.empty:
                print(f"buscando dentro del if por {busqueda} en especialidades")
                df = df[df["especialidades"].str.contains(busqueda, case=False, na=False)]
            else:
                df = df_nombre
            # si no har search, entonces buscamos por comuna
        elif comuna:
            print("buscando por {comuna}")
            df["dpa"] = df["dpa"].astype(str)
            df = df[df["dpa"].str.contains(comuna, case=False, na=False)]
        # 🔍 Convertir a JSON y devolver
    #imprimir en la consola el df
        print("df filtrado por busqueda: ", df)
                
        clinicas_json = df.to_dict(orient="records")
        return jsonify({"clinicas": clinicas_json})

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route("/sugerencias", methods=["GET"])
def obtener_sugerencias():
    query = request.args.get("q", "").lower()  # Obtener el texto ingresado por el usuario
    query = remover_tildes(query)  # 🔥 Eliminar tildes de la búsqueda
    comuna = request.args.get("comuna", "")  # Obtener el valor del select comunas
    resultados = []

    if query:
        try:
            print("📂 Intentando leer el archivo: data/clinicas.csv")  # Depuración
            df = pd.read_csv("data/clinicas.csv", sep=";")  # Leer el archivo CSV

            print("✅ Archivo CSV leído correctamente")

            # Mostrar las primeras filas del archivo en la consola
            print("🔍 Primeras filas del CSV:\n", df.head())
            #muestro el tipo de dato de la columna dpa
            print("Tipo de dato de la columna dpa:", df['dpa'].dtype)
            # Verificar si la columna existe en el CSV
            if "nombre" not in df.columns or "dpa" not in df.columns:
                print("❌ ERROR: La columna 'nombre' o 'DPA' no existe en el CSV")
                return jsonify({"error": "Las columnas 'nombre' o 'dpa' no existen en el CSV"}), 500
            
            # Filtrar por la comuna seleccionada
            df["dpa"] = df["dpa"].astype(str)
            df_filtrado = df[df["dpa"].str.contains(comuna, case=False, na=False)]
            clinicas = df_filtrado["nombre"].dropna().unique()  # Obtener nombres únicos
            especialidades = df_filtrado["especialidades"].dropna().unique()
            # Filtrar sugerencias que contengan el texto ingresado
            resultados_nombre = [c for c in clinicas if query in remover_tildes(c.lower())]
            resultados_especialidades = [e for e in especialidades if query in remover_tildes(e.lower())]
            # Combinar resultados de nombres y especialidades
            resultados = list(set(resultados_nombre + resultados_especialidades))

            # Filtrar sugerencias que contengan el texto ingresado
                          
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


@app.route("/api/reservas", methods=["GET"])
def obtener_reservas():
    try:
        reservas = []
        with open('data/reservas.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                reservas.append(row)
        #print(f"Reservas: {reservas}")  # Depuración
        
        # Asegúrate de que reservas es un array
        if not isinstance(reservas, list):
            reservas = [reservas]

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


@app.route("/api/insertar_reservas", methods=["GET"])
#insertar una reserva
#def insert_reservation(id_clinica, correo_cliente, id_clientes_mascotas, fecha, hora):
def insert_reservation():
    #imprimo en la consola todas las variables de sesión y sus valores
    print("Variables de sesión:")
    for key, value in session.items():  
        print(f"{key}: {value}")    


    # recuperamos las variables de sesion fechaSeleccionada, horaSeleccionada, mascotaSeleccionada, id_clinica y correo_cliente
    id_clinica = session.get('id_clinica') 
    #correo_cliente corresponde al valor de email de la variavle de sesion user
    correo_cliente = session.get('user')['email']
    nombre_cliente = session.get('user')['name']
    id_veterinario = session.get('id_veterinario')
    mascotaSeleccionada = session.get('mascotaSeleccionada')
    fechaSeleccionada = session.get('fechaSeleccionada')
    precio = session.get('precio') 
    print(f"Precio: {precio}")
    token = session.get('token')
    #si fechaSeleccionada está vacia, entonces le asignamos el valor de fechaSeleccionada de la url
    if not fechaSeleccionada:
        fechaSeleccionada = session.get('fecha')
    horaSeleccionada = session.get('horaSeleccionada')
    if not horaSeleccionada:
        horaSeleccionada = session.get('hora')    
#si el largo de horaSeleccionada es 5, entonces le agregamos un 0 al final
    if len(horaSeleccionada) == 5:
        horaSeleccionada += ":00"

    print(f"Insertando reserva: {id_clinica}, {correo_cliente}, {mascotaSeleccionada}, {fechaSeleccionada}, {horaSeleccionada}, {precio}")
    with open('data/reservas.csv', 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        reservations = list(reader)
    # Verificar si la reserva ya existe
    for reservation in reservations:
        if (reservation['id_clinica'] == int(id_clinica) and
            reservation['correo_cliente'] == correo_cliente and
            reservation['mascota'] == int(mascotaSeleccionada) and  
            reservation['fecha'] == fechaSeleccionada and
            reservation['hora'] == horaSeleccionada and
            reservation['medico_que_atendio'] == id_veterinario and
            reservation['estado'] == 1):
            return jsonify({"error": "La reserva ya existe"}), 400

    
    #transformar reservations en un data frame
    reservations_df = pd.DataFrame(reservations)
    #obtener el valor maximo de la columna id_reserva del data frame
    #
    reservations_df['id_reserva'] = reservations_df['id_reserva'].astype(int)
    max_id_reserva = reservations_df['id_reserva'].max()
    #Almacenamos max_id_reserva en una variable de seción
    session['max_id_reserva'] = int(max_id_reserva)
    # Creamos el objeto con los datos de la nueva reserva
    session_id = session.get('session_id')

    new_reservation = {
        'id_reserva': (max_id_reserva + 1),
        'id_clinica': id_clinica,
        'correo_cliente': correo_cliente,
        'mascota': mascotaSeleccionada,
        'fecha': fechaSeleccionada,
        'hora': horaSeleccionada,
        'precio': precio,
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

    #retornamos un código 200
    #return jsonify({"message": "Reserva creada", "session_id": session_id}), 200
    return jsonify({"message": "Reserva creada exitosamente"}), 200
    #return
# Endpoint para confirmar o cancelar la reserva


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

@app.route("/api/insertar_comunas", methods=["POST"])
def insertar_comunas():
    data = request.json
    comuna = data.get('comuna')
    print("Comuna recibida:", comuna)
    
    # Lee el archivo data/dpa.csv y lo convierte a un dataframe
    df = pd.read_csv("data/dpa.csv", delimiter=";")
    
    # Filtra el dataframe por la comuna seleccionada
    filtered_df = df[df['Nombre_Comuna'] == comuna]
    
    # Obtiene el valor del campo Region
    if not filtered_df.empty:
        region = filtered_df.iloc[0]['Region']
        
        # Filtra el df por la región seleccionada
        filtered_df = df[df['Region'] == region]
        
        # Para cada registro de filtered_df, inserta un option en el select comunas
        options = ""
        for index, row in filtered_df.iterrows():
            options += f"<option value='{row['Comuna']}'>{row['Nombre_Comuna']}</option>"
        
        # Retorna el HTML de los options
        return options
    else:
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
    #si no hay usuario, entonces redirigimos a la página de inicio de sesión
    if not user:
        return redirect(url_for("login"))
    # Leer reservas.csv
    email = user.get("email")
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas = df_reservas[(df_reservas["correo_cliente"] == email) & (df_reservas["estado"] >= 0)]

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

    df_reservas = df_reservas.sort_values(by=["fecha"], ascending=False)
    print(df_reservas)
    # Convertir dataframe a lista de diccionarios
    mis_citas = df_reservas.to_dict(orient="records")
    if not user:
        return redirect(url_for("login"))    
    return render_template("mis_citas.html", user=user, mis_citas=mis_citas)


@app.route('/cancelar_cita', methods=["POST"])
#@login_required
def cancelar_cita():
    data = request.get_json(silent=True)
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
    
    id_clinica = int(data["id_clinica"])
    correo_cliente = data["correo"]
    fecha_original = data.get("fecha")

    # 🛠 Convertir fecha del formato ISO a formato CSV (%d-%m-%Y)
    fecha = datetime.strptime(fecha_original[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
    #pasamos fhea a formato %d-%m-%Y
    #fecha = pd.to_datetime(fecha, format="%Y-%m-%d")

    print(f"[INFO] Datos recibidos en cancelar_cita: {id_clinica}, {correo_cliente}, {fecha}")
    try:
        df = pd.read_csv("data/reservas.csv", sep=";")
        print(f"[INFO] DataFrame cargado: {df.head()}")
        mask = (
            (df["id_clinica"] == id_clinica) &
            (df["correo_cliente"] == correo_cliente) &
            (df["fecha"] == fecha)
        )
        print(f"[INFO] Máscara de filtro: {mask}")

        if mask.any():
            df.loc[mask, "estado"] = -1
            df.to_csv("data/reservas.csv", sep=";", index=False)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Reserva no encontrada."}), 404

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
    df_vaterinario = pd.read_csv("data/staff.csv", sep=";")
    df_vaterinario = df_vaterinario[(df_vaterinario["correo"] == email)]

    return render_template("pawcarepro.html", 
                            user=user, 
                            datos_veterinario=df_vaterinario.to_dict(orient="records") 
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
        amount = float(session.get('precio', 1000))

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
    if not session.get('pago_confirmado'):
        return "<script>alert('No puedes reservar sin pagar'); window.location.href='/';</script>"

    response, status_code = insert_reservation()
    user=session.get("user", None)
    id_clinica= int(session.get('id_clinica'))
    fecha= session.get('fecha')
    hora= session.get('hora')
    id_veterinario= int(session.get('id_veterinario'))
    id_mascota= int(session.get('mascotaSeleccionada'))
    token   = session.get('token')
    numero_tarjeta = session.get('numero_tarjeta')
    print(user)
    if not user:
        return redirect(url_for("login"))    
    email=user.get("email")

    df_clinica = pd.read_csv("data/clinicas.csv", sep=";")
    df_clinica = df_clinica[(df_clinica["id_clinica"] == id_clinica)]
    nombre_clinica = session.get('nombre_clinica')    
    direccion_clinica = df_clinica.iloc[0]["direccion"]
    session['nombre_clinica'] = nombre_clinica
    session['direccion_clinica'] = direccion_clinica
    df_mis_mascotas = pd.read_csv("data/clientes_mascotas.csv", sep=";")
    df_mis_mascotas = df_mis_mascotas[(df_mis_mascotas["id_clientes_mascotas"] == id_mascota)]
    nombre_mascota = df_mis_mascotas.iloc[0]["nombre_mascota"]
    session['nombre_mascota'] = nombre_mascota
    df_veterinario = pd.read_csv("data/staff.csv", sep=";")
    df_veterinario = df_veterinario[(df_veterinario["id_veterinario"] == id_veterinario)]
    nombres_veterinario = df_veterinario.iloc[0]["nombres"]
    apellidos_veterinario = df_veterinario.iloc[0]["apellidos"]
    session['nombres_veterinario'] = nombres_veterinario
    session['apellidos_veterinario'] = apellidos_veterinario
    
    if status_code == 200:

        #imprimir todo el contenido del objeto card_detail
        #
        

        #session.pop('pago_confirmado', None)
        #return render_template('cita_pagada.html', user=user)
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
        return "<script>alert('Error al registrar la reserva. Inténtalo nuevamente.'); window.location.href='/agendar';</script>"



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
    nombre_archivo = 'reserva.pdf'
    # Crear PDF en memoria
    buffer = io.BytesIO()
    #c = canvas.Canvas(nombre_archivo, pagesize=LETTER)
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    # Márgenes y ajustes
    x_margin = inch
    y_start = height - inch

    #mostrar los valores de datos
    #print(f"Datos recibidos en generar_pdf: {datos}")
    #Insertar la imagen cabecera_cita.png (100% por 100%) a 1 centìmetro del borde superior de la hoja
    #c.drawImage("static/images/cabecera_cita.png", 0, height - 1*inch, width=width, height=1*inch, mask='auto')
    c.drawImage("static/images/cabecera_cita.png", 25, height - 1*inch, width=589, height=60, mask=None, preserveAspectRatio=True, anchor='c')
    #cual es la sintaxis de drawImage
    
    # Fuente
    #c.setFont("Helvetica-Bold", 16)
    #c.drawCentredString(width / 2, y_start, "Detalles de la Reserva")

    # Cambiar a fuente estándar
    c.setFont("Helvetica", 12)

    y = y_start - 120
    fecha=session.get('fecha')
    #pasamos fecha a formato dd/mm/aaaa
    fecha = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m/%Y")


    nombres_veterinario = session.get('nombres_veterinario')
    apellidos_veterinario = session.get('apellidos_veterinario')
    nombre_mascota = session.get('nombre_mascota')
    precio = session.get('precio')
    #pasamos precio a tipo entero
    precio = int(precio)
    #cambiamos el formato de precio, con "." como separador de miles y din decimales


    # Contenido
    lineas = [
        f"Veterinario: {nombres_veterinario} {apellidos_veterinario}",	
        f"Mascota: {nombre_mascota}",	
        f"Fecha: {fecha}",
        f"Hora: {session.get('hora')}",
        f"Valor cancelado: ${precio}",
        f"Tarjeta terminada en: {session.get('numero_tarjeta')}",
        "",
        "Te recomendamos llegar 10 minutos antes de tu cita para evitar retrasos.",
        "",
        "Atte.,",
        "El equipo de PawCare"
    ]

    for linea in lineas:
        c.drawString(x_margin, y, linea)
        y -= 20

    c.save()



    #print(f"PDF generado en: {os.path.abspath(nombre_archivo)}")


    # entregar el archivo c al cliente
    buffer.seek(0)
    # descargar el archivo en el computador del usuario
    #return send_file(nombre_archivo, as_attachment=True, download_name=nombre_archivo, mimetype='application/pdf')

    # Devolver el archivo al usuario
    return send_file(
        buffer,
        as_attachment=True,
        download_name="reserva_cita.pdf",
        mimetype="application/pdf"
    )


@app.route('/enviar-cita-calendario', methods=['POST'])
def enviar_cita_calendario():
    # Variables desde sesión
    direccion = session.get('direccion_clinica')
    correo = session.get('correo_cliente')
    fecha = session.get('fecha')  # formato: YYYY-MM-DD
    hora = session.get('hora')    # formato: HH:MM
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

if __name__ == "__main__":
    app.run(debug=True)

