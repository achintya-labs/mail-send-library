from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Optional

import httplib2
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from googleapiclient import discovery, errors
from oauth2client import client, file, tools


SCOPES = "https://www.googleapis.com/auth/gmail.send"
APPLICATION_NAME = "MailPkg Gmail Client"


class GmailClientError(Exception):
    """Base Gmail client exception."""


class GmailAuthenticationError(GmailClientError):
    """Raised when OAuth authentication fails."""


class GmailSendError(GmailClientError):
    """Raised when email sending fails."""


class GmailClient:
    """
    Gmail API email client.

    Example:
        gmail = GmailClient(
            secrets_file="secret.json",
            credentials_dir="./credentials",
        )

        gmail.send_email(
            sender="me@gmail.com",
            to="user@example.com",
            subject="Hello",
            message_text_plain="Plain text",
            message_text_html="<b>Hello</b>",
            attachment="report.pdf",
        )
    """

    def __init__(
        self,
        secrets_file: str | Path,
        credentials_dir: str | Path = "./credentials",
        credentials_filename: str = "gmail_credentials.json",
    ) -> None:

        self.secrets_file = Path(secrets_file).expanduser().resolve()
        self.credentials_dir = Path(credentials_dir).expanduser().resolve()
        self.credentials_path = self.credentials_dir / credentials_filename

        self._validate_paths()

    def _validate_paths(self) -> None:
        if not self.secrets_file.exists():
            raise FileNotFoundError(
                f"Gmail OAuth secrets file not found: {self.secrets_file}"
            )

        self.credentials_dir.mkdir(parents=True, exist_ok=True)

    def _get_credentials(self):
        store = file.Storage(str(self.credentials_path))
        credentials = store.get()

        if credentials and not credentials.invalid:
            return credentials

        try:
            flow = client.flow_from_clientsecrets(
                str(self.secrets_file),
                SCOPES,
            )

            flow.user_agent = APPLICATION_NAME

            credentials = tools.run_flow(flow, store)

            return credentials

        except Exception as exc:
            raise GmailAuthenticationError(
                f"Failed to authenticate Gmail client: {exc}"
            ) from exc

    def _build_service(self):
        credentials = self._get_credentials()

        try:
            http = credentials.authorize(httplib2.Http())

            return discovery.build(
                "gmail",
                "v1",
                http=http,
                cache_discovery=False,
            )

        except Exception as exc:
            raise GmailAuthenticationError(
                f"Failed to initialize Gmail service: {exc}"
            ) from exc

    def send_email(
        self,
        sender: str,
        to: str,
        subject: str,
        message_text_plain: str = "",
        message_text_html: str = "",
        cc: str = "",
        attachment: Optional[str | Path] = None,
    ) -> dict:

        service = self._build_service()

        if attachment:
            body = self._create_message_with_attachment(
                sender=sender,
                to=to,
                cc=cc,
                subject=subject,
                message_text_plain=message_text_plain,
                message_text_html=message_text_html,
                attachment_path=attachment,
            )
        else:
            body = self._create_message_without_attachment(
                sender=sender,
                to=to,
                cc=cc,
                subject=subject,
                message_text_plain=message_text_plain,
                message_text_html=message_text_html,
            )

        try:
            response = (
                service.users()
                .messages()
                .send(userId="me", body=body)
                .execute()
            )

            return {
                "success": True,
                "message_id": response.get("id"),
                "thread_id": response.get("threadId"),
            }

        except errors.HttpError as exc:
            raise GmailSendError(
                f"Gmail API error while sending email: {exc}"
            ) from exc

        except Exception as exc:
            raise GmailSendError(
                f"Unexpected error while sending email: {exc}"
            ) from exc

    def _create_message_without_attachment(
        self,
        sender: str,
        to: str,
        cc: str,
        subject: str,
        message_text_plain: str,
        message_text_html: str,
    ) -> dict:

        message = MIMEMultipart("alternative")

        message["Subject"] = subject
        message["From"] = sender
        message["To"] = to

        if cc:
            message["CC"] = cc

        if message_text_plain:
            message.attach(MIMEText(message_text_plain, "plain"))

        if message_text_html:
            message.attach(MIMEText(message_text_html, "html"))

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        return {"raw": raw_message}

    def _create_message_with_attachment(
        self,
        sender: str,
        to: str,
        cc: str,
        subject: str,
        message_text_plain: str,
        message_text_html: str,
        attachment_path: str | Path,
    ) -> dict:

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

        if message_text_plain:
            message.attach(MIMEText(message_text_plain, "plain"))

        if message_text_html:
            message.attach(MIMEText(message_text_html, "html"))

        mime_type, encoding = mimetypes.guess_type(str(attachment_path))

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

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        return {"raw": raw_message}


if __name__ == "__main__":

    gmail = GmailClient(
        secrets_file="./secret.json",
        credentials_dir="./credentials",
    )

    try:
        response = gmail.send_email(
            sender="your_email@gmail.com",
            to="recipient@example.com",
            subject="Test Email",
            message_text_plain="Hello from Gmail API",
            message_text_html="<h1>Hello from Gmail API</h1>",
            attachment=None,
        )

        print("Email sent successfully")
        print(response)

    except GmailClientError as exc:
        print(f"ERROR: {exc}")