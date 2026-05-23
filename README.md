
# email_sender

Unified Python email package supporting:

- Gmail API
- ZeptoMail SMTP

---

# Installation

## Install locally

```bash
pip install .
```

## Development install

```bash
pip install -e .
```

---

# Package Structure

```text
email_sender/
├── pyproject.toml
├── README.md
└── email_sender/
    ├── __init__.py
    ├── gmail/
    │   ├── __init__.py
    │   └── client.py
    └── zeptomail/
        ├── __init__.py
        └── client.py
```

---

# Importing

```python
from email_sender import GmailClient
from email_sender import ZeptoMailClient
```

---

# Gmail Setup

## 1. Enable Gmail API

Go to:

https://console.cloud.google.com/

Then:

1. Create a project
2. Enable Gmail API
3. Create OAuth credentials
4. Download the OAuth JSON file

Rename it to something like:

```text
secret.json
```

---

## 2. Gmail Credentials Flow

On first login:

- browser authentication opens
- OAuth token is generated
- credentials stored locally

Example credentials folder:

```text
credentials/
└── gmail_credentials.json
```

---

# Gmail Usage

## Basic Email

```python
from email_sender import GmailClient

gmail = GmailClient(
    secrets_file="./secret.json",
    credentials_dir="./credentials",
)

response = gmail.send_email(
    sender="you@gmail.com",
    to="user@example.com",
    subject="Hello",
    message_text_plain="Hello world",
)

print(response)
```

---

## HTML Email

```python
response = gmail.send_email(
    sender="you@gmail.com",
    to="user@example.com",
    subject="HTML Email",
    message_text_html="""
    <h1>Hello</h1>
    <p>This is HTML email.</p>
    """,
)
```

---

## Email With Attachment

```python
response = gmail.send_email(
    sender="you@gmail.com",
    to="user@example.com",
    subject="Report",
    message_text_plain="Attached report.",
    attachment="./report.pdf",
)
```

---

# ZeptoMail Setup

Create a credentials file:

```json
{
    "username": "your_smtp_username",
    "password": "your_smtp_password",
    "replyemail": "reply@example.com"
}
```

Save as:

```text
zepto.json
```

---

# ZeptoMail Usage

## Basic Email

```python
from email_sender import ZeptoMailClient

zepto = ZeptoMailClient(
    credentials_file="./zepto.json"
)

response = zepto.send_email(
    sender="sender@example.com",
    to="user@example.com",
    subject="Hello",
    message_text_plain="Hello from ZeptoMail",
)

print(response)
```

---

## HTML Email

```python
response = zepto.send_email(
    sender="sender@example.com",
    to="user@example.com",
    subject="HTML Email",
    message_text_html="""
    <h1>Hello</h1>
    <p>This is HTML email.</p>
    """,
)
```

---

## Email With Attachment

```python
response = zepto.send_email(
    sender="sender@example.com",
    to="user@example.com",
    subject="Attachment",
    message_text_plain="Please find attachment.",
    attachment="./report.pdf",
)
```

---

# CC and Reply-To

```python
response = zepto.send_email(
    sender="sender@example.com",
    to="user@example.com",
    cc="manager@example.com",
    reply_to="support@example.com",
    subject="Team Update",
    message_text_plain="Update attached.",
)
```

---

# Error Handling

## Gmail

```python
from email_sender import (
    GmailClient,
    GmailClientError,
)

try:
    gmail = GmailClient(
        secrets_file="./secret.json"
    )

    gmail.send_email(
        sender="you@gmail.com",
        to="user@example.com",
        subject="Test",
    )

except GmailClientError as exc:
    print(f"Error: {exc}")
```

---

## ZeptoMail

```python
from email_sender import (
    ZeptoMailClient,
    ZeptoMailError,
)

try:
    zepto = ZeptoMailClient(
        credentials_file="./zepto.json"
    )

    zepto.send_email(
        sender="sender@example.com",
        to="user@example.com",
        subject="Test",
    )

except ZeptoMailError as exc:
    print(f"Error: {exc}")
```

---

# Example Response

```python
{
    "success": True,
    "message_id": "...",
    "thread_id": "..."
}
```

---

# Recommended .gitignore

```gitignore
# OAuth credentials
secret.json
zepto.json

# Generated OAuth tokens
credentials/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual env
venv/
.env/
```

---

# Recommended Usage Pattern

```python
from email_sender import GmailClient

gmail = GmailClient(
    secrets_file="./secret.json",
)

gmail.send_email(
    sender="you@gmail.com",
    to="user@example.com",
    subject="Hello",
    message_text_plain="Hello world",
)
```

---

# License

Copyright 2026 Achintya Raghavan 