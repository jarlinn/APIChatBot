"""
Email service with support for Console, Mailtrap, and SMTP providers
"""

import os
from typing import Optional, Dict, Any
import logging
from enum import Enum

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

from src.app.config import settings

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """Supported email providers"""
    CONSOLE = "console"
    MAILTRAP = "mailtrap"


class EmailService:
    """
    Unified email service supporting multiple providers:
    - Console: Print emails to terminal (development)
    - Mailtrap: Email testing service (development/production)
    """

    def __init__(self):

        self.provider = EmailProvider(settings.email_provider)

        # Common configuration
        self.from_name = settings.email_from_name
        self.frontend_url = settings.frontend_url
        
        # Provider-specific configuration
        self._smtp_config = self._get_smtp_config()
        
        # Template configuration
        template_dir = os.path.join(os.path.dirname(__file__), "../templates/email")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        logger.info("📧 Email service initialized with provider: %s", self.provider.value)

    def _get_smtp_config(self) -> Dict[str, Any]:
        """Get SMTP configuration based on provider"""
        if self.provider == EmailProvider.CONSOLE:
            return {}
        
        # if self.api_token is not None:
        return {
            "host": settings.mailtrap_host,
            "port": settings.mailtrap_port,
            "username": settings.mailtrap_username,
            "password": settings.mailtrap_password,
            "from_email": settings.mailtrap_from_email,
            "use_tls": True
        }
        # return {}

    def _print_console_email(
        self, to_email: str, subject: str, html_content: str, 
        text_content: Optional[str] = None
    ):
        """Print email to console for development"""
        print("\n" + "="*80)
        print("📧 EMAIL SENT (CONSOLE MODE)")
        print("="*80)
        print(f"📤 From: {self.from_name}")
        print(f"📥 To: {to_email}")
        print(f"📋 Subject: {subject}")
        print("-"*80)
        print("📄 HTML CONTENT:")
        print(
            html_content[:500] + "..." if len(html_content) > 500 
            else html_content
        )
        if text_content:
            print("-"*80)
            print("📝 TEXT CONTENT:")
            print(
                text_content[:300] + "..." if len(text_content) > 300 
                else text_content
            )
        print("="*80)
        logger.info("📧 Email displayed in console for %s", to_email)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email using configured provider
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Handle console mode
            if self.provider == EmailProvider.CONSOLE:
                self._print_console_email(to_email, subject, html_content, text_content)
                return True
            
            # Get SMTP configuration based on provider
            smtp_config = await self._get_smtp_config_for_provider()
            if not smtp_config:
                logger.error(
                "Failed to get SMTP configuration for provider: %s", 
                self.provider.value
            )
                return False
            
            # Create email message
            message = self._create_email_message(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=smtp_config["from_email"]
            )
            
            # Send email via SMTP
            await self._send_smtp_email(message, smtp_config)
            
            logger.info(
                "✅ Email sent successfully to %s via %s", 
                to_email, self.provider.value
            )
            
            return True

        except Exception as e:
            logger.error("❌ Error sending email to %s: %s", to_email, str(e))
            return False

    async def _get_smtp_config_for_provider(self) -> Optional[Dict[str, Any]]:
        """Get SMTP configuration for the current provider"""
        if self.provider == EmailProvider.MAILTRAP:
            config = self._smtp_config.copy()
            if not all([config.get("host"), config.get("username"), config.get("password")]):
                logger.error(
                    "Missing required Mailtrap configuration for %s", 
                    self.provider.value
                )
                return None
            return config
        
        return None

    def _create_email_message(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str], 
        from_email: str
    ) -> MIMEMultipart:
        """Create email message with HTML and optional text content"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{from_email}>"
        message["To"] = to_email

        # Add plain text content if provided
        if text_content:
            text_part = MIMEText(text_content, "plain", "utf-8")
            message.attach(text_part)

        # Add HTML content
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        return message

    async def _send_smtp_email(self, message: MIMEMultipart, smtp_config: Dict[str, Any]):
        """Send email via SMTP"""
        logger.info("📤 Connecting to SMTP server:")
        logger.info("  🌐 Host: %s", smtp_config["host"])
        logger.info("  🔌 Port: %s", smtp_config["port"])
        logger.info("  👤 Username: %s", smtp_config["username"])
        logger.info("  🔐 Password: %s", "***" + smtp_config["password"][-4:] if smtp_config["password"] else "None")
        
        await aiosmtplib.send(
            message,
            hostname=smtp_config["host"],
            port=smtp_config["port"],
            start_tls=smtp_config.get("use_tls", True),
            username=smtp_config["username"],
            password=smtp_config["password"],
            timeout=30,
        )
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            user_name: User's name (optional, will use email prefix if not provided)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Load email template
            template = self.jinja_env.get_template("password_reset.html")
            
            # Generate reset URL
            reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"
            
            # Prepare template variables
            template_vars = {
                "user_name": user_name or to_email.split("@")[0],
                "reset_url": reset_url,
                "reset_token": reset_token,
                "app_name": "ChatBot UFPS",
                "frontend_url": self.frontend_url,
                "support_email": "support@chatbot.ufps.edu.co"
            }
            
            # Render HTML template
            html_content = template.render(**template_vars)
            
            # Create plain text fallback
            text_content = self._create_password_reset_text(
                user_name=template_vars["user_name"],
                reset_url=reset_url,
                reset_token=reset_token
            )
            
            # Send email
            success = await self.send_email(
                to_email=to_email,
                subject="🔐 Restablecer contraseña - ChatBot UFPS",
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info("✅ Password reset email sent to %s", to_email)
            else:
                logger.error("❌ Failed to send password reset email to %s", to_email)
                
            return success
            
        except Exception as e:
            logger.error("❌ Error sending password reset email to %s: %s", to_email, str(e))
            return False

    def _create_password_reset_text(self, user_name: str, reset_url: str, reset_token: str) -> str:
        """Create plain text version of password reset email"""
        return f"""
