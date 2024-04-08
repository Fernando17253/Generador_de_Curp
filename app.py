from flask import Flask, redirect, render_template, request, url_for
import re
from datetime import datetime
import os
import qrcode

app = Flask(__name__)



def guardar_curp(curp):
    archivo_curps = "curps.txt"
    if curp_existe(curp, archivo_curps):
        return False
    else:
        with open(archivo_curps, "a") as file:
            file.write(curp + "\n")
        return True

def curp_existe(curp, archivo_curps):
    if not os.path.exists(archivo_curps):
        return False
    with open(archivo_curps, "r") as file:
        curps = file.read().splitlines()
    return curp in curps

def generar_codigo_qr(curp):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(curp)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"static/qr_{curp}.png")


def obtener_entidad(entidad):
    claves_entidad = {
        "Aguascalientes": "AS", 
        "Baja California": "BC", 
        "Baja California Sur": "BS",
        "Campeche": "CC", 
        "Coahuila": "CL", 
        "Colima": "CM", 
        "Chiapas": "CS",
        "Chihuahua": "CH", 
        "Ciudad de México": "DF", 
        "Durango": "DG",
        "Guanajuato": "GT", 
        "Guerrero": "GR", 
        "Hidalgo": "HG", "Jalisco": "JC",
        "México": "MC", 
        "Michoacán": "MN", 
        "Morelos": "MS", 
        "Nayarit": "NT",
        "Nuevo León": "NL", 
        "Oaxaca": "OC", 
        "Puebla": "PL", 
        "Querétaro": "QT",
        "Quintana Roo": "QR", 
        "San Luis Potosí": "SP", 
        "Sinaloa": "SL", 
        "Sonora": "SR",
        "Tabasco": "TC", 
        "Tamaulipas": "TS", 
        "Tlaxcala": "TL", 
        "Veracruz": "VZ",
        "Yucatán": "YN", 
        "Zacatecas": "ZS", 
        "Nacido en el Extranjero": "NE"
    }
    entidad_normalizada = entidad.title()
    
    return claves_entidad.get(entidad_normalizada, "NE")



@app.route('/generar', methods=['POST'])
def generar():
    nombre1 = request.form.get('nombre1')
    nombrenum2 = request.form.get('nombre2', '').strip().upper()
    apellido_paterno = request.form.get('apellido_paterno')
    apellido_materno = request.form.get('apellido_materno')
    fecha_nacimiento = request.form.get('fecha_nacimiento')
    sexo = request.form.get('sexo')
    entidad = request.form.get('entidad_nacimiento').upper()

    nombre2 = nombrenum2 if nombrenum2 else nombre1.strip().upper()

    curp = generar_curp(nombre1, nombre2, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, entidad)
    curp = curp.replace("-", "")

    generar_codigo_qr(curp)

    if guardar_curp(curp):
        curpgenerada = 'CURP generada y guardada exitosamente: ' + curp
    else:
        curpgenerada = 'La CURP ya existe: ' + curp

    return redirect(url_for('mostrar_curp', curplista=curpgenerada, paraqr=curp))

def obtener_iniciales_y_fechas(nombre2, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, entidad):
    nombre2 = nombre2.strip().upper()
    apellido_paterno = apellido_paterno.strip().upper()
    apellido_materno = apellido_materno.strip().upper()
    fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
    
    inicial_apellido1 = apellido_paterno[0]
    primera_vocal_apellido1 = re.search(r'[AEIOU]', apellido_paterno[1:]).group(0)
    
    inicial_apellido2 = apellido_materno[0] if apellido_materno else 'X'
    inicial_nombre = nombre2[0]
    
    fecha_formato = fecha_nacimiento.strftime('%y-%m-%d')
    sexo = 'H' if sexo.startswith('Hombre') else 'M'
    codigo_entidad = obtener_entidad(entidad)
    
    return f"{inicial_apellido1}{primera_vocal_apellido1}{inicial_apellido2}{inicial_nombre}{fecha_formato}{sexo}{codigo_entidad}"

def obtener_consonantes(apellido_paterno, apellido_materno, nombre2):

    patron_consonante = re.compile(r'(?<!^)[BCDFGHJKLMNÑPQRSTVWXYZ]', re.I)

    consonante_apellido1 = patron_consonante.search(apellido_paterno[1:])
    consonante_apellido2 = patron_consonante.search(apellido_materno[1:]) if apellido_materno else None
    consonante_nombre = patron_consonante.search(nombre2[0:])

    return (consonante_apellido1.group(0) if consonante_apellido1 else 'X') + \
           (consonante_apellido2.group(0) if consonante_apellido2 else 'X') + \
           (consonante_nombre.group(0) if consonante_nombre else 'X')

def generar_homoclave(nombre2, fecha_nacimiento, apellido_paterno):
    nombre_completo = f"{nombre2}"
    consonantes = "AEIOU"
    consonantes_nombre = ''.join([letra for letra in nombre_completo if letra.upper() in consonantes])
        
    fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
    fecha_formato = fecha_nacimiento.strftime('%m')

    homoclave = consonantes_nombre[1] + fecha_formato[-1:] if len(consonantes_nombre) >= 1 else "XX"
    return homoclave

def generar_curp(nombre1, nombre2, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, entidad):
    iniciales_y_fechas = obtener_iniciales_y_fechas(nombre2, apellido_paterno, apellido_materno, fecha_nacimiento, sexo, entidad)
    consonantes = obtener_consonantes(apellido_paterno, apellido_materno, nombre2)
    homoclave = generar_homoclave(nombre2,fecha_nacimiento, apellido_paterno)  # Aquí puedes llamar a una función que genere una homoclave basada en lógica específica
    return f"{iniciales_y_fechas}{consonantes}{homoclave}".upper()

@app.route('/mostrar_curp/<curplista>,<paraqr>')
def mostrar_curp(curplista, paraqr):
    return render_template('mostrar_curp.html', curpvisualizada=curplista, paraqr=paraqr)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)