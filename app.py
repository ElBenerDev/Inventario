from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import json
from models import Producto, Cliente, Venta, ItemVenta

app = Flask(__name__)
app.secret_key = 'clave_secreta_del_sistema'  # Cambiar en producción

# Almacenamiento temporal en memoria
productos = []
clientes = []
ventas = []

@app.route('/')
def index():
    # Estadísticas básicas para el dashboard
    stats = {
        'total_productos': len(productos),
        'total_clientes': len(clientes),
        'total_ventas': len(ventas),
        'productos_sin_stock': len([p for p in productos if p.stock <= p.stock_minimo])
    }
    return render_template('index.html', stats=stats)

@app.route('/productos', methods=['GET', 'POST'])
def gestionar_productos():
    if request.method == 'POST':
        try:
            producto = Producto(
                id=len(productos) + 1,
                codigo=request.form['codigo'],
                nombre=request.form['nombre'],
                categoria=request.form['categoria'],
                descripcion=request.form['descripcion'],
                precio=float(request.form['precio']),
                stock=int(request.form['stock']),
                stock_minimo=int(request.form['stock_minimo']),
                unidad_medida=request.form['unidad_medida'],
                ubicacion=request.form['ubicacion']
            )
            productos.append(producto)
            flash('Producto agregado exitosamente', 'success')
        except Exception as e:
            flash(f'Error al agregar producto: {str(e)}', 'error')
        return redirect(url_for('gestionar_productos'))
    
    return render_template('productos.html', productos=productos)

@app.route('/producto/<int:id>', methods=['DELETE'])
def eliminar_producto(id):
    global productos
    productos = [p for p in productos if p.id != id]
    return jsonify({'success': True})

@app.route('/clientes', methods=['GET', 'POST'])
def gestionar_clientes():
    if request.method == 'POST':
        try:
            cliente = Cliente(
                id=len(clientes) + 1,
                nombre=request.form['nombre'],
                email=request.form['email'],
                telefono=request.form['telefono'],
                direccion=request.form['direccion'],
                tipo_cliente=request.form['tipo_cliente'],
                notas=request.form['notas']
            )
            clientes.append(cliente)
            flash('Cliente agregado exitosamente', 'success')
        except Exception as e:
            flash(f'Error al agregar cliente: {str(e)}', 'error')
        return redirect(url_for('gestionar_clientes'))
    
    return render_template('clientes.html', clientes=clientes)

@app.route('/ventas', methods=['GET', 'POST'])
def gestionar_ventas():
    if request.method == 'POST':
        try:
            data = request.json
            items = [ItemVenta(**item) for item in data['items']]
            
            venta = Venta(
                id=len(ventas) + 1,
                cliente_id=data['cliente_id'],
                items=items,
                total=sum(item.subtotal for item in items),
                estado=data.get('estado', 'completada'),
                notas=data.get('notas', '')
            )
            
            # Actualizar stock
            for item in items:
                for producto in productos:
                    if producto.id == item.producto_id:
                        if producto.stock >= item.cantidad:
                            producto.stock -= item.cantidad
                        else:
                            return jsonify({
                                'success': False,
                                'message': f'Stock insuficiente para {producto.nombre}'
                            }), 400
            
            ventas.append(venta)
            return jsonify({'success': True, 'venta_id': venta.id})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('ventas.html', 
                         ventas=ventas, 
                         productos=productos, 
                         clientes=clientes)

if __name__ == '__main__':
    # Agregar algunos datos de ejemplo
    productos.append(Producto(
        id=1,
        codigo="P001",
        nombre="Producto Demo",
        categoria="General",
        precio=100.00,
        stock=50,
        stock_minimo=10,
        unidad_medida="unidad"
    ))
    
    clientes.append(Cliente(
        id=1,
        nombre="Cliente Demo",
        email="demo@example.com",
        telefono="123456789"
    ))
    
    app.run(debug=True)