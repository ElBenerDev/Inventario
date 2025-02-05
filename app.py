from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from models import Usuario, Producto, Cliente, Venta, ItemVenta, LogAuditoria
from session_manager import SessionManager, login_required, role_required
from werkzeug.security import generate_password_hash
from notifications import NotificationSystem

app = Flask(__name__)
app.secret_key = 'clave_secreta_del_sistema'  # Cambiar en producción

# Inicialización de variables globales
global usuarios, productos, clientes, ventas, logs_auditoria, notification_system
usuarios = []
productos = []
clientes = []
ventas = []
logs_auditoria = []
notification_system = NotificationSystem()

# Crear usuario admin inicial
admin_user = Usuario(
    id=1,
    username="ElBenerDev",
    email="admin@sistema.com",
    nombre_completo="Administrador del Sistema",
    role="admin",
    password_hash=generate_password_hash("admin123"),
    created_at=datetime.now(),
    updated_at=datetime.now(),
    created_by=1,
    is_active=True
)
usuarios.append(admin_user)

@app.context_processor
def utility_processor():
    def get_unread_notifications():
        if SessionManager.get_current_user_id():
            return notification_system.get_user_notifications(SessionManager.get_current_user_id())
        return []
    
    return {
        'get_current_username': SessionManager.get_current_username,
        'get_current_user_role': SessionManager.get_current_user_role,
        'get_current_user_id': SessionManager.get_current_user_id,
        'notification_system': notification_system,
        'get_unread_notifications': get_unread_notifications
    }


@app.route('/notificaciones')
@login_required
def ver_notificaciones():
    user_id = SessionManager.get_current_user_id()
    include_read = request.args.get('include_read', 'false').lower() == 'true'
    notificaciones = notification_system.get_user_notifications(user_id, include_read)
    return render_template('notificaciones.html', notificaciones=notificaciones)

@app.route('/notificaciones/marcar-leida/<int:notification_id>', methods=['POST'])
@login_required
def marcar_notificacion_leida(notification_id):
    user_id = SessionManager.get_current_user_id()
    success = notification_system.mark_as_read(notification_id, user_id)
    return jsonify({'success': success})


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está autenticado, redirigir al index
    if SessionManager.get_current_user_id():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = next((u for u in usuarios if u.username == username), None)
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Su cuenta está desactivada', 'error')
                return redirect(url_for('login'))
            
            SessionManager.set_user_session(user.id, user.username, user.role)
            user.last_login = datetime.now()
            
            # Registrar log de inicio de sesión
            log = LogAuditoria(
                usuario_id=user.id,
                accion="login",
                tabla="usuarios",
                registro_id=user.id,
                ip=request.remote_addr if request.remote_addr else "127.0.0.1"
            )
            logs_auditoria.append(log)
            
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
        
        flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user_id = SessionManager.get_current_user_id()
    if user_id:
        # Registrar log de cierre de sesión
        log = LogAuditoria(
            usuario_id=user_id,
            accion="logout",
            tabla="usuarios",
            registro_id=user_id,
            ip=request.remote_addr if request.remote_addr else "127.0.0.1"
        )
        logs_auditoria.append(log)
    
    SessionManager.clear_session()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Calcular estadísticas
    total_inventario = sum(p.precio_costo * p.stock for p in productos)
    ganancia_potencial = sum((p.precio_venta - p.precio_costo) * p.stock for p in productos)
    
    # Calcular ganancia real de las ventas
    ganancia_real = sum(
        sum((item.precio_unitario - next(
            (p.precio_costo for p in productos if p.id == item.producto_id), 0
        )) * item.cantidad for item in venta.items)
        for venta in ventas
    )
    
    stats = {
        'total_productos': len(productos),
        'total_clientes': len(clientes),
        'total_ventas': len(ventas),
        'productos_sin_stock': len([p for p in productos if p.stock <= p.stock_minimo]),
        'usuario_actual': SessionManager.get_current_username(),
        'total_inventario': total_inventario,
        'ganancia_potencial': ganancia_potencial,
        'ganancia_real': ganancia_real
    }
    return render_template('index.html', stats=stats)

@app.route('/productos', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'inventario'])
def gestionar_productos():
    if request.method == 'POST':
        try:
            current_user_id = SessionManager.get_current_user_id()
            producto = Producto(
                id=len(productos) + 1,
                codigo=request.form['codigo'],
                nombre=request.form['nombre'],
                categoria=request.form['categoria'],
                descripcion=request.form['descripcion'],
                precio_costo=float(request.form['precio_costo']),
                precio_venta=float(request.form['precio_venta']),
                stock=int(request.form['stock']),
                stock_minimo=int(request.form['stock_minimo']),
                unidad_medida=request.form['unidad_medida'],
                ubicacion=request.form['ubicacion'],
                created_by=current_user_id,
                updated_by=current_user_id
            )
            productos.append(producto)
            
            # Registrar log de creación
            log = LogAuditoria(
                usuario_id=current_user_id,
                accion="crear",
                tabla="productos",
                registro_id=producto.id,
                datos_nuevos=producto.dict(),
                ip=request.remote_addr if request.remote_addr else "127.0.0.1"
            )
            logs_auditoria.append(log)
            
            flash('Producto agregado exitosamente', 'success')
        except Exception as e:
            flash(f'Error al agregar producto: {str(e)}', 'error')
        return redirect(url_for('gestionar_productos'))
    
    # Calcular totales para la vista
    total_inventario = sum(p.precio_costo * p.stock for p in productos)
    ganancia_potencial = sum((p.precio_venta - p.precio_costo) * p.stock for p in productos)
    ganancia_real = sum(
        sum((item.precio_unitario - next(
            (p.precio_costo for p in productos if p.id == item.producto_id), 0
        )) * item.cantidad for item in venta.items)
        for venta in ventas
    )
    
    return render_template('productos.html', 
                         productos=productos,
                         current_user_role=SessionManager.get_current_user_role(),
                         total_inventario=total_inventario,
                         ganancia_potencial=ganancia_potencial,
                         ganancia_real=ganancia_real)

