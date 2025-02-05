from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g
from datetime import datetime
from models import Usuario, Producto, Cliente, Venta, ItemVenta, LogAuditoria, Proveedor
from session_manager import SessionManager, login_required, role_required
from werkzeug.security import generate_password_hash
from notifications import NotificationSystem
from services.audit import AuditoriaService
from services.proveedor_service import ProveedorService

app = Flask(__name__)
app.secret_key = 'clave_secreta_del_sistema'  # Cambiar en producción

# Inicialización de variables globales
global usuarios, productos, clientes, ventas, logs_auditoria, notification_system, proveedores
usuarios = []
productos = []
clientes = []
ventas = []
logs_auditoria = []
notification_system = NotificationSystem()
proveedores = []


# Inicializar servicios
auditoria_service = AuditoriaService()
proveedor_service = ProveedorService(auditoria_service)

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
    
    def format_datetime(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else ''
    
    return {
        'get_current_username': SessionManager.get_current_username,
        'get_current_user_role': SessionManager.get_current_user_role,
        'get_current_user_id': SessionManager.get_current_user_id,
        'notification_system': notification_system,
        'get_unread_notifications': get_unread_notifications,
        'format_datetime': format_datetime,
        'current_datetime': datetime.utcnow()
    }

@app.before_request
def before_request():
    g.user = None
    user_id = SessionManager.get_current_user_id()
    if user_id:
        g.user = next((u for u in usuarios if u.id == user_id), None)

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
    
@app.route('/proveedores', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'inventario'])
def gestionar_proveedores():
    if request.method == 'POST':
        try:
            current_user_id = SessionManager.get_current_user_id()
            username = SessionManager.get_current_username()
            
            datos_proveedor = {
                'nombre': request.form['nombre'],
                'ruc': request.form['ruc'],
                'direccion': request.form['direccion'],
                'ciudad': request.form['ciudad'],
                'pais': request.form.get('pais', 'Ecuador'),
                'telefono': request.form['telefono'],
                'email': request.form['email'],
                'sitio_web': request.form.get('sitio_web'),
                'contacto_nombre': request.form['contacto_nombre'],
                'contacto_telefono': request.form['contacto_telefono'],
                'contacto_email': request.form['contacto_email'],
                'categoria': request.form['categoria'],
                'notas': request.form.get('notas'),
                'terminos_pago': request.form['terminos_pago'],
                'limite_credito': float(request.form.get('limite_credito', 0))
            }
            
            proveedor = proveedor_service.crear_proveedor(
                datos=datos_proveedor,
                usuario_id=current_user_id,
                username=username,
                ip=request.remote_addr
            )
            
            flash('Proveedor agregado exitosamente', 'success')
            return redirect(url_for('gestionar_proveedores'))
            
        except Exception as e:
            flash(f'Error al crear proveedor: {str(e)}', 'error')
            return redirect(url_for('gestionar_proveedores'))
    
    # Para solicitudes GET
    return render_template('proveedores/index.html', 
                         proveedores=proveedor_service.proveedores,
                         categorias_proveedores=[
                             "Materia Prima",
                             "Suministros",
                             "Servicios",
                             "Equipamiento",
                             "Transporte",
                             "Otros"
                         ],
                         terminos_pago=[
                             "Contado",
                             "15 días",
                             "30 días",
                             "45 días",
                             "60 días",
                             "90 días"
                         ])

@app.route('/proveedor/<int:id>', methods=['GET'])
@login_required
@role_required(['admin', 'inventario'])
def obtener_proveedor(id):
    proveedor = next((p for p in proveedores if p.id == id), None)
    if not proveedor:
        return jsonify({'error': 'Proveedor no encontrado'}), 404
    
    return jsonify(proveedor.dict())

@app.route('/proveedor/<int:id>/detalle', methods=['GET'])
@login_required
@role_required(['admin', 'inventario'])
def detalle_proveedor(id):
    proveedor = next((p for p in proveedores if p.id == id), None)
    if not proveedor:
        flash('Proveedor no encontrado', 'error')
        return redirect(url_for('gestionar_proveedores'))
    
    # Obtener productos asociados
    productos_proveedor = [p for p in productos if p.id in proveedor.productos]
    
    return render_template('proveedores/detalle.html',
                         proveedor=proveedor,
                         productos=productos,  # Todos los productos para el modal
                         productos_proveedor=productos_proveedor)  # Solo productos asociados
    
@app.route('/proveedor/<int:id>', methods=['PUT'])
@login_required
@role_required(['admin', 'inventario'])
def actualizar_proveedor(id):
    try:
        current_user_id = SessionManager.get_current_user_id()
        data = request.get_json()
        
        proveedor = next((p for p in proveedores if p.id == id), None)
        if not proveedor:
            return jsonify({'error': 'Proveedor no encontrado'}), 404

        # Guardar datos antiguos para el log
        datos_antiguos = proveedor.dict()
        
        # Actualizar campos del proveedor
        campos_actualizables = [
            'nombre', 'ruc', 'direccion', 'ciudad', 'pais', 
            'telefono', 'email', 'sitio_web', 'contacto_nombre',
            'contacto_telefono', 'contacto_email', 'categoria',
            'notas', 'terminos_pago', 'limite_credito', 'estado'
        ]
        
        for campo in campos_actualizables:
            if campo in data:
                setattr(proveedor, campo, data[campo])
        
        proveedor.updated_at = datetime.utcnow()
        proveedor.updated_by = current_user_id

        # Registrar en el log de auditoría
        log = LogAuditoria(
            usuario_id=current_user_id,
            accion="actualizar",
            tabla="proveedores",
            registro_id=proveedor.id,
            datos_antiguos=datos_antiguos,
            datos_nuevos=proveedor.dict(),
            ip=request.remote_addr
        )
        logs_auditoria.append(log)

        return jsonify({'success': True, 'message': 'Proveedor actualizado exitosamente'})
    
    except ValueError as e:
        return jsonify({'error': f'Error de validación: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error al actualizar proveedor: {str(e)}'}), 500

