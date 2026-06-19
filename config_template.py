API_KEY = "YOUR_SEND_MAIL_TOKEN"

API_URL = "https://api.zeptomail.in/v1.1/email/batch"

SENDER_EMAIL = "noreply@example.com"
SENDER_NAME = "Example Company"

REPLY_TO_EMAIL = "support@example.com"

SUBJECT = "Welcome {{name}}"

CSV_FILE = "recipients.csv"
HTML_FILE = "email_template.html"

BATCH_SIZE = 500


# Set True for testing without CSV
USE_TEST_RECIPIENTS = False

TEST_RECIPIENTS = [
    {
        "name": "John Doe",
        "email": "john@example.com",
    },
    {
        "name": "Jane Smith",
        "email": "jane@example.com",
    },
]
