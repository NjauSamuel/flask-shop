from flask import Flask, render_template, redirect, url_for, flash, request, abort
from models import Item, db
from datetime import datetime

app = Flask(__name__)

# Configuring The Database:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kossa_shop.db'
db.init_app(app)

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




@app.context_processor
def inject_now():
	""" sends datetime to all templates as 'now' """
	return {'now': datetime.utcnow()}



if __name__ == '__main__':
    app.run(debug=True, port=5001)
