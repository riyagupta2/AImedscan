from flask import (Blueprint, render_template, redirect, request, url_for,
                   abort, flash,jsonify )
from flask.ext.login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from app import app, models, db
from app.forms import user as user_forms
from app.toolbox import email
# Setup Stripe integration
import stripe
import json
from json import dumps

from paypal import PayPalConfig
from paypal import PayPalInterface
#import paypalrestsdk
import smtplib
from smtplib import SMTPException
from app import app, mail

from flask_mail import Message

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# stripe_keys = {
# 	'secret_key': "sk_test_zJuSsNUL5yB4Vy0irwY0urHe",
# 	'publishable_key': "pk_test_9h0f2uum2Ym96ZlIky9Cbuwh"
# }

# stripe.api_key = stripe_keys['secret_key']


config = PayPalConfig(API_USERNAME = "malleswar_api1.praise-tech.com",
                      API_PASSWORD = "R3RV7QDC78BY4XVC",
                      API_SIGNATURE = "ARfxBoFTKjG9iqDKA3aAlDEk9ElWADpqZqgjMJcJ17PUADfIUh1kgrXp",
                      DEBUG_LEVEL=0,
                      API_ENVIRONMENT = "PRODUCTION")

# paypalrestsdk.configure({
#   "mode": "live", # sandbox or live
#   "client_id": "AUtXI41eXk-7O6Eiam6s3p0wb08bd6nra4oOiRFPxFpFgJ_xgzqOtZ8gCZgvNPU_0icbcXfGw_mXC7W9",
#   "client_secret": "EOILOIjnfXX63VqwMMOYX1_sfyiS-RikxfNkoQa6fqOQaT4CzrNp-DSc_dYJhb2RjqJUEqiWVyxOAOSu" })

interface = PayPalInterface(config=config)


# Serializer for generating random tokens
ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Create a user blueprint
userbp = Blueprint('userbp', __name__, url_prefix='/user')


@userbp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = user_forms.SignUp()
    if form.validate_on_submit():
        # Create a user who hasn't validated his email address
        user = models.User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            email=form.email.data,
            confirmation=False,
            password=form.password.data,
        )
        # Insert the user in the database
        db.session.add(user)
        db.session.commit()
        # Subject of the confirmation email
        subject = 'Please confirm your email address.'
        # Generate a random token
        token = ts.dumps(user.email, salt='email-confirm-key')
        # Build a confirm link with token
        confirmUrl = url_for('userbp.confirm', token=token, _external=True)
        # Render an HTML template to send by email
        html = render_template('email/confirm.html',
                               confirm_url=confirmUrl)
        message = Mail(
            from_email='reach@aimedscan.com',
            to_emails='riyagupta@tristonsoft.com',
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
        # Send the email to user
        try:
            email.send(user.email, subject, html)
            print("email sent")
        except SMTPException as e:
            print("can not send email")

        # Send back to the home page
        flash('Check your emails to confirm your email address.', 'positive')
        return redirect(url_for('userbp.signin'))
    return render_template('user/signup2.html', form=form, title='Sign up')


@userbp.route('/confirm/<token>', methods=['GET', 'POST'])
def confirm(token):
    try:
        email = ts.loads(token, salt='email-confirm-key', max_age=86400)
    # The token can either expire or be invalid
    except:
        abort(404)
    # Get the user from the database
    user = models.User.query.filter_by(email=email).first()
    # The user has confirmed his or her email address
    user.confirmation = True
    # Update the database with the user
    db.session.commit()
    # Send to the signin page
    flash(
        'Your email address has been confirmed, you can sign in.', 'positive')
    return redirect(url_for('userbp.signin'))


@userbp.route('/signin', methods=['GET', 'POST'])
def signin():
    form = user_forms.Login()
    error = None
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        # Check the user exists
        if user is not None:
            # Check the password is correct
            if user.check_password(form.password.data):
                login_user(user)
                # Send back to the home page
                flash('Succesfully signed in.', 'positive')
                return redirect(url_for('index'))
            else:
                #error = 'The password you have entered is wrong.'
                flash('The password you have entered is wrong.', 'negative')
                return redirect(url_for('userbp.signin'))
        else:
            #error = 'Unknown email address.' 
            flash('Unknown email address.', 'negative')
            return redirect(url_for('userbp.signin'))
    return render_template('user/signin2.html', form=form, title='Sign in')


@userbp.route('/signout')
def signout():
    logout_user()
    flash('Succesfully signed out.', 'positive')
    return redirect(url_for('index'))


@userbp.route('/account')
@login_required
def account():
    return render_template('user/account.html', title='Account')


@userbp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    form = user_forms.Forgot()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        # Check the user exists
        if user is not None:
            # Subject of the confirmation email
            subject = 'Reset your password.'
            # Generate a random token
            token = ts.dumps(user.email, salt='password-reset-key')
            # Build a reset link with token
            resetUrl = url_for('userbp.reset', token=token, _external=True)
            # Render an HTML template to send by email
            html = render_template('email/reset.html', reset_url=resetUrl)
            # Send the email to user
            email.send(user.email, subject, html)
            # Send back to the home page
            flash('Check your emails to reset your password.', 'positive')
            return redirect(url_for('index'))
        else:
            flash('Unknown email address.', 'negative')
            return redirect(url_for('userbp.forgot'))
    return render_template('user/forgot.html', form=form)


@userbp.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    try:
        email = ts.loads(token, salt='password-reset-key', max_age=86400)
    # The token can either expire or be invalid
    except:
        abort(404)
    form = user_forms.Reset()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=email).first()
        # Check the user exists
        if user is not None:
            user.password = form.password.data
            # Update the database with the user
            db.session.commit()
            # Send to the signin page
            flash('Your password has been reset, you can sign in.', 'positive')
            return redirect(url_for('userbp.signin'))
        else:
            flash('Unknown email address.', 'negative')
            return redirect(url_for('userbp.forgot'))
    return render_template('user/reset.html', form=form, token=token)

