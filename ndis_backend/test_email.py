"""
Quick test — run this in your ndis_backend folder to check if direct email delivery works.

    python test_email.py your-address@tempmail.plus

If it prints "SUCCESS" the OTP emails will reach temp-mail automatically.
If it prints "BLOCKED" your ISP blocks port 25 — use the amber dev banner on screen instead.
"""
import sys, socket, smtplib, dns.resolver
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def test(to_email: str):
    domain = to_email.split("@")[1]
    print(f"Looking up MX for {domain}...")
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = sorted(mx_records, key=lambda r: r.preference)[0].exchange.to_text().rstrip(".")
        print(f"Mail server: {mx_host}")
    except Exception as e:
        print(f"FAIL — DNS lookup error: {e}")
        return

    print(f"Testing port 25 to {mx_host}...")
    try:
        s = socket.create_connection((mx_host, 25), timeout=8)
        banner = s.recv(256).decode(errors="ignore").strip()
        s.close()
        print(f"Port 25 open — banner: {banner[:60]}")
    except Exception as e:
        print(f"BLOCKED — port 25 is closed/blocked: {e}")
        print("\nYour ISP blocks port 25. Use the amber dev-mode OTP banner on screen for testing.")
        return

    print("Sending test email...")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "NDIS Manager — Email Test"
        msg["From"]    = "NDIS Manager <noreply@ndis-manager.com.au>"
        msg["To"]      = to_email
        msg.attach(MIMEText(f"<p>Direct email delivery is working! Your OTPs will arrive here.</p>", "html"))

        with smtplib.SMTP(mx_host, 25, timeout=15) as server:
            server.ehlo("ndis-manager.com.au")
            server.sendmail("noreply@ndis-manager.com.au", [to_email], msg.as_string())

        print(f"\n✓ SUCCESS — check your inbox at {to_email}")
        print("OTP emails will now be delivered automatically to temp-mail during signup.")
    except Exception as e:
        print(f"\nFAIL — SMTP error: {e}")
        print("Use the amber dev-mode OTP banner on screen for testing.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_email.py your-address@tempmail.plus")
        sys.exit(1)
    test(sys.argv[1])
