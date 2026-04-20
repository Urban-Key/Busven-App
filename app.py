from flask import Flask, render_template, request
import sqlite3
import random
import string
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime

app = Flask(__name__)

# =========================
# BASE DE DATOS
# =========================
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS boletos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            documento TEXT,
            correo TEXT,
            origen TEXT,
            destino TEXT,
            fecha TEXT,
            hora TEXT,
            codigo TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# =========================
# TERMINALES (GLOBAL 🔥)
# =========================
terminales = {
    "Cúcuta": "Terminal de Transportes Cúcuta, Norte de Santander",
    "San Cristóbal": "Terminal de Pasajeros Genaro Méndez",
    "Caracas": "Terminal La Bandera",
    "Maracaibo": "Terminal de Pasajeros de Maracaibo"
}

# =========================
# PAGINA PRINCIPAL
# =========================
@app.route('/')
def index():
    return render_template('index.html')

# =========================
# BUSCAR VIAJES
# =========================
@app.route('/viajes', methods=['POST'])
def viajes():

    origen_raw = request.form['origen']
    destino_raw = request.form['destino']
    fecha = request.form['fecha']
    pasajeros = request.form['pasajeros']

    ciudades = {
        "cúcuta": "Cúcuta",
        "san cristobal": "San Cristóbal",
        "caracas": "Caracas",
        "maracaibo": "Maracaibo"
    }

    origen = ciudades.get(origen_raw.lower(), origen_raw)
    destino = ciudades.get(destino_raw.lower(), destino_raw)

    salida_terminal = terminales.get(origen, f"Terminal de {origen}")
    llegada_terminal = terminales.get(destino, f"Terminal de {destino}")

    lista_viajes = [
        {
            "hora": "05:00 AM",
            "precio": "Ref. 35,00",
            "bs": "Bs. 16.675,20",
            "salida": salida_terminal,
            "llegada": llegada_terminal
        },
        {
            "hora": "09:00 AM",
            "precio": "Ref. 40,00",
            "bs": "Bs. 19.000,00",
            "salida": salida_terminal,
            "llegada": llegada_terminal
        },
        {
            "hora": "05:00 PM",
            "precio": "Ref. 45,00",
            "bs": "Bs. 21.000,00",
            "salida": salida_terminal,
            "llegada": llegada_terminal
        }
    ]

    return render_template(
        'viajes.html',
        viajes=lista_viajes,
        origen=origen,
        destino=destino,
        fecha=fecha,
        pasajeros=pasajeros
    )

# =========================
# COMPRAR
# =========================
@app.route('/comprar', methods=['POST'])
def comprar():
    origen = request.form['origen']
    destino = request.form['destino']
    fecha = request.form['fecha']
    pasajeros = int(request.form['pasajeros'])
    hora = request.form['hora']

    precio_usd = 35
    tasa = 476.43
    precio_bs = precio_usd * tasa

    return render_template(
        'datos.html',
        origen=origen,
        destino=destino,
        fecha=fecha,
        hora=hora,
        pasajeros=pasajeros,
        precio_usd=precio_usd,
        precio_bs=precio_bs,
        tasa=tasa
    )

# =========================
# ASIENTOS
# =========================
@app.route('/asientos', methods=['POST'])
def asientos():

    origen = request.form.get('origen')
    destino = request.form.get('destino')
    fecha = request.form.get('fecha')
    hora = request.form.get('hora')

    pasajeros = int(request.form.get('pasajeros', 1))

    nombres = request.form.getlist('nombre[]')
    documentos = request.form.getlist('documento[]')
    correo = request.form.get('correo')

    return render_template(
        'asientos.html',
        origen=origen,
        destino=destino,
        fecha=fecha,
        hora=hora,
        pasajeros=pasajeros,
        nombres=nombres,
        documentos=documentos,
        correo=correo
    )

# =========================
# PAGO
# =========================
@app.route('/pago', methods=['POST'])
def pago():

    origen = request.form['origen']
    destino = request.form['destino']
    fecha = request.form['fecha']
    hora = request.form['hora']
    pasajeros = request.form.get('pasajeros', len(request.form.getlist('nombre[]')))
    asientos = request.form['asientos']

    nombres = request.form.getlist('nombre[]')
    documentos = request.form.getlist('documento[]')
    correo = request.form['correo']

    precio = "Ref. 35,00"
    bs = "Bs. 16.675,20"

    return render_template(
        'pago.html',
        origen=origen,
        destino=destino,
        fecha=fecha,
        hora=hora,
        pasajeros=pasajeros,
        asientos=asientos,
        nombres=nombres,
        documentos=documentos,
        correo=correo,
        precio=precio,
        bs=bs
    )

