import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os


def send_email(smtp_host: str, smtp_port: int, username: str, password: str,
               to: str, subject: str, body: str, is_html: bool = False,
               attachment_path: str = None) -> dict:
    from core.validation import validate_not_empty_or_error, validate_email_or_error
    err = validate_not_empty_or_error(smtp_host, "smtp_host") \
          or validate_not_empty_or_error(username, "username") \
          or validate_not_empty_or_error(to, "to") \
          or validate_email_or_error(to)
    if err:
        return {"success": False, "error": err}
    try:
        msg = MIMEMultipart()
        msg["From"] = username
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html" if is_html else "plain"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f'attachment; filename="{os.path.basename(attachment_path)}"')
            msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(username, password)
            server.send_message(msg)

        return {"success": True, "to": to, "subject": subject}
    except Exception as e:
        return {"success": False, "error": str(e)}


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="send_email",
        description="Send an email via SMTP. Supports HTML body and file attachments.",
        parameters={"type": "object", "properties": {
            "smtp_host": {"type": "string"},
            "smtp_port": {"type": "integer"},
            "username": {"type": "string"},
            "password": {"type": "string"},
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
            "is_html": {"type": "boolean"},
            "attachment_path": {"type": "string"},
        }},
        execute_fn=lambda smtp_host="", smtp_port=465, username="", password="",
                      to="", subject="", body="", is_html=False, attachment_path=None:
            send_email(smtp_host, smtp_port, username, password,
                       to, subject, body, is_html, attachment_path),
    )


def unregister_tools():
    from core.tool_registry import registry
    registry.unregister("send_email")
