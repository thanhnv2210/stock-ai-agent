"""
notifier.py

Sends alerts via console (always), Slack webhook, Telegram, and/or email (SMTP).

Configure via environment variables (or a .env file loaded before running):
  SLACK_WEBHOOK_URL    - Slack incoming webhook URL
  TELEGRAM_BOT_TOKEN  - Telegram bot token from @BotFather
  TELEGRAM_CHAT_ID    - Telegram chat/user ID to send messages to
  EMAIL_FROM           - Sender address
  EMAIL_TO             - Recipient address (comma-separated for multiple)
  EMAIL_SMTP_HOST      - SMTP host (default: smtp.gmail.com)
  EMAIL_SMTP_PORT      - SMTP port (default: 587)
  EMAIL_SMTP_PASSWORD  - SMTP password or app password
"""

import json
import os
import smtplib
import urllib.request
import urllib.parse
from email.mime.text import MIMEText


class Notifier:
    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_to = os.getenv("EMAIL_TO")
        self.smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.smtp_password = os.getenv("EMAIL_SMTP_PASSWORD")

    def send(self, subject: str, body: str):
        """Send an alert. Always prints to console; optionally sends Slack/Telegram/email."""
        print(f"\n[ALERT] {subject}\n{body}\n")
        if self.slack_webhook:
            self._send_slack(subject, body)
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(subject, body)
        if self.email_from and self.email_to and self.smtp_password:
            self._send_email(subject, body)

    def _send_telegram(self, subject: str, body: str):
        text = f"*{subject}*\n{body}"
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = json.dumps({
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=10)
            print("[Notifier] Telegram alert sent.")
        except Exception as e:
            print(f"[Notifier] Telegram failed: {e}")

    def _send_slack(self, subject: str, body: str):
        payload = json.dumps({"text": f"*{subject}*\n{body}"}).encode()
        req = urllib.request.Request(
            self.slack_webhook,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            print("[Notifier] Slack alert sent.")
        except Exception as e:
            print(f"[Notifier] Slack failed: {e}")

    def _send_email(self, subject: str, body: str):
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.email_from
        msg["To"] = self.email_to
        recipients = [r.strip() for r in self.email_to.split(",")]
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.smtp_password)
                server.sendmail(self.email_from, recipients, msg.as_string())
            print(f"[Notifier] Email sent to {self.email_to}.")
        except Exception as e:
            print(f"[Notifier] Email failed: {e}")
