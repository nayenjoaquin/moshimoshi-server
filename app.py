from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mysqldb import MySQL
from config import DevelopmentConfig
import smtplib
import uuid
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)
app.config.from_object(DevelopmentConfig)
db = MySQL(app)

def cleanOrders():
    with app.app_context():
        cur = db.connection.cursor()
        cur.execute("DELETE FROM pedido WHERE estado='new'")
        db.connection.commit()
    print("limpiando pedidos")
    return

scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanOrders, trigger="interval", days=2)
scheduler.start()


@app.route('/getMangasByPage/<page>')
def getMangasByPage(page):
    cur = db.connection.cursor()
    cur.execute('''SELECT * FROM manga ORDER BY stock = 0, name LIMIT 40 OFFSET {}'''.format((int(page)-1)*40))
    data = cur.fetchall()
    return jsonify(data)

@app.route('/getMangasNameList')
def getMangasNameList():
    cur = db.connection.cursor()
    cur.execute('''SELECT name,id FROM manga''')
    data = cur.fetchall()
    return jsonify(data)

@app.route('/getMangasByName/<name>')
def getMangasByName(name):
    cur = db.connection.cursor()
    cur.execute('''SELECT * FROM manga
                WHERE manga.name LIKE "%{}%"'''.format(name))
    data = cur.fetchall()
    return jsonify(data)

@app.route('/getManga/<id>')
def getMangaById(id):
    cur = db.connection.cursor()
    cur.execute('''SELECT * FROM manga
                WHERE manga.id={}'''.format(id))
    data = cur.fetchall()
    return jsonify(data)

@app.route('/newManga', methods=['POST'])
def newManga():
    return 'agregando mangas'


@app.route('/deleteManga/<id>')
def deleteManga(id):
    return 'eliminando manga'


@app.route('/updateManga', methods=['POST'])
def updateManga():
    return 'actualizando stock'

@app.route('/newOrder', methods=['POST'])
def newOrder():
    orderId=uuid.uuid1().hex
    order = request.json
    envio = "{}, {}, {}".format(order['direccion'],order['ciudad'],order['region'])
    cur = db.connection.cursor()
    cur.execute('''INSERT INTO pedido VALUES ("{}", "{}", "{}", "{}", {}, {}, CURRENT_TIMESTAMP, "new")'''.format(orderId,order['nombre'],order['correo'],envio,order['telefono'],order['total']))
    for item in order['carrito']:
        cur.execute('''INSERT INTO item_pedido VALUES
        ({}, "{}", {})'''.format(item['mangaID'],orderId,item['amount']))
    db.connection.commit()
    sendOrderMail(order,orderId,envio)
    
    return jsonify(orderId)


def sendOrderMail(order,orderId,envio):
    subject = "NUEVO PEDIDO N°:{}".format(orderId)
    message = '''{} ha realizado un nuevo pedido.

PRODUCTOS:
{}

TOTAL: ${}

DIRECCIÓN DE ENVÍO: {}

CLICK PARA CONFIRMAR PEDIDO: https://moshimoshi-server.herokuapp.com/confirmOrder/{}
    '''.format(order['nombre'],order['productos'],order['total'],envio,orderId)
    body = "Subject: {}\r\n{}".format(subject,message)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("mangasmoshimoshi@gmail.com","xqnktwaiwvarfafy")
    server.sendmail("noreply@gmail.com", "mangasmoshimoshi@gmail.com", body.encode('utf-8'))

@app.route('/confirmOrder/<orderId>')
def confirmOrder(orderId):
    cur = db.connection.cursor()
    cur.execute('SELECT estado FROM pedido WHERE orderId="{}"'.format(orderId))
    orderStatus = cur.fetchone()[0]
    if orderStatus == "new":
        cur.execute('''SELECT * FROM item_pedido WHERE pedidoID="{}"'''.format(orderId))
        orderItems = cur.fetchall()
        for item in orderItems:
            cur.execute('''UPDATE manga
            SET stock = stock-{}
            WHERE id={}'''.format(item[2],item[0]))
            cur.execute('''INSERT INTO linea_venta VALUES({},"{}",{})'''.format(item[0],orderId,item[2]))
        
        cur.execute('''DELETE FROM item_pedido
        WHERE pedidoID="{}"'''.format(orderId))
        cur.execute('UPDATE pedido SET estado="confirmado" WHERE orderId="{}"'.format(orderId))
        db.connection.commit()
        return "CONFIRMANDO PEDIDO NRO {}".format(orderId)
    else:
        return "ESTE PEDIDO YA HA SIDO CONFIRMADO"

atexit.register(lambda: scheduler.shutdown())