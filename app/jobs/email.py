import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app
from app import Q


class Email:
    def __init__(self):
        self.smtp_username = current_app.config["MAIL_USERNAME"]
        self.smtp_password = current_app.config["MAIL_PASSWORD"]
        self.host = current_app.config["MAIL_SERVER"]
        self.port = current_app.config["MAIL_PORT"]
        self.tls = current_app.config["MAIL_USE_TLS"]

    def send(self, email_address):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = self.subject
        msg["From"] = email.utils.formataddr(
            ("Holepunch NOREPLY", "noreply@holepunch.io")
        )
        msg["To"] = email_address
        part1 = MIMEText(self.body_text, "plain")
        part2 = MIMEText(self.body_html, "html")
        msg.attach(part1)
        msg.attach(part2)
        if self.tls:
            server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            server = smtplib.SMTP(self.host, self.port)
        server.login(self.smtp_username, self.smtp_password)
        server.sendmail("noreply@holepunch.io", email_address, msg.as_string())
        server.close()
        pass


@Q.job(timeout=60000)
def send_beta_backlog_notification_email(email_address):
    email = Email()
    email.subject = "Holepunch beta"
    email.body_text = "We have reached the limit on beta users. We will notify you when space has opened up."
    email.body_html = f"""
<html>
<head></head>
<body>
<h1>Holepunch email confirmation</h1>
    <p>We have reached the limit on beta users. We will notify you when space has opened up.</p>
    </body>
</html>
"""
    email.send(email_address)


@Q.job(timeout=60000)
def send_confirm_email(email_address, token_url):
    email = Email()
    email.subject = "Account Email Verification"
    email.body_text = "Click this link to register your account: " + token_url
    email.body_html = f"""
<html>
<head></head>
<body>
<h1>Holepunch email confirmation</h1>
    <p>Visit <a href="{token_url}">{token_url}</a> to register your account.</p>
    </body>
</html>
"""
    email.send(email_address)


@Q.job(timeout=60000)
def send_password_change_confirm_email(email_address):
    email = Email()
    email.subject = "You've successfully changed your Holepunch password"
    email.body_text = ""
    email.body_html = f"""
                <html>
                <head></head>
                <body>
                    <h1>
                        Holepunch Password Change Confirmation
                    </h1>
                    <p>Your Holepunch account password was recently changed.</p>
                    <p>If you didn't make this change, please let us know.</p>
                    <p>Thanks!</p>
                    <p> - The Holepunch Team</p>
                </body>
                </html>
                """
    email.send(email_address)