Hola {user_name},

Has solicitado restablecer tu contraseña en ChatBot UFPS.

Para restablecer tu contraseña, haz clic en el siguiente enlace:
{reset_url}

⏰ Este enlace expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo de forma segura.

Saludos,
Equipo ChatBot UFPS

---
📧 ¿Necesitas ayuda? Contacta a: support@chatbot.ufps.edu.co
🌐 Sitio web: {self.frontend_url}
        """.strip()

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
        temporary_password: Optional[str] = None
    ) -> bool:
        """
        Send welcome email to new users
        
        Args:
            to_email: Recipient email address
            user_name: User's name
            temporary_password: Temporary password if applicable
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create welcome email content
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">¡Bienvenido a ChatBot UFPS! 🎉</h2>
                
                <p>Hola <strong>{user_name}</strong>,</p>
                
                <p>Tu cuenta ha sido creada exitosamente en ChatBot UFPS. Ya puedes comenzar a hacer preguntas y obtener respuestas inteligentes.</p>
                
                {'<p><strong>Contraseña temporal:</strong> <code>' + temporary_password + '</code></p>' if temporary_password else ''}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.frontend_url}" style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">
                        Acceder a ChatBot UFPS
                    </a>
                </div>
                
                <p>¡Esperamos que disfrutes usando nuestra plataforma!</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #7f8c8d; font-size: 12px;">
                    Este es un correo automático, por favor no responder.<br>
                    Si tienes preguntas, contacta a: support@chatbot.ufps.edu.co
                </p>
            </div>
            """
            
            text_content = f"""
¡Bienvenido a ChatBot UFPS! 🎉

Hola {user_name},

Tu cuenta ha sido creada exitosamente en ChatBot UFPS. Ya puedes comenzar a hacer preguntas y obtener respuestas inteligentes.

{'Contraseña temporal: ' + temporary_password if temporary_password else ''}

Accede a la plataforma en: {self.frontend_url}

¡Esperamos que disfrutes usando nuestra plataforma!

