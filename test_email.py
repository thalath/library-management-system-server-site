import smtplib
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

email = os.getenv("MAIL_USERNAME")
password = os.getenv("MAIL_PASSWORD")

try:
    context = ssl.create_default_context()

    with smtplib.SMTP(
        "smtp.gmail.com", 587, timeout=30
    ) as server:

        server.set_debuglevel(1)

        server.ehlo()
        server.starttls(context=context)
        server.ehlo()

        server.login(email, password)

        print("SMTP authentication successful!")

except Exception as e:
    print("SMTP Error:", e)