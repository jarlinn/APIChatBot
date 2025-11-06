"""
Email service with support for Console and sendgrid (HTTPS API) providers
"""

import os
from typing import Optional, Dict, Any
import logging
from enum import Enum

import aiohttp
from jinja2 import Environment, FileSystemLoader

from src.app.config import settings

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """Supported email providers"""
    CONSOLE = "console"
    SENDGRID = "sendgrid"


class EmailService:
    """
    Unified email service supporting multiple providers:
    - Console: Print emails to terminal (development)
    - SendGrid: Email delivery service via HTTPS API (production)
    """

    def __init__(self):

        self.provider = EmailProvider(settings.email_provider)

        # Common configuration
        self.from_name = settings.email_from_name
        self.frontend_url = settings.frontend_url
        
        # Template configuration
        template_dir = os.path.join(os.path.dirname(__file__), "../templates/email")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        logger.info("📧 Email service initialized with provider: %s", self.provider.value)

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
            # Handle SendGrid provider (HTTPS API)
            success = await self._send_sendgrid_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            if success:
                logger.info("Email sent successfully to %s via %s", to_email, self.provider.value)
            return success

        except Exception as e:
            logger.error("Error sending email to %s: %s", to_email, str(e))
            return False

    def _get_provider_config(self, provider: EmailProvider) -> Optional[Dict[str, Any]]:
        """Get configuration for the specified provider"""
        if provider == EmailProvider.SENDGRID:
            if not settings.sendgrid_api_key:
                logger.error("Missing SendGrid API key (SENDGRID_API_KEY)")
                return None
            return {"api_key": settings.sendgrid_api_key, "from_email": settings.mailtrap_from_email}  # Use same from_email
        return None

    async def _send_sendgrid_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str]
    ) -> bool:
        """Send email via SendGrid HTTPS API"""
        config = self._get_provider_config(EmailProvider.SENDGRID)
        if not config:
            return False

        # Build content array
        content = [{"type": "text/html", "value": html_content}]
        if text_content:
            content.insert(0, {"type": "text/plain", "value": text_content})

        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {"email": config["from_email"], "name": self.from_name},
            "content": content
        }

        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 202:
                        logger.info("📧 Email sent via SendGrid to %s", to_email)
                        return True
                    else:
                        response_text = await response.text()
                        logger.error("SendGrid API error: %s - %s", response.status, response_text)
                        return False
        except Exception as e:
            logger.error("Error sending email via SendGrid: %s", str(e))
            return False

    async def send_email_change_success_notification(
        self,
        to_email: str,
        temporary_password: str,
        old_email: str
    ) -> bool:
        """
        Send notification after successful email change with temporary password

        Args:
            to_email: New email address (recipient)
            temporary_password: Temporary password that was set
            old_email: Previous email address for context

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Load email template
            template = self.jinja_env.get_template("email_change_success.html")

            # Prepare template variables
            template_vars = {
                "temporary_password": temporary_password,
                "old_email": old_email,
                "new_email": to_email,
                "app_name": "ChatBot UFPS",
                "frontend_url": self.frontend_url,
                "support_email": "support@chatbot.ufps.edu.co"
            }

            # Render HTML template
            html_content = template.render(**template_vars)

            # Create plain text fallback
            text_content = self._create_email_change_success_text(
                temporary_password=temporary_password,
                old_email=old_email,
                new_email=to_email
            )

            # Send email
            success = await self.send_email(
                to_email=to_email,
                subject="🔐 ¡Email actualizado! - Contraseña temporal - ChatBot UFPS",
                html_content=html_content,
                text_content=text_content
            )

            if success:
                logger.info("Email change success notification sent to %s", to_email)
            else:
                logger.error("Failed to send email change success notification to %s", to_email)

            return success

        except Exception as e:
            logger.error("Error sending email change success notification to %s: %s", to_email, str(e))
            return False
    
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
                logger.info("Password reset email sent to %s", to_email)
            else:
                logger.error("Failed to send password reset email to %s", to_email)
                
            return success
            
        except Exception as e:
            logger.error("Error sending password reset email to %s: %s", to_email, str(e))
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

    def _create_welcome_text(self, user_name: str, temporary_password: Optional[str]) -> str:
        """Create plain text version of welcome email"""
        return f"""
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

    def _create_email_change_verification_text(self, verification_code: str, new_email: str) -> str:
        """Create plain text version of email change verification"""
        return f"""
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

    def _create_email_change_confirmation_text(self, confirm_url: str, old_email: str, new_email: str) -> str:
        """Create plain text version of email change confirmation"""
        return f"""
