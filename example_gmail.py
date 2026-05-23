from email_sender import (
    GmailClient,
    GmailClientError,
)


def main():

    gmail = GmailClient(
        secrets_file="./secret_gmail.json",
        credentials_dir="./_credentials",
    )

    try:
        response = gmail.send_email(
            sender="your_email@gmail.com",
            to="recipient@example.com",
            subject="Test Email from Gmail API",

            message_text_plain="""
Hello,

This is a plain text email sent using the Gmail API.

Regards,
email_sender
""",

            message_text_html="""
<h1>Hello</h1>

<p>
This is an HTML email sent using the
<b>email_sender</b> package.
</p>

<hr>

<p>Regards,<br>email_sender</p>
""",

            # Optional
            cc="manager@example.com",

            # Optional
            #attachment="./report.pdf",
        )

        print("Email sent successfully")
        print(response)

    except GmailClientError as exc:
        print(f"Gmail Error: {exc}")


if __name__ == "__main__":
    main()