from email_sender import (
    ZeptoMailClient,
    ZeptoMailError,
)


def main():

    zepto = ZeptoMailClient(
        credentials_file="./zepto.json"
    )

    try:
        response = zepto.send_email(
            sender="sender@example.com",
            to="recipient@example.com",
            subject="Test Email from ZeptoMail",

            message_text_plain="""
Hello,

This is a plain text email sent using ZeptoMail.

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
            reply_to="support@example.com",

            # Optional
            attachment="./report.pdf",
        )

        print("Email sent successfully")
        print(response)

    except ZeptoMailError as exc:
        print(f"ZeptoMail Error: {exc}")


if __name__ == "__main__":
    main()