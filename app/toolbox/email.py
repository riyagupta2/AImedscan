from threading import Thread
from flask.ext.mail import Message
from app import app, mail
import smtplib

#from email.mime.text import MIMEText
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import render_template
def send(recipient, subject, body):
    '''
    Send a mail to a recipient. The body is usually a rendered HTML template.
    The sender's credentials has been configured in the config.py file.
    '''
    #sender = app.config['ADMINS'][0]
    #message = Message(subject, sender=sender, recipients=[recipient])
    #message.body = body
    message = Mail(
            from_email=app.config['ADMINS'][0],
            to_emails=[recipient],
            subject='Sending with Twilio SendGrid is Fun',
            html_content=render_template('email/confirm.html',
                               confirm_url=confirmUrl))
    try:
        sg = SendGridAPIClient('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')
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
    # Create a new thread
    thr = Thread(target=send_async, args=[app, message])
    thr.start()


def send_async(app, message):
    ''' Send the mail asynchronously. '''
    with app.app_context():
        mail.send(message)