from flask import Flask, render_template, redirect, url_for, flash, request, abort
from models import Item, db
from datetime import datetime
import os
from dotenv import load_dotenv
# The Class for implementing Logging in flask. 
from flask_login import login_user, current_user, login_required, logout_user
# Importing WTF forms for Registration and Login
from authForms import LoginForm, RegisterForm

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user

# Importing Flask Bootstrap
from flask_bootstrap import Bootstrap


app = Flask(__name__)

# Configuring The Database:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kossa_shop.db'
db.init_app(app)

#Other configurations:
load_dotenv()
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
Bootstrap(app)


# Other initializations including loging in:
login_manager = LoginManager()
login_manager.init_app(app)

# Making The Database 
with app.app_context():
    db.create_all()


# Fake User class
class User:
    def __init__(self, is_authenticated, name):
        self.is_authenticated = is_authenticated
        self.name = name

@app.route('/')
def home():
    current_user = 1

    # Create a fake current_user object and set is_authenticated to True
    current_user = User(is_authenticated=True, name='Samuel Njau')

    # Passing Items to my template. 
    items = Item.query.all()


    return render_template("index.html", current_user=current_user, items=items)

# The Registration Route:
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

# The User Loader for Login management:
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

# The Login Route:
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


# The function below provides the current date and time to all the views. 
@app.context_processor
def inject_now():
	""" sends datetime to all templates as 'now' """
	return {'now': datetime.utcnow()}




if __name__ == '__main__':
    app.run(debug=True, port=5050)
