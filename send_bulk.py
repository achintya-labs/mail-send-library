#!/usr/bin/env python3

import csv
from pathlib import Path

import requests

from config import *


def load_html():
    return Path(HTML_FILE).read_text(encoding="utf-8")


def load_recipients():
    if USE_TEST_RECIPIENTS:
        return TEST_RECIPIENTS

    recipients = []

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            recipients.append(
                {
                    "name": row["name"].strip(),
                    "email": row["email"].strip(),
                }
            )

    return recipients


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def build_payload(recipients, html_body):
    return {
        "from": {
            "address": SENDER_EMAIL,
            "name": SENDER_NAME,
        },
        "reply_to": [
            {
                "address": REPLY_TO_EMAIL
            }
        ],
        "subject": SUBJECT,
        "htmlbody": html_body,
        "to": [
            {
                "email_address": {
                    "address": r["email"],
                    "name": r["name"],
                },
                "merge_info": {
                    "name": r["name"]
                }
            }
            for r in recipients
        ]
    }


def send_batch(payload):
    headers = {
        "authorization": API_KEY,
        "content-type": "application/json",
        "accept": "application/json",
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def main():
    html_body = load_html()

    recipients = load_recipients()

    total = len(recipients)

    print(f"Loaded {total} recipients")

    batch_no = 1

    for batch in chunk(recipients, BATCH_SIZE):
        payload = build_payload(batch, html_body)

        result = send_batch(payload)

        print(
            f"Batch {batch_no}: "
            f"{len(batch)} recipients sent"
        )

        print(result)

        batch_no += 1


if __name__ == "__main__":
    main()
