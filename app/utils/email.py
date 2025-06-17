import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import os

from app.models.Booking import Booking
from app.models.User import User

# Configuración de email desde variables de entorno
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)


def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Envía un email usando SMTP.

    Args:
        to_email: Email del destinatario
        subject: Asunto del email
        body: Cuerpo del email en texto plano
        html_body: Cuerpo del email en HTML (opcional)

    Returns:
        bool: True si se envió correctamente, False si no
    """
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            print("SMTP credentials not configured")
            return False

        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email

        # Agregar texto plano
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)

        # Agregar HTML si se proporciona
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)

        # Enviar email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_confirmation_email(user_email: str, reservation_id: str) -> bool:
    """
    Envía email de confirmación de reserva.

    Args:
        user_email: Email del usuario
        reservation_id: ID de la reserva

    Returns:
        bool: True si se envió correctamente, False si no
    """
    try:
        # Obtener datos de la reserva
        booking = Booking.objects.get(id=reservation_id)

        # Formatear fechas
        check_in_str = booking.check_in.strftime("%d/%m/%Y %H:%M")
        check_out_str = booking.check_out.strftime("%d/%m/%Y %H:%M")

        # Calcular noches
        nights = (booking.check_out.date() - booking.check_in.date()).days

        subject = f"Confirmación de Reserva - {booking.room.hotel.name}"

        # Cuerpo en texto plano
        body = f"""
¡Hola {booking.user.name}!

Tu reserva ha sido creada exitosamente. Aquí están los detalles:

DETALLES DE LA RESERVA:
- ID de Reserva: {reservation_id}
- Hotel: {booking.room.hotel.name}
- Habitación: {booking.room.name}
- Check-in: {check_in_str}
- Check-out: {check_out_str}
- Noches: {nights}
- Total: €{booking.total:.2f}

SERVICIOS EXTRAS:
"""

        if booking.extra_services:
            for service in booking.extra_services:
                body += f"- {service.name}: €{service.price:.2f}\n"
        else:
            body += "- Ninguno\n"

        body += f"""
INSTRUCCIONES:
- Presenta este email o el ID de reserva al hacer check-in
- El check-in es a partir de las 15:00
- El check-out es hasta las 12:00
- Para cualquier consulta, contacta con nosotros

¡Esperamos verte pronto!

Equipo de Reservas
        """

        # Cuerpo en HTML
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; border: 1px solid #ddd; }}
        .details {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; }}
        .highlight {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Confirmación de Reserva</h1>
    </div>

    <div class="content">
        <h2>¡Hola {booking.user.name}!</h2>
        <p>Tu reserva ha sido creada exitosamente. Aquí están los detalles:</p>

        <div class="details">
            <h3>DETALLES DE LA RESERVA:</h3>
            <ul>
                <li><strong>ID de Reserva:</strong> <span class="highlight">{reservation_id}</span></li>
                <li><strong>Hotel:</strong> {booking.room.hotel.name}</li>
                <li><strong>Habitación:</strong> {booking.room.name}</li>
                <li><strong>Check-in:</strong> {check_in_str}</li>
                <li><strong>Check-out:</strong> {check_out_str}</li>
                <li><strong>Noches:</strong> {nights}</li>
                <li><strong>Total:</strong> <span class="highlight">€{booking.total:.2f}</span></li>
            </ul>
        </div>

        <div class="details">
            <h3>SERVICIOS EXTRAS:</h3>
            <ul>
"""

        if booking.extra_services:
            for service in booking.extra_services:
                html_body += f"<li>{service.name}: €{service.price:.2f}</li>"
        else:
            html_body += "<li>Ninguno</li>"

        html_body += f"""
            </ul>
        </div>

        <div class="details">
            <h3>INSTRUCCIONES:</h3>
            <ul>
                <li>Presenta este email o el ID de reserva al hacer check-in</li>
                <li>El check-in es a partir de las 15:00</li>
                <li>El check-out es hasta las 12:00</li>
                <li>Para cualquier consulta, contacta con nosotros</li>
            </ul>
        </div>

        <p>¡Esperamos verte pronto!</p>
    </div>

    <div class="footer">
        <p>Equipo de Reservas</p>
    </div>
</body>
</html>
        """

        return send_email(user_email, subject, body, html_body)

    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False