---
📧 ¿Necesitas ayuda? Contacta a: support@chatbot.ufps.edu.co
🌐 Sitio web: {self.frontend_url}
            """.strip()
            
            return await self.send_email(
                to_email=to_email,
                subject="🎉 ¡Bienvenido a ChatBot UFPS!",
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error("❌ Error sending welcome email to %s: %s", to_email, str(e))
            return False

    async def send_email_change_verification(
        self,
        to_email: str,
        verification_code: str,
        new_email: str
    ) -> bool:
        """
        Send email change verification code

        Args:
            to_email: Current email address (recipient)
            verification_code: Verification code for email change
            new_email: New email address the user wants to change to

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create email content
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">🔐 Código de Verificación - Cambio de Email</h2>

                <p>Hola,</p>

                <p>Has solicitado cambiar tu dirección de correo electrónico en ChatBot UFPS.</p>

                <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 20px; margin: 20px 0; text-align: center;">
                    <h3 style="color: #495057; margin: 0 0 10px 0;">Tu código de verificación:</h3>
                    <div style="font-size: 24px; font-weight: bold; color: #007bff; letter-spacing: 3px;">{verification_code}</div>
                </div>

                <p><strong>Nuevo email solicitado:</strong> {new_email}</p>

                <p>Ingresa este código en la aplicación para confirmar el cambio de tu dirección de correo electrónico.</p>

                <p style="color: #dc3545;"><strong>⚠️ Importante:</strong> Este código expirará en 24 horas.</p>

                <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #7f8c8d; font-size: 12px;">
                    Este es un correo automático, por favor no responder.<br>
                    Si tienes preguntas, contacta a: support@chatbot.ufps.edu.co
                </p>
            </div>
            """

            text_content = f"""
🔐 Código de Verificación - Cambio de Email

Hola,

Has solicitado cambiar tu dirección de correo electrónico en ChatBot UFPS.

Tu código de verificación: {verification_code}

Nuevo email solicitado: {new_email}

Ingresa este código en la aplicación para confirmar el cambio de tu dirección de correo electrónico.

⚠️ Importante: Este código expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo de forma segura.

---
📧 ¿Necesitas ayuda? Contacta a: support@chatbot.ufps.edu.co
🌐 Sitio web: {self.frontend_url}
            """.strip()

            return await self.send_email(
                to_email=to_email,
                subject="🔐 Código de Verificación - Cambio de Email - ChatBot UFPS",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error("❌ Error sending email change verification to %s: %s", to_email, str(e))
            return False

    async def send_email_change_confirmation(
        self,
        to_email: str,
        confirm_token: str,
        old_email: str
    ) -> bool:
        """
        Send email change confirmation to new email address

        Args:
            to_email: New email address (recipient)
            confirm_token: Confirmation token for completing email change
            old_email: Current email address for context

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create confirmation URL
            confirm_url = f"{self.frontend_url}/auth/email-change-complete?token={confirm_token}"

            # Create email content
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">✅ Confirma tu nuevo email</h2>

                <p>Hola,</p>

                <p>Has solicitado cambiar tu dirección de correo electrónico en ChatBot UFPS.</p>

                <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 20px; margin: 20px 0;">
                    <p><strong>Email anterior:</strong> {old_email}</p>
                    <p><strong>Nuevo email:</strong> {to_email}</p>
                </div>

                <p>Para completar el cambio de email, haz click en el botón de abajo:</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{confirm_url}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        ✅ Confirmar cambio de email
                    </a>
                </div>

                <p style="color: #dc3545;"><strong>⚠️ Importante:</strong> Este enlace expirará en 24 horas.</p>

                <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #7f8c8d; font-size: 12px;">
                    Este es un correo automático, por favor no responder.<br>
                    Si tienes preguntas, contacta a: support@chatbot.ufps.edu.co
                </p>
            </div>
            """

            text_content = f"""
✅ Confirma tu nuevo email

Hola,

Has solicitado cambiar tu dirección de correo electrónico en ChatBot UFPS.

Email anterior: {old_email}
Nuevo email: {to_email}

Para completar el cambio, visita este enlace:
{confirm_url}

⚠️ Importante: Este enlace expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo de forma segura.

---
📧 ¿Necesitas ayuda? Contacta a: support@chatbot.ufps.edu.co
🌐 Sitio web: {self.frontend_url}
            """.strip()

            return await self.send_email(
                to_email=to_email,
                subject="✅ Confirma tu nuevo email - ChatBot UFPS",
                html_content=html_content,
                text_content=text_content
            )

        except Exception as e:
            logger.error("❌ Error sending email change confirmation to %s: %s", to_email, str(e))
            return False


# Global email service instance
email_service = EmailService()
