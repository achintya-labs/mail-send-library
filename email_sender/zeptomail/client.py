from __future__ import annotations

import json
import mimetypes
import smtplib
import ssl
from pathlib import Path
from typing import Optional

from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


SMTP_SERVER = "smtp.zeptomail.in"
SMTP_PORT = 587


class ZeptoMailError(Exception):
    """Base ZeptoMail exception."""


class ZeptoMailAuthenticationError(ZeptoMailError):
    """Raised when SMTP authentication fails."""


class ZeptoMailSendError(ZeptoMailError):
    """Raised when sending email fails."""


class ZeptoMailConfigurationError(ZeptoMailError):
    """Raised when config file is invalid."""


class ZeptoMailClient:
    """
    ZeptoMail SMTP client.

    Expected credentials JSON format:

    {
        "username": "your_smtp_username",
        "password": "your_smtp_password",
        "replyemail": "reply@example.com"
    }

    Example:
        zepto = ZeptoMailClient(
            credentials_file="./zepto.json"
        )

        zepto.send_email(
            sender="sender@example.com",
            to="user@example.com",
            subject="Hello",
            message_text_html="<h1>Hello</h1>",
            attachment="report.pdf",
        )
    """

    def __init__(
        self,
        credentials_file: str | Path,
        smtp_server: str = SMTP_SERVER,
        smtp_port: int = SMTP_PORT,
    ) -> None:

        self.credentials_file = (
            Path(credentials_file)
            .expanduser()
            .resolve()
        )

        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

        self.credentials = self._load_credentials()

    def _load_credentials(self) -> dict:

        if not self.credentials_file.exists():
            raise FileNotFoundError(
                f"ZeptoMail credentials file not found: "
                f"{self.credentials_file}"
            )

        try:
            with open(self.credentials_file, "r") as fp:
                credentials = json.load(fp)

        except json.JSONDecodeError as exc:
            raise ZeptoMailConfigurationError(
                f"Invalid JSON in credentials file: {exc}"
            ) from exc

        required_keys = {
            "username",
            "password",
            "replyemail",
        }

        missing_keys = required_keys - credentials.keys()

        if missing_keys:
            raise ZeptoMailConfigurationError(
                f"Missing required keys in credentials file: "
                f"{', '.join(sorted(missing_keys))}"
            )

        return credentials

    def _create_server(self) -> smtplib.SMTP:

        try:
            context = ssl.create_default_context()

            server = smtplib.SMTP(
                self.smtp_server,
                self.smtp_port,
            )

            server.starttls(context=context)

            server.login(
                self.credentials["username"],
                self.credentials["password"],
            )

            return server

        except smtplib.SMTPAuthenticationError as exc:
            raise ZeptoMailAuthenticationError(
                "Invalid ZeptoMail SMTP credentials"
            ) from exc

        except Exception as exc:
            raise ZeptoMailAuthenticationError(
                f"Failed to connect to ZeptoMail SMTP server: {exc}"
            ) from exc

    def send_email(
        self,
        sender: str,
        to: str,
        subject: str,
        message_text_plain: str = "",
        message_text_html: str = "",
        cc: str = "",
        reply_to: Optional[str] = None,
        attachment: Optional[str | Path] = None,
    ) -> dict:

        if reply_to is None:
            reply_to = self.credentials["replyemail"]

        if attachment:
            message = self._create_message_with_attachment(
                sender=sender,
                to=to,
                cc=cc,
                subject=subject,
                message_text_plain=message_text_plain,
                message_text_html=message_text_html,
                reply_to=reply_to,
                attachment_path=attachment,
            )
        else:
            message = self._create_message_without_attachment(
                sender=sender,
                to=to,
                cc=cc,
                subject=subject,
                message_text_plain=message_text_plain,
                message_text_html=message_text_html,
                reply_to=reply_to,
            )

        try:
            with self._create_server() as server:
                server.send_message(message)

            return {
                "success": True,
                "recipient": to,
                "subject": subject,
            }

        except Exception as exc:
            raise ZeptoMailSendError(
                f"Failed to send email: {exc}"
            ) from exc

    def _create_message_without_attachment(
        self,
        sender: str,
        to: str,
        cc: str,
        subject: str,
        message_text_plain: str,
        message_text_html: str,
        reply_to: str,
    ) -> MIMEMultipart:

        message = MIMEMultipart("alternative")

        message["Subject"] = subject
        message["From"] = sender
        message["To"] = to

        if cc:
            message["CC"] = cc

        message["Reply-To"] = reply_to

        if message_text_plain:
            message.attach(MIMEText(message_text_plain, "plain"))

        if message_text_html:
            message.attach(MIMEText(message_text_html, "html"))

        return message

    def _create_message_with_attachment(
        self,
        sender: str,
        to: str,
        cc: str,
        subject: str,
        message_text_plain: str,
        message_text_html: str,
        reply_to: str,
        attachment_path: str | Path,
    ) -> MIMEMultipart:

        attachment_path = Path(attachment_path)

        if not attachment_path.exists():
            raise FileNotFoundError(
                f"Attachment not found: {attachment_path}"
            )

        message = MIMEMultipart()

        message["Subject"] = subject
        message["From"] = sender
        message["To"] = to

        if cc:
            message["CC"] = cc

        message["Reply-To"] = reply_to

        if message_text_plain:
            message.attach(MIMEText(message_text_plain, "plain"))

        if message_text_html:
            message.attach(MIMEText(message_text_html, "html"))

        mime_type, encoding = mimetypes.guess_type(
            str(attachment_path)
        )

        if mime_type is None or encoding is not None:
            mime_type = "application/octet-stream"

        main_type, sub_type = mime_type.split("/", 1)

        with open(attachment_path, "rb") as fp:
            file_data = fp.read()

        if main_type == "text":
            attachment = MIMEText(
                file_data.decode(),
                _subtype=sub_type,
            )

        elif main_type == "image":
            attachment = MIMEImage(
                file_data,
                _subtype=sub_type,
            )

        elif main_type == "audio":
            attachment = MIMEAudio(
                file_data,
                _subtype=sub_type,
            )

        elif main_type == "application":
            attachment = MIMEApplication(
                file_data,
                _subtype=sub_type,
            )

        else:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(file_data)

        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=attachment_path.name,
        )

        message.attach(attachment)

        return message


if __name__ == "__main__":

    zepto = ZeptoMailClient(
        credentials_file="./zepto.json"
    )

    try:
        response = zepto.send_email(
            sender="sender@example.com",
            to="recipient@example.com",
            subject="Test Email",
            message_text_plain="Hello from ZeptoMail",
            message_text_html="<h1>Hello from ZeptoMail</h1>",
            attachment=None,
        )

        print("Email sent successfully")
        print(response)

    except ZeptoMailError as exc:
        print(f"ERROR: {exc}")