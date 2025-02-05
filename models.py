from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(BaseModel):
    id: Optional[int] = None
    username: str
    email: EmailStr
    password_hash: str
    role: str  # admin, vendedor, inventario
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    @classmethod
    def create(cls, username: str, email: str, password: str, role: str = "vendedor"):
        return cls(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class Producto(BaseModel):
    id: Optional[int] = None
    codigo: str
    nombre: str
    categoria: str
    descripcion: Optional[str] = None
    precio_costo: float  # Nuevo campo para el costo
    precio_venta: float  # Renombramos precio a precio_venta
    stock: int
    stock_minimo: int = 0
    unidad_medida: str
    ubicacion: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    @property
    def valor_inventario(self) -> float:
        return self.precio_costo * self.stock

    @property
    def ganancia_potencial(self) -> float:
        return (self.precio_venta - self.precio_costo) * self.stock

class Cliente(BaseModel):
    id: Optional[int] = None
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo_cliente: str = "regular"  # regular, mayorista, distribuidor
    notas: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

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
    fecha_venta: datetime = datetime.now()
    estado: str = "completada"  # pendiente, completada, cancelada
    notas: Optional[str] = None
    
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

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "accion": self.accion,
            "tabla": self.tabla,
            "registro_id": self.registro_id,
            "datos_anteriores": self.datos_anteriores,
            "datos_nuevos": self.datos_nuevos,
            "fecha": self.fecha.isoformat(),
            "ip": self.ip
        }