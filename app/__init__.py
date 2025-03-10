import os, json
import requests
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from .forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from .db_models import db, User, Item
from itsdangerous import URLSafeTimedSerializer
from .funcs import mail, send_confirmation_email, fulfill_order
from dotenv import load_dotenv
from .admin.routes import admin
import hmac
import hashlib
import json
from flask import request, jsonify


load_dotenv()
app = Flask(__name__)
app.register_blueprint(admin)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DB_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_USERNAME'] = os.environ["EMAIL"]
app.config['MAIL_PASSWORD'] = os.environ["PASSWORD"]
app.config['MAIL_SERVER'] = "smtp.googlemail.com"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_PORT'] = 587
# stripe.api_key = os.environ["STRIPE_PRIVATE"]

Bootstrap(app)
db.init_app(app)
mail.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
	db.create_all()

@app.context_processor
def inject_now():
	""" sends datetime to templates as 'now' """
	return {'now': datetime.utcnow()}

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

@app.route("/")
def home():
	items = Item.query.all()
	return render_template("home.html", items=items)

@app.route("/login", methods=['POST', 'GET'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		email = form.email.data
		user = User.query.filter_by(email=email).first()
		if user == None:
			flash(f'User with email {email} doesn\'t exist!<br> <a href={url_for("register")}>Register now!</a>', 'error')
			return redirect(url_for('login'))
		elif check_password_hash(user.password, form.password.data):
			login_user(user)
			return redirect(url_for('home'))
		else:
			flash("Email and password incorrect!!", "error")
			return redirect(url_for('login'))
	return render_template("login.html", form=form)

@app.route("/register", methods=['POST', 'GET'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegisterForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			flash(f"User with email {user.email} already exists!!<br> <a href={url_for('login')}>Login now!</a>", "error")
			return redirect(url_for('register'))
		new_user = User(name=form.name.data,
						email=form.email.data,
						password=generate_password_hash(
									form.password.data,
									method='pbkdf2:sha256',
									salt_length=8),
						phone=form.phone.data)
		db.session.add(new_user)
		db.session.commit()
		# send_confirmation_email(new_user.email)
		flash('Thanks for registering! You may login now.', 'success')
		return redirect(url_for('login'))
	return render_template("register.html", form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
	try:
		confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
		email = confirm_serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
	except:
		flash('The confirmation link is invalid or has expired.', 'error')
		return redirect(url_for('login'))
	user = User.query.filter_by(email=email).first()
	if user.email_confirmed:
		flash(f'Account already confirmed. Please login.', 'success')
	else:
		user.email_confirmed = True
		db.session.add(user)
		db.session.commit()
		flash('Email address successfully confirmed!', 'success')
	return redirect(url_for('login'))

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route("/resend")
@login_required
def resend():
	send_confirmation_email(current_user.email)
	logout_user()
	flash('Confirmation email sent successfully.', 'success')
	return redirect(url_for('login'))

@app.route("/add/<id>", methods=['POST'])
def add_to_cart(id):
	if not current_user.is_authenticated:
		flash(f'You must login first!<br> <a href={url_for("login")}>Login now!</a>', 'error')
		return redirect(url_for('login'))

	item = Item.query.get(id)
	if request.method == "POST":
		quantity = request.form["quantity"]
		current_user.add_to_cart(id, quantity)
		flash(f'''{item.name} successfully added to the <a href=cart>cart</a>.<br> <a href={url_for("cart")}>view cart!</a>''','success')
		return redirect(url_for('home'))

@app.route("/cart")
@login_required
def cart():
	price = 0
	price_ids = []
	items = []
	quantity = []
	for cart in current_user.cart:
		items.append(cart.item)
		quantity.append(cart.quantity)
		price_id_dict = {
			"price": cart.item.price,
			"quantity": cart.quantity,
			}
		price_ids.append(price_id_dict)
		price += cart.item.price*cart.quantity
	return render_template('cart.html', items=items, price=price, price_ids=price_ids, quantity=quantity)

@app.route('/orders')
@login_required
def orders():
	return render_template('orders.html', orders=current_user.orders)

@app.route("/remove/<id>/<quantity>")
@login_required
def remove(id, quantity):
	current_user.remove_from_cart(id, quantity)
	return redirect(url_for('cart'))

@app.route('/item/<int:id>')
def item(id):
	item = Item.query.get(id)
	return render_template('item.html', item=item)

@app.route('/search')
def search():
	query = request.args['query']
	search = "%{}%".format(query)
	items = Item.query.filter(Item.name.like(search)).all()
	return render_template('home.html', items=items, search=True, query=query)


# Paystack API Key

# Fetch APP_ENV from the environment or default to 'production' if not set
APP_ENV = os.environ.get('APP_ENV', 'production').lower()

# Conditionally set the Paystack Secret Key
if APP_ENV == 'local':
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
else:
    PAYSTACK_SECRET_KEY = os.environ.get('LIVE_PAYSTACK_SECRET_KEY')

# Ensure the key is not None
if PAYSTACK_SECRET_KEY is None:
    raise ValueError("PAYSTACK_SECRET_KEY is not configured correctly for the current environment.")


@app.route('/payment_success')
def payment_success():
    return render_template('success.html')

@app.route('/payment_failure')
def payment_failure():
    return render_template('failure.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = json.loads(request.form['price_ids'].replace("'", '"'))
    
    # Debugging step: Print the structure of `data`
    print(data)
    
    # Prepare the Paystack payment link data
    price = sum(int(item['price']) * int(item['quantity']) for item in data)
    payload = {
		'client_reference_id': current_user.id,  # Pass the user's ID as client_reference_id For payment Confirmation
        'email': current_user.email,  # You may want to send the user's email
        'amount': price * 100,
        'callback_url': url_for('payment_success', _external=True),
        'cancel_url': url_for('payment_failure', _external=True),
        'webhook_url': url_for('paystack_webhook', _external=True),
    }
    
    # Create the payment link using Paystack API
    try:
        response = requests.post(
            'https://api.paystack.co/transaction/initialize',
            headers={'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'},
            data=payload
        )
        response_data = response.json()

        if response_data['status']:
            return redirect(response_data['data']['authorization_url'])
        else:
            return "Payment Initialization Failed", 400
    except Exception as e:
        return str(e), 500
	
@app.route('/paystack-webhook', methods=['POST'])
def paystack_webhook():
    if request.content_length > 1024 * 1024:
        print("Request too big!")
        abort(400)

    payload = request.get_data(as_text=True) # Getting The Payload from the request

    signature = request.headers.get('X-Paystack-Signature')

    # Paystack webhook secret key (must be set in Paystack dashboard)
    PAYSTACK_SECRET = PAYSTACK_SECRET_KEY

	# Compute the expected signature
    computed_signature = hmac.new(
        PAYSTACK_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
	
    print(computed_signature)

    # Compare the computed signature with the one from the headers (To verify source Authenticity)
    if computed_signature != signature:
        return "Invalid signature", 400

    event = json.loads(payload)

    if event['event'] == 'charge.success':
        # This means payment was successful
        transaction = event['data']['customer']['email']		
    
        # Fulfill the purchase here
        fulfill_order(transaction)

    return {}, 200
