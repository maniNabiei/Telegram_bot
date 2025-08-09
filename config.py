import smtplib
import ssl
import random
from email.message import EmailMessage
from db import *

EMAIL_SENDER = 'maninabieidjango@gmail.com'
EMAIL_PASSWORD = 'zazuzxcummdwudhx'


def send_verification_email(to_email):
    code = str(random.randint(1000, 9999))
    msg = EmailMessage()
    msg['subject'] = 'فعال سازی حساب کاربری'
    msg['from'] = EMAIL_SENDER
    msg['to'] = to_email
    msg.set_content(f'کد تایید شما: {code}')
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)
    return code

