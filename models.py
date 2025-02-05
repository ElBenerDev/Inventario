from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr
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

class Cliente(BaseModel):
    id: Optional[int] = None
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo_cliente: str = "regular"
    notas: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    created_by: int
    updated_by: int

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