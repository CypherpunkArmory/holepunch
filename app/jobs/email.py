import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app
from app import Q
from app.models import Plan


def squish(string):
    return " ".join(string.split())


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
        part1 = MIMEText(squish(self.body_text), "plain")
        part2 = MIMEText(squish(self.body_html), "html")
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


@Q.job(func_or_queue="email", timeout=60000)
def send_beta_backlog_notification_email(email_address):
    email = Email()
    email.subject = "Holepunch beta"
    email.body_text = """
    We have reached the limit on beta users.
    We will notify you when space has opened up."""
    email.body_html = f"""
<html>
<head></head>
<body>
<h1>Holepunch email confirmation</h1>
    <p>
        We have reached the limit on beta users.
        We will notify you when space has opened up.
    </p>
    </body>
</html>
"""
    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_confirm_email(email_address, token_url):
    email = Email()
    email.subject = "Account Email Verification"
    email.body_text = "Click this link to register your account: " + token_url
    email.body_html = f"""
<html>
<head></head>
<body>
<h1>Holepunch email confirmation</h1>
    <p>Visit <a href="{token_url}">{token_url}</a> to confirm your account.</p>
    </body>
</html>
"""
    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
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
    <p>If you didn't make this change, please let us know at support@holepunch.io</p>
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""

    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_password_reset_confirm_email(email_address, token_url):
    email = Email()
    email.subject = "Reset your Holepunch Password"
    email.body_text = "Click this link to reset your password: " + token_url
    email.body_html = f"""
<html>
<head></head>
<body>
    <h1>
        Holepunch Password Reset Request
    </h1>
    <p>You've requested that the password for your Holepunch account be reset.</p>
    <p>Visit <a href="{token_url}">{token_url}</a> to reset your password.</p>
    <p>If you didn't make this change, please let us know at support@holepunch.io</p>
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""

    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_email_change_confirm_email(email_address):
    email = Email()
    email.subject = "You've successfully changed your Holepunch email"
    email.body_text = (
        "Your holepunch email was changed - let us know if you didn't make this change."
    )
    email.body_html = f"""
<html>
<head></head>
<body>
    <h1>
        Holepunch Email Change Confirmation
    </h1>
    <p>Your Holepunch account email was recently changed.</p>
    <p>If you didn't make this change, please let us know at support@holepunch.io</p>
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""

    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_subscribed_successfully_email(email_address):
    email = Email()
    email.subject = "Welcome to Holepunch"
    email.body_text = "Your Holepunch subscription is now active"
    email.body_html = f"""
<html>
<head></head>
<body>
    <h1>
        Welcome to Holepunch!
    </h1>
    <p>Thanks for subscribing!  Your Holepunch.io Account is now Active</p>
    <p>If have any questions about your subscription, please let us know at support@holepunch.io</p>
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""
    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_subscribed_failed_email(email_address):
    email = Email()
    email.subject = "We've encountered a problem"
    email.body_text = """There was an error processing your payment
- please login to fix this problem and then try again"""
    email.body_html = f"""
<html>
<head></head>
<body>
    <h1>
        Something went wrong.
    </h1>
    <p>
        We tried to subscribe you to Holepunch.io - but we couldn't
        process your payment.
    </p>
    <p>Please visit holepunch.io to fix this problem and then try again.</p>
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""
    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_subscription_requires_action(email_address):
    email = Email()
    email.subject = "Holepunch.io: Additional Action is Required"
    email.body_text = """Your card has additional security measures that
    require you to approve this transaction."""
    email.body_html = f"""
<html>
<head></head>
<body>
    <h1>
        Additional Action is Required
    </h1>
    <p>
        We tried to subscribe you to Holepunch.io - but your payment
        method has additional security measures that require you
        to approve this transaction.
    </p>
    <p>Please visit holepunch.io to fix this problem and then try again.</p>
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""
    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_unsubscribe_required_email(email_address):
    email = Email()
    email.subject = "Holepunch.io: Additional Action is Required"
    email.body_text = """You must cancel your existing subscription before
    you can change the associated stripe account."""
    email.body_html = f"""
<html>
<head></head>
<body>
    <h1>
        Additional Action is Required
    </h1>
    <p>
        It seems you would like to point your holepunch user to a different
        Stripe Account. As this is a potential fraud risk for you, we require
        that your subscription be cancelled before we can make this change for you.
        If you didn't request this change, please contact support@holepunch.io.
    </p>
    <p>Please visit holepunch.io to fix this problem and then try again.</p>
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""
    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_unsubscribe_successful_email(email_address, old_plan_id):
    email = Email()
    plan = Plan.query.get(old_plan_id)
    email.subject = "You have been unsubscribed from Holepunch.io"
    email.body_text = "You have been unsubscribed from Holepunch.io"
    email.body_html = f"""
<html>
<head></head>
<body>
    <h1>
        Thank you for being a Holepunch.io Customer
    </h1>
    <p>
        We have cancelled your Holepunch subscription to
        our {plan.name} plan. Your subscription will be cancelled
        immediately. If there is time left on your billing cycle
        you may notice a refund for your unused subscription time on
        your next billing date.
    </p>
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""
    email.send(email_address)


@Q.job(func_or_queue="email", timeout=60000)
def send_unsubscribe_not_required_email(email_address):
    email = Email()
    email.subject = "We could not unsubscribe you from Holepunch.io"
    email.body_text = "There was an error unsubscribing you."
    email.body_html = f"""
<html>
<head></head>
<body>
    <h1>
        There seems to have been a mixup!
    </h1>
    <p>
        You have asked to cancel your Holepunch.io subscription, but
        we do not have a record of your subscription.
    </p>
    <p>
        If you were trying to delete your account, please visit
        <a href="http://holepunch.io/account">Your Holepunch.io account page</a>
    <p>
    <p>
        If you noticed a charge from Holepunch.io, and have received
        this email, please contact
        <a href="mailto:support@holepunch?subject=Subscription Cancellation Error">
        Holepunch Support
        </a> immediately so we can correct the error.
    <p>Thanks!</p>
    <p> - The Holepunch Team</p>
</body>
</html>
"""
    email.send(email_address)
