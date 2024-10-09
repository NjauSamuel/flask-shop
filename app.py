import secrets
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from models import Item, db, User
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# generate a secret key for JWT authentication
secret_key = secrets.token_hex(32)

# Configuring The Database:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kossa_shop.db'
app.config['JWT_SECRET_KEY'] = secret_key
db.init_app(app)

# Making The Database
with app.app_context():
    db.create_all()


# Fake User class
# class User:
#     def __init__(self, is_authenticated, name):
#         self.is_authenticated = is_authenticated
#         self.name = name

@app.route('/')
def landing_page():
    current_user = 1

    # Create a fake current_user object and set is_authenticated to True
    # current_user = User(is_authenticated=True, name='Samuel Njau')

    # Passing Items to my template.
    items = Item.query.all()


    return render_template("index.html", current_user=current_user, items=items)

@app.route('/home')
@jwt_required()
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET'])
def signup_page():
    return render_template('signup.html')


@app.route('/login', methods=['GET'])
def login_page():
    return render_template('signin.html')


# working on the sigup route for user registration
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return {"msg": "Username already exists."}, 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return {"msg": "User created successfully."}, 201


# working on the signin/login route for user authentication
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity={"username": username}, expires_delta=timedelta(hours=1))
        return {"access_token": access_token}, 200

    return {"msg": "Bad username or password."}, 401


@app.context_processor
def inject_now():
	""" sends datetime to all templates as 'now' """
	return {'now': datetime.utcnow()}



if __name__ == '__main__':
    app.run(debug=True, port=5001)