✅ Confirma tu nuevo email

Hola,

Has solicitado cambiar tu dirección de correo electrónico en ChatBot UFPS.

Email anterior: {old_email}
Nuevo email: {new_email}

Para completar el cambio, visita este enlace:
{confirm_url}

⚠️ Importante: Este enlace expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo de forma segura.

---
📧 ¿Necesitas ayuda? Contacta a: support@chatbot.ufps.edu.co
🌐 Sitio web: {self.frontend_url}
        """.strip()

    def _create_email_change_success_text(self, temporary_password: str, old_email: str, new_email: str) -> str:
        """Create plain text version of email change success notification"""
        return f"""
🔐 ¡Email actualizado exitosamente!

Hola,

Tu dirección de correo electrónico ha sido cambiada exitosamente en ChatBot UFPS.

📧 Email anterior: {old_email}
📧 Email nuevo: {new_email}

🔑 Tu contraseña temporal: {temporary_password}

⚠️ IMPORTANTE: Por seguridad, debes cambiar esta contraseña temporal lo antes posible.

Pasos para cambiar tu contraseña:
1. Inicia sesión con tu nuevo email y la contraseña temporal
2. Ve a tu perfil de usuario
3. Haz clic en "Cambiar contraseña"
4. Establece una nueva contraseña segura

Si no cambias la contraseña temporal, tu cuenta podría estar en riesgo.

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
            # Load email template
            template = self.jinja_env.get_template("welcome_email.html")

            # Prepare template variables
            template_vars = {
                "user_name": user_name,
                "temporary_password": temporary_password,
                "frontend_url": self.frontend_url,
                "app_name": "ChatBot UFPS",
                "support_email": "support@chatbot.ufps.edu.co"
            }

            # Render HTML template
            html_content = template.render(**template_vars)

            # Create plain text fallback
            text_content = self._create_welcome_text(
                user_name=user_name,
                temporary_password=temporary_password
            )

            # Send email
            success = await self.send_email(
                to_email=to_email,
                subject="🎉 ¡Bienvenido a ChatBot UFPS!",
                html_content=html_content,
                text_content=text_content
            )

            if success:
                logger.info("Welcome email sent to %s", to_email)
            else:
                logger.error("Failed to send welcome email to %s", to_email)

            return success

        except Exception as e:
            logger.error("Error sending welcome email to %s: %s", to_email, str(e))
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
            # Load email template
            template = self.jinja_env.get_template("email_change_verification.html")

            # Prepare template variables
            template_vars = {
                "verification_code": verification_code,
                "new_email": new_email,
                "app_name": "ChatBot UFPS",
                "frontend_url": self.frontend_url,
                "support_email": "support@chatbot.ufps.edu.co"
            }

            # Render HTML template
            html_content = template.render(**template_vars)

            # Create plain text fallback
            text_content = self._create_email_change_verification_text(
                verification_code=verification_code,
                new_email=new_email
            )

            # Send email
            success = await self.send_email(
                to_email=to_email,
                subject="🔐 Código de Verificación - Cambio de Email - ChatBot UFPS",
                html_content=html_content,
                text_content=text_content
            )

            if success:
                logger.info("Email change verification sent to %s", to_email)
            else:
                logger.error("Failed to send email change verification to %s", to_email)

            return success

        except Exception as e:
            logger.error("Error sending email change verification to %s: %s", to_email, str(e))
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
            # Load email template
            template = self.jinja_env.get_template("email_change_confirmation.html")

            # Create confirmation URL
            confirm_url = f"{self.frontend_url}/auth/email-change-complete?token={confirm_token}"

            # Prepare template variables
            template_vars = {
                "confirm_url": confirm_url,
                "old_email": old_email,
                "new_email": to_email,
                "app_name": "ChatBot UFPS",
                "frontend_url": self.frontend_url,
                "support_email": "support@chatbot.ufps.edu.co"
            }

            # Render HTML template
            html_content = template.render(**template_vars)

            # Create plain text fallback
            text_content = self._create_email_change_confirmation_text(
                confirm_url=confirm_url,
                old_email=old_email,
                new_email=to_email
            )

            # Send email
            success = await self.send_email(
                to_email=to_email,
                subject="Confirma tu nuevo email - ChatBot UFPS",
                html_content=html_content,
                text_content=text_content
            )

            if success:
                logger.info("Email change confirmation sent to %s", to_email)
            else:
                logger.error("Failed to send email change confirmation to %s", to_email)

            return success

        except Exception as e:
            logger.error("Error sending email change confirmation to %s: %s", to_email, str(e))
            return False


# Global email service instance
email_service = EmailService()

