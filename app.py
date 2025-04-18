from flask import Flask, send_file, abort, redirect, url_for, session, request, jsonify, render_template, send_from_directory
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message
from functools import wraps
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime
from fpdf import FPDF

import os
import base64
import requests
from config import Config
import jwt
import pandas as pd
import unicodedata
import csv
import io

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

    session['id_clinica'] = data.get('id_clinica')
    #si id_clinica está vacia, entonces le asignamos el valor de id_clinica de la url
    if not session['id_clinica']:
        session['id_clinica'] = request.args.get('id_clinica')
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
    #print(f"[INFO] next: {request.full_path}")
    if request.full_path.startswith("/agendar"):
        session['next'] = request.full_path
    
    nonce = generate_nonce()
    session['nonce'] = nonce
     
    fecha = request.args.get('fecha')
    hora = request.args.get('hora')
    
    # Guardar los parámetros en la sesión
    session['fecha'] = fecha
    session['hora'] = hora

    session['fechaSeleccionada'] =fecha
    session['horaSeleccionada'] = hora

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

    # Recupera la ruta original (relativa) desde el decorador
    next_path = session.get("next", None)
    print(f"Ruta de redirección en el callback es: {next_path}")
    # Si no existe next_path, redirige al home o sitio privado
    if not next_path:
        return redirect(url_for("mis_mascotas"))

    # Si empieza con /agendar, redirige con url_for para asegurar parámetros
    parsed = urlparse(next_path)
    if parsed.path.startswith("/agendar"):
        params = parse_qs(parsed.query)
        return redirect(url_for(
            "agendar",
            id_clinica=params.get("id_clinica", [None])[0],
            fecha=params.get("fecha", [None])[0],
            hora=params.get("hora", [None])[0]
        ), user=user_info)

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
    print(f"Parámetros de la URL: {request.args}")
    # Verificar si el usuario está autenticado
    user_info = session.get('user')
    print(f"Información del usuario: {user_info}")
    user = session.get("user") 
    if user:
        print(f"correo del usuario: {user['email']}")

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
        print(id_clinica, fecha, hora)
        # Verificar si los parámetros existen
        print("los parametros son")
        if id_clinica and user_info['email'] and id_clientes_mascotas and fecha and hora:
            # Insertar la nueva reserva en el archivo CSV
            print("Insertar la nueva reserva en el archivo CSV")
            response, status_code = insert_reservation()
            if (status_code==200):
                print("Reserva creada")
                return render_template("agendar.html?ac=1")
            else:   
                print("Reserva no creada")
                return render_template("agendar.html?ac=99")        

    #primero debo ver si status_code existe y esta definida
    #si no existe, entonces la reserva no fue creada
    return render_template("agendar.html")

    

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

    print(df_mis_mascotas)
    # Convertir dataframe a lista de diccionarios
    mis_mascotas = df_mis_mascotas.to_dict(orient="records")

    #######
    ## Código para crear citas para la página mis_macotas
    df_reservas = pd.read_csv("data/reservas.csv", sep=";")
    df_reservas = df_reservas[(df_reservas["correo_cliente"] == email) & (df_reservas["estado"] == 1)]
    
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
    per_page = 5
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

    mascotaSeleccionada = session.get('mascotaSeleccionada')
    fechaSeleccionada = session.get('fechaSeleccionada')
    #si fechaSeleccionada está vacia, entonces le asignamos el valor de fechaSeleccionada de la url
    if not fechaSeleccionada:
        fechaSeleccionada = session.get('fecha')
    horaSeleccionada = session.get('horaSeleccionada')
    if not horaSeleccionada:
        horaSeleccionada = session.get('hora')    
