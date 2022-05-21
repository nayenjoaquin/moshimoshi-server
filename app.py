from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
from flask_mysqldb import MySQL
from config import DevelopmentConfig

app = Flask(__name__)
cors = CORS(app)
app.config.from_object(DevelopmentConfig)
db = MySQL(app)


@app.route('/getMangas')
@cross_origin()
def getMangas():
    cur = db.connection.cursor()
    cur.execute('''SELECT * FROM manga''')
    data = cur.fetchall()
    return jsonify(data)


@app.route('/getMangasByName/<name>')
@cross_origin()
def getMangasByName(name):
    cur = db.connection.cursor()
    cur.execute('''SELECT * FROM manga
                WHERE manga.name LIKE "%{}%"'''.format(name))
    data = cur.fetchall()
    return jsonify(data)

@app.route('/getManga/<id>')
@cross_origin()
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

