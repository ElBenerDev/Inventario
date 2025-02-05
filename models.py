from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr, validator
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    password_hash: str
    nombre_completo: str
    role: str  # admin, vendedor, inventario
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    created_by: Optional[int] = None

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Producto(BaseModel):
    id: Optional[int] = None
    codigo: str
    nombre: str
    categoria: str
    descripcion: Optional[str] = None
    precio_costo: float
    precio_venta: float
    stock: int
    stock_minimo: int = 0
    unidad_medida: str
    ubicacion: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    created_by: int
    updated_by: int

class Cliente:
    def __init__(self, id, nombre, email, telefono, direccion, tipo_cliente, notas, created_by, updated_by):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.telefono = telefono
        self.direccion = direccion
        self.tipo_cliente = tipo_cliente
        self.notas = notas
        self.created_by = created_by
        self.updated_by = updated_by

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'tipo_cliente': self.tipo_cliente,
            'notas': self.notas,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }

    def dict(self):  # Método alternativo para compatibilidad
        return self.to_dict()
    
class ItemVenta(BaseModel):
    producto_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float

class Venta(BaseModel):
    id: Optional[int] = None
    cliente_id: int
    items: List[ItemVenta]
    total: float
    estado: str = "completada"
    notas: Optional[str] = None
    fecha_venta: datetime = datetime.now()
    created_by: int
    updated_by: int

class LogAuditoria(BaseModel):
    id: Optional[int] = None
    usuario_id: int
    accion: str
    tabla: str
    registro_id: int
    datos_anteriores: Optional[dict] = None
    datos_nuevos: Optional[dict] = None
    fecha: datetime = datetime.now()
    ip: str
    
class Notificacion(BaseModel):
    id: Optional[int] = None
    tipo: str  # stock_bajo, vencimiento_producto, resumen_diario, cambio_precio, etc.
    titulo: str
    mensaje: str
    destinatarios: List[int]  # Lista de IDs de usuarios
    leida: bool = False
    fecha_creacion: datetime = datetime.now()
    fecha_lectura: Optional[datetime] = None
    urgente: bool = False
    datos_adicionales: Optional[dict] = None
    
class Proveedor(BaseModel):
    id: Optional[int] = None
    codigo: str
    nombre: str
    ruc: str
    direccion: str
    ciudad: str
    pais: str = "Ecuador"  # Valor por defecto
    telefono: str
    email: str
    sitio_web: Optional[str] = None
    contacto_nombre: str
    contacto_telefono: str
    contacto_email: str
    categoria: str  # ej: "Materia Prima", "Suministros", "Servicios"
    productos: List[int] = []  # Lista de IDs de productos
    notas: Optional[str] = None
    estado: str = "activo"  # activo, inactivo
    terminos_pago: str  # ej: "30 días", "60 días", "Contado"
    moneda: str = "USD"
    limite_credito: float = 0.0
    total_compras: float = 0.0
    ultima_compra: Optional[datetime] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    created_by: int
    updated_by: int

    @validator('ruc')
    def validar_ruc(cls, v):
        # Validación básica de RUC ecuatoriano
        if not v.isdigit() or len(v) != 13:
            raise ValueError('RUC debe tener 13 dígitos numéricos')
        return v

    @validator('email', 'contacto_email')
    def validar_email(cls, v):
        # Validación básica de email
        if '@' not in v or '.' not in v:
            raise ValueError('Email inválido')
        return v

    @validator('telefono', 'contacto_telefono')
    def validar_telefono(cls, v):
        # Limpia el número de teléfono y valida formato básico
        v = ''.join(filter(str.isdigit, v))
        if len(v) < 9 or len(v) > 10:
            raise ValueError('Número de teléfono debe tener entre 9 y 10 dígitos')
        return v

    @validator('limite_credito')
    def validar_limite_credito(cls, v):
        if v < 0:
            raise ValueError('El límite de crédito no puede ser negativo')
        return v

    class Config:
        validate_assignment = True