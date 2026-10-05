"""Quick SMTP test — run with: python test_smtp.py"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings

print(f"SMTP_USER : {settings.SMTP_USER!r}")
print(f"SMTP_PASS : {'SET (' + settings.SMTP_PASS[:4] + '…)' if settings.SMTP_PASS else 'EMPTY'}")
print(f"SMTP_HOST : {settings.SMTP_HOST}:{settings.SMTP_PORT}")
print(f"DEV_REDIRECT: {settings.DEV_REDIRECT_EMAIL!r}")
print()

if not settings.SMTP_USER or not settings.SMTP_PASS:
    print("❌ No credentials in .env — fix SMTP_USER / SMTP_PASS first")
    exit(1)

TO = settings.DEV_REDIRECT_EMAIL or settings.SMTP_USER
print(f"Sending test email to: {TO}")

try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "NDIS Manager — SMTP test"
    msg["From"]    = f"NDIS Manager <{settings.SMTP_USER}>"
    msg["To"]      = TO
    msg.attach(MIMEText("<h2>SMTP is working ✅</h2><p>Your OTP emails will arrive here.</p>", "html"))

    import socket
    # Force IPv4 — avoids ISP IPv6 filtering that drops AUTH responses
    ipv4 = socket.getaddrinfo(settings.SMTP_HOST, settings.SMTP_PORT, socket.AF_INET)[0][4][0]
    print(f"Connecting to IPv4: {ipv4}:{settings.SMTP_PORT}")

    if settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(ipv4, settings.SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(1)
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, TO, msg.as_string())
    else:
        with smtplib.SMTP(ipv4, settings.SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(1)
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, TO, msg.as_string())

    print("\n✅ Email sent successfully! Check your inbox.")
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication failed — App Password rejected by Gmail: {e}")
    print("   Fix: go to myaccount.google.com → Security → App passwords")
    print("   Delete the old one and create a new 'NDIS' app password.")
    print("   Then update SMTP_PASS in .env and restart the backend.")
except Exception as e:
    print(f"\n❌ Failed: {e}")
