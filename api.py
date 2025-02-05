from flask import Blueprint, jsonify, request
from models import Producto, Venta, Cliente

api = Blueprint('api', __name__)

@api.route('/api/productos', methods=['GET'])
def get_productos():
    # API REST para acceso externo
    pass

@api.route('/api/ventas', methods=['POST'])
def create_venta():
    # Crear ventas vía API
    pass