import smtplib, ssl
from email.message import EmailMessage

def send_mail(to_address, subject, text):
    msg = EmailMessage()
    msg.set_content(text)

    msg['Subject'] = subject
    msg['From'] = "streamlitmailsender@gmail.com"
    msg['To'] = to_address

    # Send the message via our own SMTP server.
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login("streamlitmailsender@gmail.com", "sEzju1-zoqcex-wuzjyj")
    server.send_message(msg)
    server.quit()