# =========================
# CONFIRMAR PAGO
# =========================
@app.route('/confirmar_pago', methods=['POST'])
def confirmar_pago():

    origen = request.form.get("origen")
    destino = request.form.get("destino")
    fecha = request.form.get("fecha")
    hora = request.form.get("hora")
    pasajeros = request.form.get("pasajeros")
    asientos = request.form.get("asientos")

    nombres = request.form.getlist("nombre[]")
    documentos = request.form.getlist("documento[]")
    correo = request.form.get("correo")
    metodo = request.form.get("metodo")

    # TERMINALES 🔥
    salida_terminal = terminales.get(origen, f"Terminal de {origen}")
    llegada_terminal = terminales.get(destino, f"Terminal de {destino}")

    codigo = ''.join(random.choices(string.ascii_uppercase, k=5))

    BASE_URL = request.host_url.rstrip('/')

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={BASE_URL}/boleto/{codigo}"

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    for i in range(len(nombres)):
        c.execute("""
            INSERT INTO boletos (nombre, documento, correo, origen, destino, fecha, hora, codigo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombres[i],
            documentos[i],
            correo,
            origen,
            destino,
            fecha,
            hora,
            codigo
        ))

    conn.commit()
    conn.close()

    return render_template(
        "boleto.html",
        origen=origen,
        destino=destino,
        salida_terminal=salida_terminal,
        llegada_terminal=llegada_terminal,
        fecha=fecha,
        hora=hora,
        pasajeros=pasajeros,
        asientos=asientos,
        nombres=nombres,
        documentos=documentos,
        correo=correo,
        metodo=metodo,
        codigo=codigo,
        estado="ACTIVO",
        precio="Ref. 35,00",
        bs="Bs. 16.675,20",
        qr=qr_url
    )

# =========================
# VER BOLETO (QR)
# =========================
@app.route('/boleto/<codigo>')
def ver_boleto_qr(codigo):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        SELECT nombre, documento, origen, destino, fecha, hora
        FROM boletos
        WHERE codigo = ?
    """, (codigo,))

    data = c.fetchone()
    conn.close()

    if not data:
        return "❌ Boleto no encontrado"

    nombre, documento, origen, destino, fecha, hora = data

    salida_terminal = terminales.get(origen, f"Terminal de {origen}")
    llegada_terminal = terminales.get(destino, f"Terminal de {destino}")

    BASE_URL = request.host_url.rstrip('/')

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={BASE_URL}/boleto/{codigo}"

    return render_template(
        'ticket.html',
        nombre=nombre,
        documento=documento,
        origen=origen,
        destino=destino,
        salida_terminal=salida_terminal,
        llegada_terminal=llegada_terminal,
        fecha=fecha,
        hora=hora,
        codigo=codigo,
        qr=qr_url,
        estado="ACTIVO",
        precio="Ref. 35,00"
    )
@app.route('/descargar_pdf/<codigo>')
def descargar_pdf(codigo):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        SELECT nombre, documento, origen, destino, fecha, hora
        FROM boletos
        WHERE codigo = ?
    """, (codigo,))

    data = c.fetchone()
    conn.close()

    if not data:
        return "Boleto no encontrado"

    nombre, documento, origen, destino, fecha, hora = data

    import io
    buffer = io.BytesIO()

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors

    p = canvas.Canvas(buffer, pagesize=letter)

    # 🔥 FONDO TIPO TARJETA
    p.setFillColorRGB(0.95, 0.96, 1)
    p.roundRect(50, 400, 500, 300, 20, fill=1)

    # 🔵 HEADER
    p.setFillColorRGB(0.18, 0.19, 0.57)
    p.roundRect(50, 650, 500, 50, 20, fill=1)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 665, "DETALLE DEL BOLETO")

    # TEXTO
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 12)

    p.drawString(80, 610, f"Pasajero: {nombre}")
    p.drawString(80, 590, f"Documento: {documento}")

    p.drawString(80, 550, f"Origen: {origen}")
    p.drawString(80, 530, f"Destino: {destino}")

    p.drawString(80, 490, f"Fecha: {fecha}")
    p.drawString(80, 470, f"Hora: {hora}")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(80, 430, f"Código: {codigo}")

    # QR (imagen)
    import urllib.request
    BASE_URL = request.host_url.rstrip('/')

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={BASE_URL}/boleto/{codigo}"

    try:
        urllib.request.urlretrieve(qr_url, "qr_temp.png")
        p.drawImage("qr_temp.png", 400, 460, 120, 120)
    except:
        pass

    p.showPage()
    p.save()

    buffer.seek(0)

    from flask import make_response
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=boleto_{codigo}.pdf'

    return response

# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run(debug=True)
