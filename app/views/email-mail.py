import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email='reach@aimedscan.com',
    to_emails='riyagupta@tristonsoft.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
try:
    sg = SendGridAPIClient('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')
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)