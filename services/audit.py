from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class LogAuditoria(BaseModel):
    id: Optional[int] = None
    fecha: datetime = datetime.utcnow()
    usuario_id: int
    username: str
    accion: str  # crear, actualizar, eliminar, actualizar_productos
    tabla: str
    registro_id: int
    datos_antiguos: Optional[Dict[str, Any]] = None
    datos_nuevos: Optional[Dict[str, Any]] = None
    ip: str
    detalles: Optional[str] = None

class AuditoriaService:
    def __init__(self):
        self.logs = []
        self._counter = 1

    def registrar_accion(self, 
                        usuario_id: int,
                        username: str,
                        accion: str,
                        tabla: str,
                        registro_id: int,
                        datos_antiguos: Optional[Dict] = None,
                        datos_nuevos: Optional[Dict] = None,
                        ip: str = "",
                        detalles: str = "") -> LogAuditoria:
        """
        Registra una acción en el log de auditoría
        """
        try:
            log = LogAuditoria(
                id=self._counter,
                usuario_id=usuario_id,
                username=username,
                accion=accion,
                tabla=tabla,
                registro_id=registro_id,
                datos_antiguos=datos_antiguos,
                datos_nuevos=datos_nuevos,
                ip=ip,
                detalles=detalles
            )
            
            self.logs.append(log)
            self._counter += 1
            
            # Aquí se podría agregar la lógica para guardar en BD
            return log
        
        except Exception as e:
            print(f"Error al registrar auditoría: {str(e)}")
            raise

    def obtener_logs_por_tabla(self, tabla: str, limite: int = 100):
        """
        Obtiene los últimos logs de una tabla específica
        """
        return [log for log in reversed(self.logs) 
                if log.tabla == tabla][:limite]

    def obtener_logs_por_usuario(self, usuario_id: int, limite: int = 100):
        """
        Obtiene los últimos logs de un usuario específico
        """
        return [log for log in reversed(self.logs) 
                if log.usuario_id == usuario_id][:limite]