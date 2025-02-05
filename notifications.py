from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import Notificacion, Producto, Usuario, Venta
from typing import List
import logging

class NotificationSystem:
    def __init__(self, email_config=None):
        self.email_config = email_config or {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_user': 'tu_correo@gmail.com',
            'smtp_password': 'tu_contraseña_aplicacion'
        }
        self.notificaciones = []
        self.logger = logging.getLogger(__name__)

    def check_low_stock(self, productos: List[Producto], usuarios_admin: List[Usuario]) -> List[Notificacion]:
        """Verifica productos con stock bajo y genera notificaciones."""
        nuevas_notificaciones = []
        
        for producto in productos:
            if producto.stock <= producto.stock_minimo:
                notificacion = Notificacion(
                    tipo="stock_bajo",
                    titulo=f"Stock bajo - {producto.nombre}",
                    mensaje=f"El producto {producto.nombre} (Código: {producto.codigo}) "
                           f"tiene un stock de {producto.stock} unidades, "
                           f"por debajo del mínimo establecido ({producto.stock_minimo}).",
                    destinatarios=[u.id for u in usuarios_admin],
                    urgente=producto.stock == 0
                )
                nuevas_notificaciones.append(notificacion)
                self.notificaciones.append(notificacion)
                
                # Enviar email si el stock es 0
                if producto.stock == 0:
                    self.send_email_notification(
                        destinatarios=[u.email for u in usuarios_admin],
                        asunto=f"URGENTE: Stock agotado - {producto.nombre}",
                        mensaje=notificacion.mensaje
                    )
        
        return nuevas_notificaciones

    def generate_daily_summary(self, ventas: List[Venta], productos: List[Producto], usuarios_admin: List[Usuario]) -> Notificacion:
        """Genera un resumen diario de operaciones."""
        fecha_actual = datetime.now()
        ventas_hoy = [v for v in ventas if v.fecha_venta.date() == fecha_actual.date()]
        
        # Calcular estadísticas
        total_ventas = sum(v.total for v in ventas_hoy)
        productos_vendidos = sum(sum(item.cantidad for item in v.items) for v in ventas_hoy)
        productos_bajos_stock = sum(1 for p in productos if p.stock <= p.stock_minimo)
        
        mensaje = f"""
        Resumen del día {fecha_actual.strftime('%Y-%m-%d')}:
        
        Ventas:
        - Total de ventas: ${total_ventas:.2f}
        - Cantidad de ventas: {len(ventas_hoy)}
        - Productos vendidos: {productos_vendidos}
        
        Inventario:
        - Productos con stock bajo: {productos_bajos_stock}
        - Valor total del inventario: ${sum(p.precio_costo * p.stock for p in productos):.2f}
        """
        
        notificacion = Notificacion(
            tipo="resumen_diario",
            titulo=f"Resumen diario - {fecha_actual.strftime('%Y-%m-%d')}",
            mensaje=mensaje,
            destinatarios=[u.id for u in usuarios_admin],
            datos_adicionales={
                'total_ventas': total_ventas,
                'num_ventas': len(ventas_hoy),
                'productos_vendidos': productos_vendidos,
                'productos_bajos_stock': productos_bajos_stock
            }
        )
        
        self.notificaciones.append(notificacion)
        return notificacion

    def notify_price_changes(self, producto: Producto, precio_anterior: float, usuarios: List[Usuario]) -> Notificacion:
        """Notifica cambios en los precios de productos."""
        mensaje = (
            f"El precio del producto {producto.nombre} (Código: {producto.codigo}) "
            f"ha sido actualizado de ${precio_anterior:.2f} a ${producto.precio_venta:.2f}"
        )
        
        notificacion = Notificacion(
            tipo="cambio_precio",
            titulo=f"Cambio de precio - {producto.nombre}",
            mensaje=mensaje,
            destinatarios=[u.id for u in usuarios],
            datos_adicionales={
                'producto_id': producto.id,
                'precio_anterior': precio_anterior,
                'precio_nuevo': producto.precio_venta
            }
        )
        
        self.notificaciones.append(notificacion)
        return notificacion

    def send_email_notification(self, destinatarios: List[str], asunto: str, mensaje: str):
        """Envía notificaciones por correo electrónico."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['smtp_user']
            msg['To'] = ", ".join(destinatarios)
            msg['Subject'] = asunto
            
            msg.attach(MIMEText(mensaje, 'plain'))
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['smtp_user'], self.email_config['smtp_password'])
                server.send_message(msg)
                
            self.logger.info(f"Email enviado exitosamente a {len(destinatarios)} destinatarios")
            return True
        
        except Exception as e:
            self.logger.error(f"Error al enviar email: {str(e)}")
            return False

    def get_user_notifications(self, user_id: int, include_read: bool = False) -> List[Notificacion]:
        """Obtiene las notificaciones de un usuario."""
        return [
            n for n in self.notificaciones 
            if user_id in n.destinatarios and (include_read or not n.leida)
        ]

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Marca una notificación como leída."""
        for notificacion in self.notificaciones:
            if notificacion.id == notification_id and user_id in notificacion.destinatarios:
                notificacion.leida = True
                notificacion.fecha_lectura = datetime.now()
                return True
        return False