#si el largo de horaSeleccionada es 5, entonces le agregamos un 0 al final
    if len(horaSeleccionada) == 5:
        horaSeleccionada += ":00"

    print(f"Insertando reserva: {id_clinica}, {correo_cliente}, {mascotaSeleccionada}, {fechaSeleccionada}, {horaSeleccionada}")
    # definimos reservations con el archivo reservas.csv
    # Leer las reservas existentes del archivo CSV y filtrar correo_cliente
    #df = pd.read_csv("data/reservas.csv", delimiter=";")   
    #filtered_df = df[df['id_clinica'] == id_clinica 
    #                 & df['correo_cliente'] == correo_cliente 
    #                 & df['mascota'] == mascotaSeleccionada 
    #                 & df['fecha'] == fechaSeleccionada 
    #                 & df['hora'] == horaSeleccionada]
    #if filtered_df no está vacío, entonces la reserva ya existe
    #if not filtered_df.empty:
    #    return jsonify({"error": "La reserva ya existe"}), 400

    #limpio el df
    #df = df.dropna()
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
            reservation['estado'] == 1):
            return jsonify({"error": "La reserva ya existe"}), 400

    
    #transformar reservations en un data frame
    reservations_df = pd.DataFrame(reservations)
    #obtener el valor maximo de la columna id_reserva del data frame
    #
    reservations_df['id_reserva'] = reservations_df['id_reserva'].astype(int)
    max_id_reserva = reservations_df['id_reserva'].max()

    # Creamos el objeto con los datos de la nueva reserva

    new_reservation = {
        'id_reserva': (max_id_reserva + 1),
        'id_clinica': id_clinica,
        'correo_cliente': correo_cliente,
        'mascota': mascotaSeleccionada,
        'fecha': fechaSeleccionada,
        'hora': horaSeleccionada,
        'estado': 1,
        'fecha_agrega_reserva': pd.Timestamp.now().strftime('%Y-%m-%d'),
        'hora_agrega_reserva': pd.Timestamp.now().strftime('%H:%M:%S')
    }
    
    # Append the new reservation to the CSV file
    with open('data/reservas.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_reservation.keys(), delimiter=';')
        writer.writerow(new_reservation)
        confirmar_url = url_for('agendar', ac=1, c=1, r=max_id_reserva+1, _external=True)
        cancelar_url = url_for('agendar', ac=1, c=0, r=max_id_reserva+1, _external=True)

        msg = Message("Tu hora ha sido agendada",
                    sender="alhen1970@gmail.com",
                    recipients=[correo_cliente])
        msg.html = f"""
        <p>Hola, {nombre_cliente}, gracias por agendar una hora para tu mascota en:</p>
        <p><b><li>Clínica veterinaria:</b> {id_clinica}</p>
        <p><b><li>Fecha:</b> {fechaSeleccionada}</p>
        <p><b><li>Hora:</b> {horaSeleccionada}</p>
        <p><b><li>Reserva Número:</b> {max_id_reserva + 1}</p>
        <p><a href="{confirmar_url}">Confirmar</a></p>
        <p><a href="{cancelar_url}">Cancelar</a></p>
        """
        mail.send(msg)
        correo_enviado=True
    if correo_enviado:
        return jsonify({"message": "Reserva creada y correo enviado"}), 200
    else:
        return jsonify({"error": "No se pudo enviar el correo"}), 500
    
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
    return render_template("iniciar_sesion.html")

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

    # Convertir columna fecha a datetime
    df_reservas["fecha"] = pd.to_datetime(df_reservas["fecha"], format="%d-%m-%Y")
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
def confirmar_cita():
    data = request.get_json(silent=True)
    if data is None:
        print("[ERROR] No se recibió un cuerpo JSON válido en /confirmar_cita")
        return jsonify({"success": False, "error": "JSON inválido o vacío"}), 400    
    print(f"[INFO] Datos recibidos en confirmar_cita: {data}")
    user = session.get("user", None)
    #si no hay usuario, entonces redirigimos a la página de inicio de sesión
    session['next'] = request.full_path
    print(f"[INFO] next: {request.full_path}")
    if not user:
        return redirect(url_for("login"))    
    
    id_cita = int(data["id_cita"])


    print(f"[INFO] Datos recibidos en cancelar_cita: {id_cita}")
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
            return jsonify({"success": True})
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


if __name__ == "__main__":
    app.run(debug=True)