@app.route('/user/pay')
@login_required
def pay():
    user = models.User.query.filter_by(email=current_user.email).first()
    if user.paid == 0:
    	return render_template('user/buy.html', key=stripe_keys['publishable_key'], email=current_user.email)
    return "You already paid."

@app.route('/user/charge',methods=['GET', 'POST'])
@login_required
def charge():
    # Amount in cents
    amount = 1000
    customer = stripe.Customer.create(email=current_user.email, source=request.form['stripeToken'])
    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description='Service Plan'
    )
    user = models.User.query.filter_by(email=current_user.email).first()
    user.paid = 1
    db.session.commit()
    
    # do anything else, like execute shell command to enable user's service on your app
    return render_template('index2.html')

@app.route('/api/payFail', methods=['POST', 'GET'])
def payFail():
	content = request.json
	stripe_email = content['data']['object']['email']
	user = models.User.query.filter_by(email=stripe_email).first()
	if user is not None: 
		user.paid = 0
		db.session.commit()
		# do anything else, like execute shell command to disable user's service on your app
	return "Response: User with associated email " + str(stripe_email) + " updated on our end (payment failure)."

@app.route('/api/paySuccess', methods=['POST', 'GET'])
def paySuccess():
	content = request.json
	stripe_email = content['data']['object']['email']
	user = models.User.query.filter_by(email=stripe_email).first()
	if user is not None: 
		user.paid = 1
		db.session.commit()
		# do anything else on payment success, maybe send a thank you email or update more db fields?
	return "Response: User with associated email " + str(stripe_email) + " updated on our end (paid)."

@app.route("/paypal/redirect")
def paypal_redirect():
    kw = {
        'amt': '10.00',
        'currencycode': 'USD',
        'returnurl': url_for('paypal_confirm', _external=True),
        'cancelurl': url_for('paypal_cancel', _external=True),
        'paymentaction': 'Sale'
    }

    setexp_response = interface.set_express_checkout(**kw)
    return redirect(interface.generate_express_checkout_redirect_url(setexp_response.token))     

@app.route("/paypal/confirm")
def paypal_confirm():
    getexp_response = interface.get_express_checkout_details(token=request.args.get('token', ''))

    if getexp_response['ACK'] == 'Success':
        user = models.User.query.filter_by(email=current_user.email).first()
        user.paid = 1
        db.session.commit()
        return """
            Everything looks good! <br />
            <a href="%s">Click here to complete the payment.</a>
        """ % url_for('paypal_do', token=getexp_response['TOKEN'])
    else:
        return """
            Oh noes! PayPal returned an error code. <br />
            <pre>
                %s
            </pre>
            Click <a href="%s">here</a> to try again.
        """ % (getexp_response['ACK'], url_for('index'))


@app.route("/paypal/do/<string:token>")
def paypal_do(token):
    getexp_response = interface.get_express_checkout_details(token=token)
    kw = {
        'amt': getexp_response['AMT'],
        'paymentaction': 'Sale',
        'payerid': getexp_response['PAYERID'],
        'token': token,
        'currencycode': getexp_response['CURRENCYCODE']
    }
    interface.do_express_checkout_payment(**kw)   

    return redirect(url_for('paypal_status', token=kw['token']))

@app.route("/paypal/status/<string:token>")
def paypal_status(token):
    checkout_response = interface.get_express_checkout_details(token=token)

    if checkout_response['CHECKOUTSTATUS'] == 'PaymentActionCompleted':
        # Here you would update a database record.
        return """
            Awesome! Thank you for your %s %s purchase.
        """ % (checkout_response['AMT'], checkout_response['CURRENCYCODE'])
    else:
        return """
            Oh no! PayPal doesn't acknowledge the transaction. Here's the status:
            <pre>
                %s
            </pre>
        """ % checkout_response['CHECKOUTSTATUS']

@app.route("/paypal/cancel")
def paypal_cancel():
    return redirect(url_for('index'))


@app.route('/payment', methods=['POST'])
def payment():

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "/payment/execute",
            "cancel_url": "/"},
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "testitem",
                    "sku": "12345",
                    "price": "500.00",
                    "currency": "USD",
                    "quantity": 1}]},
            "amount": {
                "total": "500.00",
                "currency": "USD"},
            "description": "This is the payment transaction description."}]})

    if payment.create():
        print('Payment success!')
    else:
        print(payment.error)

    return jsonify({'paymentID' : payment.id})

@app.route('/execute', methods=['POST'])
def execute():
    success = False

    payment = paypalrestsdk.Payment.find(request.form['paymentID'])

    if payment.execute({'payer_id' : request.form['payerID']}):
        print('Execute success!')
        success = True
    else:
        print(payment.error)

    return jsonify({'success' : success})