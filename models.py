from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class Producto(BaseModel):
    id: Optional[int] = None
    codigo: str
    nombre: str
    categoria: str
    descripcion: Optional[str] = None
    precio: float
    stock: int
    stock_minimo: int = 0
    unidad_medida: str
    ubicacion: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

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