@app.route('/proveedor/<int:id>', methods=['DELETE'])
@login_required
@role_required(['admin'])  # Solo administradores pueden eliminar
def eliminar_proveedor(id):
    try:
        current_user_id = SessionManager.get_current_user_id()
        proveedor = next((p for p in proveedores if p.id == id), None)
        
        if not proveedor:
            return jsonify({'error': 'Proveedor no encontrado'}), 404

        # Verificar si tiene órdenes de compra asociadas
        if tiene_ordenes_compra(id):
            return jsonify({
                'error': 'No se puede eliminar el proveedor porque tiene órdenes de compra asociadas'
            }), 400

        # Guardar datos para el log antes de eliminar
        datos_eliminados = proveedor.dict()
        
        # Eliminar el proveedor
        proveedores.remove(proveedor)

        # Registrar en el log de auditoría
        log = LogAuditoria(
            usuario_id=current_user_id,
            accion="eliminar",
            tabla="proveedores",
            registro_id=id,
            datos_antiguos=datos_eliminados,
            ip=request.remote_addr
        )
        logs_auditoria.append(log)

        return jsonify({'success': True, 'message': 'Proveedor eliminado exitosamente'})
    
    except Exception as e:
        return jsonify({'error': f'Error al eliminar proveedor: {str(e)}'}), 500

@app.route('/proveedor/<int:id>/productos', methods=['POST'])
@login_required
@role_required(['admin', 'inventario'])
def gestionar_productos_proveedor(id):
    try:
        current_user_id = SessionManager.get_current_user_id()
        data = request.get_json()
        producto_ids = data.get('producto_ids', [])

        proveedor = next((p for p in proveedores if p.id == id), None)
        if not proveedor:
            return jsonify({'error': 'Proveedor no encontrado'}), 404

        # Guardar datos antiguos para el log
        datos_antiguos = proveedor.dict()
        
        # Actualizar productos asociados
        proveedor.productos = producto_ids
        proveedor.updated_at = datetime.utcnow()
        proveedor.updated_by = current_user_id

        # Registrar en el log de auditoría
        log = LogAuditoria(
            usuario_id=current_user_id,
            accion="actualizar_productos",
            tabla="proveedores",
            registro_id=proveedor.id,
            datos_antiguos=datos_antiguos,
            datos_nuevos=proveedor.dict(),
            ip=request.remote_addr
        )
        logs_auditoria.append(log)

        return jsonify({'success': True, 'message': 'Productos actualizados exitosamente'})
    
    except Exception as e:
        return jsonify({'error': f'Error al actualizar productos: {str(e)}'}), 500

def tiene_ordenes_compra(proveedor_id: int) -> bool:
    """
    Verifica si un proveedor tiene órdenes de compra asociadas
    """
    # Aquí iría la lógica para verificar en la base de datos
    # Por ahora retornamos False
    return False

@app.route('/proveedores/buscar', methods=['GET'])
@login_required
@role_required(['admin', 'inventario'])
def buscar_proveedores():
    try:
        termino = request.args.get('q', '').lower()
        categoria = request.args.get('categoria')
        ciudad = request.args.get('ciudad')
        estado = request.args.get('estado')

        resultados = proveedores

        # Aplicar filtros
        if termino:
            resultados = [p for p in resultados if 
                         termino in p.nombre.lower() or
                         termino in p.codigo.lower() or
                         termino in p.ruc.lower()]
        
        if categoria:
            resultados = [p for p in resultados if p.categoria == categoria]
        
        if ciudad:
            resultados = [p for p in resultados if p.ciudad == ciudad]
        
        if estado:
            resultados = [p for p in resultados if p.estado == estado]

        return jsonify([{
            'id': p.id,
            'codigo': p.codigo,
            'nombre': p.nombre,
            'ruc': p.ruc,
            'ciudad': p.ciudad,
            'categoria': p.categoria,
            'estado': p.estado
        } for p in resultados])

    except Exception as e:
        return jsonify({'error': f'Error en la búsqueda: {str(e)}'}), 500

@app.route('/logs')
@login_required
@role_required(['admin'])
def ver_logs():
    return render_template('logs.html', logs=logs_auditoria, usuarios=usuarios)


def format_currency(value):
    return f"${value:,.2f}"

def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else ''

app.jinja_env.filters['currency'] = format_currency
app.jinja_env.filters['datetime'] = format_datetime

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
    
    # Agregar un proveedor de ejemplo
    proveedor_service.crear_proveedor(
        datos={
            'nombre': 'Proveedor Demo',
            'ruc': '1234567890001',
            'direccion': 'Dirección Demo',
            'ciudad': 'Ciudad Demo',
            'telefono': '123456789',
            'email': 'proveedor@demo.com',
            'contacto_nombre': 'Contacto Demo',
            'contacto_telefono': '987654321',
            'contacto_email': 'contacto@demo.com',
            'categoria': 'Materia Prima',
            'terminos_pago': '30 días'
        },
        usuario_id=1,
        username='ElBenerDev',
        ip='127.0.0.1'
    )
    
    app.run(debug=True)