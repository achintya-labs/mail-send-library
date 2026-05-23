from __future__ import annotations

import base64
import mimetypes
import pickle
import webbrowser

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailClientError(Exception):
    """Base exception for all Gmail client errors."""


class GmailAuthenticationError(GmailClientError):
    """Raised when Gmail OAuth authentication fails."""


class GmailSendError(GmailClientError):
    """Raised when email sending fails."""


class GmailClient:
    """
    Gmail API email client.

    This client handles:
    - OAuth authentication
    - Credential persistence
    - Email sending
    - Attachments

    Example:
        gmail = GmailClient(
            secrets_file="secret.json",
        )

        gmail.send_email(
            sender="me@gmail.com",
            to="user@example.com",
            subject="Hello",
            message_text_plain="Hello world",
        )
    """

    def __init__(
        self,
        secrets_file: str | Path,
        credentials_dir: str | Path = "./credentials",
        credentials_filename: str = "gmail_credentials.pkl",
    ) -> None:
        """
        Initialize Gmail client.

        Args:
            secrets_file:
                Path to Google OAuth client secrets JSON.

            credentials_dir:
                Directory used to store cached credentials.

            credentials_filename:
                Name of credential cache file.
        """

        self.secrets_file = Path(secrets_file).expanduser().resolve()

        self.credentials_dir = (
            Path(credentials_dir).expanduser().resolve()
        )

        self.credentials_path = (
            self.credentials_dir / credentials_filename
        )

        self._validate_paths()

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def _validate_paths(self) -> None:
        """
        Validate OAuth secret paths and create credential directory.
        """

        if not self.secrets_file.exists():
            raise FileNotFoundError(
                f"OAuth secrets file not found: "
                f"{self.secrets_file}"
            )

        self.credentials_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # -------------------------------------------------------------------------
    # OAuth Authentication
    # -------------------------------------------------------------------------

    def _perform_oauth_flow(self):
        """
        Perform Google OAuth authentication flow.

        A temporary localhost HTTP server is created to receive
        the OAuth callback from Google.

        Returns:
            Google OAuth credentials object.

        Raises:
            GmailAuthenticationError:
                If authentication fails.
        """

        auth_response = {
            "code": None,
            "error": None,
        }

        class OAuthHandler(BaseHTTPRequestHandler):
            """
            Temporary HTTP handler used for OAuth callback.
            """

            def do_GET(self):
                """
                Handle OAuth redirect callback.
                """

                query = parse_qs(
                    urlparse(self.path).query
                )

                if "code" in query:
                    auth_response["code"] = query["code"][0]

                if "error" in query:
                    auth_response["error"] = query["error"][0]

                self.send_response(200)
                self.end_headers()

                self.wfile.write(
                    b"""
Authentication successful.

You may close this tab.
"""
                )

            def log_message(self, format, *args):
                """
                Disable default HTTP request logging.
                """
                return

        try:

            # Create temporary local HTTP server.
            server = HTTPServer(
                ("localhost", 0),
                OAuthHandler,
            )

            # Random available port assigned by OS.
            port = server.server_address[1]

            redirect_uri = f"http://localhost:{port}/"

            # Create OAuth flow.
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.secrets_file),
                SCOPES,
                redirect_uri=redirect_uri,
            )

            auth_url, _ = flow.authorization_url(
                access_type="offline",
                prompt="consent",
            )

            print("\nOpen this URL in your browser:\n")
            print(auth_url)
            print()

            # Attempt automatic browser launch.
            try:
                webbrowser.open(auth_url)

            except Exception:
                pass

            # Continue serving requests until OAuth callback arrives.
            while (
                auth_response["code"] is None
                and auth_response["error"] is None
            ):
                server.handle_request()

            server.server_close()

            if auth_response["error"]:
                raise GmailAuthenticationError(
                    f"OAuth authorization failed: "
                    f"{auth_response['error']}"
                )

            if auth_response["code"] is None:
                raise GmailAuthenticationError(
                    "OAuth callback was never received."
                )

            # Exchange authorization code for access token.
            flow.fetch_token(
                code=auth_response["code"]
            )

            return flow.credentials

        except Exception as exc:
            raise GmailAuthenticationError(
                f"OAuth flow failed: {exc}"
            ) from exc

    def _get_credentials(self):
        """
        Retrieve valid Gmail OAuth credentials.

        Credentials are:
        1. Loaded from cache if available.
        2. Refreshed if expired.
        3. Created via OAuth if missing.

        Returns:
            Valid Google OAuth credentials.
        """

        credentials = None

        # Load cached credentials.
        if self.credentials_path.exists():

            try:
                with open(
                    self.credentials_path,
                    "rb",
                ) as token:

                    credentials = pickle.load(token)

            except Exception:
                credentials = None

        try:

            # Existing valid credentials.
            if credentials and credentials.valid:
                return credentials

            # Refresh expired credentials.
            if (
                credentials
                and credentials.expired
                and credentials.refresh_token
            ):
                credentials.refresh(Request())

            # Perform fresh OAuth flow.
            else:
                credentials = self._perform_oauth_flow()

            # Save updated credentials.
            with open(
                self.credentials_path,
                "wb",
            ) as token:

                pickle.dump(credentials, token)

            return credentials

        except Exception as exc:
            raise GmailAuthenticationError(
                f"Failed to obtain credentials: {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # Gmail API
    # -------------------------------------------------------------------------

    def _build_service(self):
        """
        Build Gmail API service client.

        Returns:
            Gmail API service object.
        """

        credentials = self._get_credentials()

        try:
            return build(
                "gmail",
                "v1",
                credentials=credentials,
                cache_discovery=False,
            )

        except Exception as exc:
            raise GmailAuthenticationError(
                f"Failed to initialize Gmail service: "
                f"{exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

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
        """
        Send email using Gmail API.

        Args:
            sender:
                Sender email address.

            to:
                Recipient email address.

            subject:
                Email subject.

            message_text_plain:
                Plain text email body.

            message_text_html:
                HTML email body.

            cc:
                Optional CC recipients.

            attachment:
                Optional file attachment path.

        Returns:
            Gmail API response dictionary.

        Raises:
            GmailSendError:
                If email sending fails.
        """

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
                .send(
                    userId="me",
                    body=body,
                )
                .execute()
            )

            return {
                "success": True,
                "message_id": response.get("id"),
                "thread_id": response.get("threadId"),
            }

        except HttpError as exc:
            raise GmailSendError(
                f"Gmail API error: {exc}"
            ) from exc

        except Exception as exc:
            raise GmailSendError(
                f"Unexpected Gmail error: {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # Message Creation
    # -------------------------------------------------------------------------

    def _create_message_without_attachment(
        self,
        sender: str,
        to: str,
        cc: str,
        subject: str,
        message_text_plain: str,
        message_text_html: str,
    ) -> dict:
        """
        Create Gmail message without attachment.

        Returns:
            Gmail API raw message dictionary.
        """

        message = MIMEMultipart("alternative")

        message["Subject"] = subject
        message["From"] = sender
        message["To"] = to

        if cc:
            message["CC"] = cc

        if message_text_plain:
            message.attach(
                MIMEText(
                    message_text_plain,
                    "plain",
                )
            )

        if message_text_html:
            message.attach(
                MIMEText(
                    message_text_html,
                    "html",
                )
            )

        return {
            "raw": self._encode_message(message)
        }

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
        """
        Create Gmail message with attachment.

        Returns:
            Gmail API raw message dictionary.
        """

        attachment_path = Path(attachment_path)

        if not attachment_path.exists():
            raise FileNotFoundError(
                f"Attachment not found: "
                f"{attachment_path}"
            )

        message = MIMEMultipart()

        message["Subject"] = subject
        message["From"] = sender
        message["To"] = to

        if cc:
            message["CC"] = cc

        if message_text_plain:
            message.attach(
                MIMEText(
                    message_text_plain,
                    "plain",
                )
            )

        if message_text_html:
            message.attach(
                MIMEText(
                    message_text_html,
                    "html",
                )
            )

        attachment = self._build_attachment(
            attachment_path
        )

        message.attach(attachment)

        return {
            "raw": self._encode_message(message)
        }

    # -------------------------------------------------------------------------
    # Attachment Helpers
    # -------------------------------------------------------------------------

    def _build_attachment(
        self,
        attachment_path: Path,
    ):
        """
        Build MIME attachment object from file.

        Args:
            attachment_path:
                Path to attachment file.

        Returns:
            MIME attachment object.
        """

        mime_type, encoding = mimetypes.guess_type(
            str(attachment_path)
        )

        if (
            mime_type is None
            or encoding is not None
        ):
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

            attachment = MIMEBase(
                main_type,
                sub_type,
            )

            attachment.set_payload(file_data)

        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=attachment_path.name,
        )

        return attachment

    # -------------------------------------------------------------------------
    # Encoding Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _encode_message(message) -> str:
        """
        Encode MIME message into Gmail API raw format.

        Args:
            message:
                MIME email message.

        Returns:
            Base64 URL-safe encoded message.
        """

        return (
            base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()
        )


if __name__ == "__main__":

    gmail = GmailClient(
        secrets_file="./secret.json",
    )

    try:

        response = gmail.send_email(
            sender="your_email@gmail.com",
            to="recipient@example.com",
            subject="Test Email",

            message_text_plain="""
Hello from Gmail API
""",

            message_text_html="""
<h1>Hello from Gmail API</h1>
""",

            attachment=None,
        )

        print("\nEmail sent successfully")
        print(response)

    except GmailClientError as exc:
        print(f"\nERROR: {exc}")