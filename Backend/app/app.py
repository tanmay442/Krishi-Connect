# Backend/app/app.py

import sqlite3
import uuid  # Import the UUID library
from flask import Flask, render_template, request, redirect, url_for, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__, template_folder='../../Frontend')
app.secret_key = 'your-super-secret-key-for-secure-sessions'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth'

DATABASE = 'Backend/app/database.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# --- User Model Updated for Public ID ---
class User(UserMixin):
    def __init__(self, public_id, name, email, tag):
        self.id = public_id  # Flask-Login's get_id() will now return the public_id
        self.name = name
        self.email = email
        self.tag = tag


# --- User Loader Updated to Use Public ID ---
# The user_id passed here is the secure public_id from the session cookie
@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    # Query using the secure public_id, not the internal integer id
    user_data = db.execute('SELECT public_id, name, email, tag FROM users WHERE public_id = ?', (user_id,)).fetchone()
    if user_data:
        return User(public_id=user_data['public_id'], name=user_data['name'], email=user_data['email'], tag=user_data['tag'])
    return None


# --- Routes ---

@app.route('/')
@login_required
def index():
    # The user's unique (and secure) ID is now current_user.id
    return render_template('welcome.html')

@app.route('/auth')
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('onboarding.html')


@app.route('/register', methods=['POST'])
def register():
    # --- Generate a new secure public_id for the user ---
    new_public_id = str(uuid.uuid4())

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    contact_number = request.form['contact_number']
    tag = request.form['tag']
    state = request.form['state']

    hashed_password = generate_password_hash(password)
    db = get_db()

    try:
        # Insert the new public_id along with other user data
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO users (public_id, name, email, password, contact_number, tag, state) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (new_public_id, name, email, hashed_password, contact_number, tag, state)
        )
        db.commit()

        # Log the new user in using their secure public_id
        user = load_user(new_public_id)
        if user:
            login_user(user) # This securely stores the public_id in the session
        
        return redirect(url_for('index'))

    except sqlite3.IntegrityError:
        flash("This email address is already registered. Please sign in.")
        return redirect(url_for('auth'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    db = get_db()
    
    user_data = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if user_data and check_password_hash(user_data['password'], password):
        # Create a User object with the public_id
        user = User(public_id=user_data['public_id'], name=user_data['name'], email=user_data['email'], tag=user_data['tag'])
        login_user(user) # Securely logs the user in
        return redirect(url_for('index'))
    else:
        flash("Invalid email or password.")
        return redirect(url_for('auth'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth'))

if __name__ == '__main__':
    app.run(debug=True)