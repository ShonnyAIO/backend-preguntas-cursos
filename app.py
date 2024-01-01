import jwt
from datetime import date
from functools import wraps
from json import JSONEncoder
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_pymongo import PyMongo

from bson import json_util
from bson.objectid import ObjectId

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj): return json_util.default(obj)

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
app.config['MONGO_URI'] = 'mongodb://localhost:27017/microscopica_course'
cors = CORS(app, resources={r"*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'laboratorio_microscopica_2024'
mongo = PyMongo(app)

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'No estas autorizado para esto'})
        try:
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms="HS256")
            current_user = mongo.db.estudiantes.find_one(
                {"_id": ObjectId(data['_id'])})
        except:
            return jsonify({'message': 'Token es invalido'})

        return f(current_user, *args, **kwargs)
    return decorator

# REGISTRAR ESTUDIANTE
@app.route('/estudiantes', methods=['POST'])
def create_estudiante():
    nombre = str(request.json['nombre']),
    apellido = request.json['apellido'],
    cedula = request.json['cedula'],
    correo_electronico = request.json['correo_electronico']

    if(nombre and apellido and cedula and correo_electronico):
        estudianteInfo = mongo.db.estudiantes.find_one({'cedula' : cedula[0]})
        if(estudianteInfo == None):
            estudianteInfo = mongo.db.estudiantes.find_one({'correo_electronico' : correo_electronico[0] })
        if(estudianteInfo != None):
            if((estudianteInfo['correo_electronico'] == correo_electronico[0]) and (estudianteInfo['cedula'] == cedula[0])):
                message = {'message': 'Lo sentimos, el correo electronico y la cedula de identidad existen, intenta otro nuevamente', 'status': 401}
                response = jsonify(message)
                response.status_code = 401
                return response
            elif(estudianteInfo['cedula'] == cedula[0]):
                message = {'message': 'Lo sentimos, la cedula de identidad existe, intenta otro nuevamente', 'status': 401}
                response = jsonify(message)
                response.status_code = 401
                return response
            elif(estudianteInfo['correo_electronico'] == correo_electronico[0]):
                message = {'message': 'Lo sentimos, el correo electronico existe, intenta otro nuevamente', 'status': 401}
                response = jsonify(message)
                response.status_code = 401
                return response
            else:
                estudianteNew = mongo.db.estudiantes.insert_one({'nombre' : nombre[0], 'apellido' : apellido[0], 'cedula' : cedula[0], 'correo_electronico' : correo_electronico})
                print(estudianteNew)
                return {' message' : 'Estudiante registrado', 'status' : 200}
        else:
            estudianteNew = mongo.db.estudiantes.insert_one({'nombre' : nombre[0], 'apellido' : apellido[0], 'cedula' : cedula[0], 'correo_electronico' : correo_electronico})
            print(estudianteNew)
            return {'message' : 'Estudiante registrado', 'status' : 200}
    else:
        message = {
            'message': 'Parametros invalidos los datos son: Nombre, Apellido, Cedula Identidad, Correo Electronico',
        }
        response = jsonify(message)
        response.status_code = 401
        return response

# INICIAR SESION ESTUDIANTE
@app.route('/login', methods=['POST'])
def login():
    correo_electronico = request.json['correo_electronico']
    cedula = request.json['cedula']

    if correo_electronico and cedula:
        estudiante = mongo.db.estudiantes.find_one(
            {'cedula': cedula})
        if estudiante:
                token = jwt.encode({'_id': str(
                    estudiante['_id']), 'cedula': estudiante['cedula']}, app.config['SECRET_KEY'], algorithm="HS256") # .decode('utf-8')
                response = ({
                    'token': token,
                    'cedula': estudiante['cedula']
                })
                return response
        else:
            message = {
                'message': 'Estudiante no registrado'
            }
            response = jsonify(message)
            response.status_code = 401
            return response
    else:
        message = {
            'message': 'Parametros invalidos'
        }
        response = jsonify(message)
        response.status_code = 401
        return response
    
@app.route("/preguntas/<string:number>", methods=["GET"])
@token_required
def getPreguntas(self, number):
    preguntas = mongo.db.preguntas.find({ 'claseID' : int(number)})
    response = json_util.dumps(preguntas)
    return Response(response, mimetype="application/json")

@app.route("/resultados", methods=["POST"])
@token_required
def postResultados(self):

    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms="HS256")
    # current_user = mongo.db.estudiantes.find_one({"_id": ObjectId(data['_id'])})

    puntaje = request.json['puntaje']
    preguntas = request.json['preguntas']

    if(puntaje and preguntas):

        fecha = str(date.today())

        print({'estudianteID' : str(data['_id']), 'puntaje' : puntaje, 'fecha' : fecha, 'preguntas' : preguntas})

        newPuntaje = mongo.db.resultados.insert_one({'estudianteID' : str(data['_id']), 'puntaje' : puntaje, 'fecha' : fecha, 'preguntas' : preguntas})
        print(newPuntaje.inserted_id)

        return {'message' : 'Resultados registrado con exito!!', 'resultado' : str(newPuntaje.inserted_id), 'status' : 200}

    else:
        message = {
            'message': 'Parametros invalidos'
        }
        response = jsonify(message)
        response.status_code = 401
        return response    
