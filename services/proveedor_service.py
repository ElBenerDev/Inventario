from typing import List, Optional, Dict
from datetime import datetime
from models import Proveedor
from services.audit import AuditoriaService

class ProveedorService:
    def __init__(self, auditoria_service: AuditoriaService):
        self.proveedores: List[Proveedor] = []
        self.auditoria = auditoria_service
        self._counter = 1

    def generar_codigo(self) -> str:
        """
        Genera un código único para el proveedor
        """
        return f"PRV{str(len(self.proveedores) + 1).zfill(3)}"

    def crear_proveedor(self, 
                       datos: Dict, 
                       usuario_id: int,
                       username: str,
                       ip: str) -> Proveedor:
        """
        Crea un nuevo proveedor
        """
        try:
            # Generar código único
            datos['codigo'] = self.generar_codigo()
            datos['id'] = self._counter
            
            # Crear instancia
            nuevo_proveedor = Proveedor(
                **datos,
                created_by=usuario_id,
                updated_by=usuario_id
            )
            
            # Agregar a la lista
            self.proveedores.append(nuevo_proveedor)
            self._counter += 1
            
            # Registrar auditoría
            self.auditoria.registrar_accion(
                usuario_id=usuario_id,
                username=username,
                accion="crear",
                tabla="proveedores",
                registro_id=nuevo_proveedor.id,
                datos_nuevos=nuevo_proveedor.dict(),
                ip=ip
            )
            
            return nuevo_proveedor
        
        except Exception as e:
            print(f"Error al crear proveedor: {str(e)}")
            raise

    def actualizar_proveedor(self,
                           id: int,
                           datos: Dict,
                           usuario_id: int,
                           username: str,
                           ip: str) -> Proveedor:
        """
        Actualiza un proveedor existente
        """
        proveedor = self.obtener_por_id(id)
        if not proveedor:
            raise ValueError(f"Proveedor con ID {id} no encontrado")

        datos_antiguos = proveedor.dict()
        
        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(proveedor, campo):
                setattr(proveedor, campo, valor)
        
        proveedor.updated_by = usuario_id
        proveedor.updated_at = datetime.utcnow()
        
        # Registrar auditoría
        self.auditoria.registrar_accion(
            usuario_id=usuario_id,
            username=username,
            accion="actualizar",
            tabla="proveedores",
            registro_id=proveedor.id,
            datos_antiguos=datos_antiguos,
            datos_nuevos=proveedor.dict(),
            ip=ip
        )
        
        return proveedor

    def obtener_por_id(self, id: int) -> Optional[Proveedor]:
        """
        Obtiene un proveedor por su ID
        """
        return next((p for p in self.proveedores if p.id == id), None)

    def buscar_proveedores(self,
                          termino: str = "",
                          categoria: str = None,
                          ciudad: str = None,
                          estado: str = None) -> List[Proveedor]:
        """
        Busca proveedores según los filtros especificados
        """
        resultados = self.proveedores

        if termino:
            termino = termino.lower()
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

        return resultados

    def eliminar_proveedor(self,
                          id: int,
                          usuario_id: int,
                          username: str,
                          ip: str) -> bool:
        """
        Elimina un proveedor
        """
        proveedor = self.obtener_por_id(id)
        if not proveedor:
            raise ValueError(f"Proveedor con ID {id} no encontrado")

        datos_eliminados = proveedor.dict()
        self.proveedores.remove(proveedor)
        
        # Registrar auditoría
        self.auditoria.registrar_accion(
            usuario_id=usuario_id,
            username=username,
            accion="eliminar",
            tabla="proveedores",
            registro_id=id,
            datos_antiguos=datos_eliminados,
            ip=ip,
            detalles="Proveedor eliminado completamente del sistema"
        )
        
        return True