def send_cancellation_email(user_email: str, reservation_id: str, cancellation_fee: float = 0.0) -> bool:
    """
    Envía email de confirmación de cancelación.

    Args:
        user_email: Email del usuario
        reservation_id: ID de la reserva
        cancellation_fee: Tarifa de cancelación aplicada

    Returns:
        bool: True si se envió correctamente, False si no
    """
    try:
        booking = Booking.objects.get(id=reservation_id)

        subject = f"Cancelación de Reserva - {booking.room.hotel.name}"

        body = f"""
Hola {booking.user.name},

Tu reserva ha sido cancelada exitosamente.

DETALLES DE LA RESERVA CANCELADA:
- ID de Reserva: {reservation_id}
- Hotel: {booking.room.hotel.name}
- Habitación: {booking.room.name}
- Fechas: {booking.check_in.strftime("%d/%m/%Y")} - {booking.check_out.strftime("%d/%m/%Y")}
- Total Original: €{booking.total:.2f}
"""

        if cancellation_fee > 0:
            refund_amount = booking.total - cancellation_fee
            body += f"""
- Tarifa de Cancelación: €{cancellation_fee:.2f}
- Monto a Reembolsar: €{refund_amount:.2f}

El reembolso será procesado en los próximos 5-7 días hábiles.
"""
        else:
            body += f"""
- Monto a Reembolsar: €{booking.total:.2f}

El reembolso será procesado en los próximos 3-5 días hábiles.
"""

        body += """
Si tienes alguna pregunta sobre el reembolso, no dudes en contactarnos.

Gracias por tu comprensión.

Equipo de Reservas
        """

        return send_email(user_email, subject, body)

    except Exception as e:
        print(f"Error sending cancellation email: {e}")
        return False


def send_reminder_email(user_email: str, reservation_id: str) -> bool:
    """
    Envía email recordatorio antes del check-in.

    Args:
        user_email: Email del usuario
        reservation_id: ID de la reserva

    Returns:
        bool: True si se envió correctamente, False si no
    """
    try:
        booking = Booking.objects.get(id=reservation_id)

        # Calcular días hasta el check-in
        days_until = (booking.check_in.date() - datetime.now().date()).days

        subject = f"Recordatorio: Tu reserva en {booking.room.hotel.name} - {days_until} días restantes"

        body = f"""
¡Hola {booking.user.name}!

Te recordamos que tu reserva está próxima:

DETALLES DE TU RESERVA:
- ID de Reserva: {reservation_id}
- Hotel: {booking.room.hotel.name}
- Habitación: {booking.room.name}
- Check-in: {booking.check_in.strftime("%d/%m/%Y a las %H:%M")}
- Check-out: {booking.check_out.strftime("%d/%m/%Y a las %H:%M")}

RECORDATORIOS IMPORTANTES:
- Check-in: a partir de las 15:00
- Check-out: hasta las 12:00
- Trae una identificación válida
- Presenta este email o el ID de reserva

DIRECCIÓN DEL HOTEL:
{booking.room.hotel.address if hasattr(booking.room.hotel, 'address') else 'Contacta el hotel para más información'}

¿Necesitas hacer algún cambio? Contáctanos lo antes posible.

¡Esperamos verte pronto!

Equipo de Reservas
        """

        return send_email(user_email, subject, body)

    except Exception as e:
        print(f"Error sending reminder email: {e}")
        return False


def send_status_update_email(user_email: str, reservation_id: str, new_status: str) -> bool:
    """
    Envía email cuando cambia el estado de una reserva.

    Args:
        user_email: Email del usuario
        reservation_id: ID de la reserva
        new_status: Nuevo estado de la reserva

    Returns:
        bool: True si se envió correctamente, False si no
    """
    try:
        booking = Booking.objects.get(id=reservation_id)

        status_messages = {
            'confirmed': 'confirmada',
            'cancelled': 'cancelada',
            'completed': 'completada'
        }

        status_text = status_messages.get(new_status, new_status)

        subject = f"Actualización de Reserva - {booking.room.hotel.name}"

        body = f"""
Hola {booking.user.name},

El estado de tu reserva ha sido actualizado.

INFORMACIÓN DE LA RESERVA:
- ID de Reserva: {reservation_id}
- Hotel: {booking.room.hotel.name}
- Nuevo Estado: {status_text.upper()}
- Fecha de Actualización: {datetime.now().strftime("%d/%m/%Y %H:%M")}

"""

        if new_status == 'confirmed':
            body += """
¡Excelente! Tu reserva ha sido confirmada. 

Recuerda:
- Check-in: a partir de las 15:00
- Check-out: hasta las 12:00
- Trae una identificación válida
"""
        elif new_status == 'completed':
            body += """
Esperamos que hayas disfrutado tu estancia.

Si tienes un momento, nos encantaría conocer tu opinión sobre tu experiencia.
"""

        body += """
Si tienes alguna pregunta, no dudes en contactarnos.

Saludos,
Equipo de Reservas
        """

        return send_email(user_email, subject, body)

    except Exception as e:
        print(f"Error sending status update email: {e}")
        return False