@app.route('/producto/<int:id>', methods=['DELETE'])
@login_required
@role_required(['admin', 'inventario'])
def eliminar_producto(id):
    current_user_id = SessionManager.get_current_user_id()
    producto = next((p for p in productos if p.id == id), None)
    
    if producto:
        # Registrar log antes de eliminar
        log = LogAuditoria(
            usuario_id=current_user_id,
            accion="eliminar",
            tabla="productos",
            registro_id=id,
            datos_anteriores=producto.dict(),
            ip=request.remote_addr if request.remote_addr else "127.0.0.1"
        )
        logs_auditoria.append(log)
        
        productos[:] = [p for p in productos if p.id != id]
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

@app.route('/productos/<int:id>', methods=['PUT'])
@login_required
@role_required(['admin', 'inventario'])
def actualizar_producto(id):
    producto = next((p for p in productos if p.id == id), None)
    if not producto:
        return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404
    
    data = request.json
    precio_anterior = producto.precio_venta
    
    # Actualizar producto
    for key, value in data.items():
        if hasattr(producto, key):
            setattr(producto, key, value)
    
    # Si el precio cambió, crear notificación
    if precio_anterior != producto.precio_venta:
        notification_system.notify_price_changes(
            producto,
            precio_anterior,
            [u for u in usuarios if u.role in ['admin', 'vendedor']]
        )
    
    return jsonify({'success': True})


@app.route('/clientes', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'vendedor'])
def gestionar_clientes():
    if request.method == 'POST':
        try:
            current_user_id = SessionManager.get_current_user_id()
            cliente = Cliente(
                id=len(clientes) + 1,
                nombre=request.form['nombre'],
                email=request.form['email'],
                telefono=request.form['telefono'],
                direccion=request.form['direccion'],
                tipo_cliente=request.form['tipo_cliente'],
                notas=request.form['notas'],
                created_by=current_user_id,
                updated_by=current_user_id
            )
            clientes.append(cliente)
            
            # Registrar log de creación
            log = LogAuditoria(
                usuario_id=current_user_id,
                accion="crear",
                tabla="clientes",
                registro_id=cliente.id,
                datos_nuevos=cliente.dict(),
                ip=request.remote_addr if request.remote_addr else "127.0.0.1"
            )
            logs_auditoria.append(log)
            
            flash('Cliente agregado exitosamente', 'success')
        except Exception as e:
            flash(f'Error al agregar cliente: {str(e)}', 'error')
        return redirect(url_for('gestionar_clientes'))
    
    return render_template('clientes.html', clientes=clientes)

@app.route('/ventas', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'vendedor'])
def gestionar_ventas():
    if request.method == 'POST':
        try:
            current_user_id = SessionManager.get_current_user_id()
            data = request.json
            items = []
            
            # Crear items de venta usando el precio de venta del producto
            for item_data in data['items']:
                producto = next((p for p in productos if p.id == item_data['producto_id']), None)
                if producto:
                    item = ItemVenta(
                        producto_id=producto.id,
                        cantidad=item_data['cantidad'],
                        precio_unitario=producto.precio_venta,
                        subtotal=producto.precio_venta * item_data['cantidad']
                    )
                    items.append(item)
            
            venta = Venta(
                id=len(ventas) + 1,
                cliente_id=data['cliente_id'],
                items=items,
                total=sum(item.subtotal for item in items),
                estado=data.get('estado', 'completada'),
                notas=data.get('notas', ''),
                created_by=current_user_id,
                updated_by=current_user_id
            )
            
            # Verificar y actualizar stock
            for item in items:
                producto = next((p for p in productos if p.id == item.producto_id), None)
                if producto:
                    if producto.stock >= item.cantidad:
                        producto.stock -= item.cantidad
                        producto.updated_by = current_user_id
                        producto.updated_at = datetime.now()
                    else:
                        return jsonify({
                            'success': False,
                            'message': f'Stock insuficiente para {producto.nombre}'
                        }), 400
            
            ventas.append(venta)
            
            # Registrar log de venta
            log = LogAuditoria(
                usuario_id=current_user_id,
                accion="crear",
                tabla="ventas",
                registro_id=venta.id,
                datos_nuevos=venta.dict(),
                ip=request.remote_addr if request.remote_addr else "127.0.0.1"
            )
            logs_auditoria.append(log)
            
            return jsonify({'success': True, 'venta_id': venta.id})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('ventas.html', 
                         ventas=ventas, 
                         productos=productos, 
                         clientes=clientes)

@app.route('/logs')
@login_required
@role_required(['admin'])
def ver_logs():
    return render_template('logs.html', logs=logs_auditoria, usuarios=usuarios)

@app.context_processor
def utility_processor():
    return {
        'get_current_username': SessionManager.get_current_username,
        'get_current_user_role': SessionManager.get_current_user_role
    }

if __name__ == '__main__':
    # Agregar datos de ejemplo
    productos.append(Producto(
        id=1,
        codigo="P001",
        nombre="Producto Demo",
        categoria="General",
        precio_costo=80.00,
        precio_venta=100.00,
        stock=50,
        stock_minimo=10,
        unidad_medida="unidad",
        created_by=1,
        updated_by=1
    ))
    
    clientes.append(Cliente(
        id=1,
        nombre="Cliente Demo",
        email="demo@example.com",
        telefono="123456789",
        created_by=1,
        updated_by=1
    ))
    
    app.run(debug=True)