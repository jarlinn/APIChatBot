# src/app/services/email_service.py
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from typing import Optional
import logging
import aiohttp
import json

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        # Detectar modo de desarrollo
        self.is_development = os.getenv("ENVIRONMENT", "development") == "development"
        
        # Determinar método de envío
        self.email_method = os.getenv("EMAIL_METHOD", "mailtrap")  # console, ethereal, mailtrap, smtp
        
        if self.email_method == "console":
            # Modo consola - Solo muestra el email en la terminal
            self.smtp_server = None
            self.smtp_port = None
            self.smtp_username = None
            self.smtp_password = None
        elif self.email_method == "mailtrap":
            # Configuración Mailtrap (gratis para desarrollo)
            self.smtp_server = "sandbox.smtp.mailtrap.io"
            self.smtp_port = 2525
            self.smtp_username = os.getenv("MAILTRAP_USERNAME", "889ab3c7261b56")
            self.smtp_password = os.getenv("MAILTRAP_PASSWORD", "a10abf4de5159c")
            
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "ChatBot UFPS")

        # Configurar Jinja2 para plantillas
        template_dir = os.path.join(os.path.dirname(__file__), "../templates/email")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Cache para credenciales Ethereal
        self._ethereal_credentials = None
    
    async def _get_ethereal_credentials(self):
        """Obtiene credenciales de Ethereal Email automáticamente"""
        if self._ethereal_credentials:
            return self._ethereal_credentials
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.nodemailer.com/user') as response:
                    if response.status == 200:
                        data = await response.json()
                        self._ethereal_credentials = {
                            'host': data['smtp']['host'],
                            'port': data['smtp']['port'],
                            'secure': data['smtp']['secure'],
                            'user': data['user'],
                            'pass': data['pass'],
                            'web_url': f"https://ethereal.email/message/{data['user']}"
                        }
                        logger.info("✅ Credenciales Ethereal obtenidas automáticamente")
                        logger.info("📧 Ver emails en: %s", self._ethereal_credentials['web_url'])
                        return self._ethereal_credentials
        except Exception as e:
            logger.error("Error obteniendo credenciales Ethereal: %s", str(e))
            return None
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Envía un email usando SMTP asíncrono"""
        try:
            # Configurar credenciales según el método
            if self.email_method == "console":
                # Modo consola - Solo mostrar en terminal
                print("\n" + "="*60)
                print("📧 EMAIL ENVIADO (MODO CONSOLA)")
                print("="*60)
                print(f"Para: {to_email}")
                print(f"Asunto: {subject}")
                print(f"De: {self.from_name}")
                print("-"*60)
                print("CONTENIDO HTML:")
                print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
                if text_content:
                    print("-"*60)
                    print("CONTENIDO TEXTO:")
                    print(text_content[:300] + "..." if len(text_content) > 300 else text_content)
                print("="*60)
                logger.info("Email mostrado en consola para %s", to_email)
                return True
            elif self.email_method == "ethereal":
                credentials = await self._get_ethereal_credentials()
                if not credentials:
                    logger.error("No se pudieron obtener credenciales Ethereal")
                    return False
                
                smtp_server = credentials['host']
                smtp_port = credentials['port']
                smtp_username = credentials['user']
                smtp_password = credentials['pass']
                from_email = credentials['user']
            else:
                smtp_server = self.smtp_server
                smtp_port = self.smtp_port
                smtp_username = self.smtp_username
                smtp_password = self.smtp_password
                from_email = self.from_email
            
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{from_email}>"
            message["To"] = to_email

            # Agregar contenido de texto plano si se proporciona
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)

            # Agregar contenido HTML
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # Debug info
            logger.info("Intentando conectar a SMTP:")
            logger.info("  Host: %s", smtp_server)
            logger.info("  Port: %s", smtp_port)
            logger.info("  Username: %s", smtp_username)
            logger.info("  Password: %s", "***" + smtp_password[-4:] if smtp_password else "None")
            
            # Enviar email
            await aiosmtplib.send(
                message,
                hostname=smtp_server,
                port=smtp_port,
                start_tls=True,
                username=smtp_username,
                password=smtp_password,
                timeout=30,  # Agregar timeout
            )

            logger.info("Email enviado exitosamente a %s", to_email)
            
            # Si es Ethereal, mostrar URL para ver el email
            if self.email_method == "ethereal" and self._ethereal_credentials:
                logger.info("📧 Ver email en: %s", self._ethereal_credentials['web_url'])
            
            return True

        except Exception as e:
            logger.error("Error enviando email a %s: %s", to_email, str(e))
            return False
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Envía email de recuperación de contraseña"""
        try:
            # Cargar plantilla
            template = self.jinja_env.get_template("password_reset.html")
            
            # URL de reset (deberías configurar esto según tu frontend)
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            reset_url = f"{frontend_url}/reset-password?token={reset_token}"
            
            # Renderizar plantilla
            html_content = template.render(
                user_name=user_name or to_email.split("@")[0],
                reset_url=reset_url,
                reset_token=reset_token,
                app_name="ChatBot UFPS"
            )
            
            # Contenido de texto plano como fallback
            text_content = f"""
Hola {user_name or to_email.split("@")[0]},

Has solicitado restablecer tu contraseña en ChatBot UFPS.

Para restablecer tu contraseña, haz clic en el siguiente enlace:
{reset_url}

O copia y pega este token en la aplicación:
{reset_token}

Este enlace expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo.

Saludos,
Equipo ChatBot UFPS
            """
            
            return await self.send_email(
                to_email=to_email,
                subject="Restablecer contraseña - ChatBot UFPS",
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(
                "Error enviando email de reset a %s: %s", to_email, str(e)
            )
            return False


# Instancia global del servicio
email_service = EmailService()
