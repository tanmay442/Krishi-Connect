import sqlite3
import uuid
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__, template_folder='../../Frontend')
app.secret_key = 'your-super-secret-key-for-secure-sessions'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth'

DATABASE = 'Backend/app/database.db'
SAMPLE_API_KEY = "579b464db66ec23bdd0000016a01febea78d49c05964acd03b47d136"

# --------------------- DATABASE ---------------------
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

# --------------------- USER MODEL ---------------------
class User(UserMixin):
    def __init__(self, public_id, name, email, tag):
        self.id = public_id
        self.name = name
        self.email = email
        self.tag = tag

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user_data = db.execute(
        'SELECT public_id, name, email, tag FROM users WHERE public_id = ?', (user_id,)
    ).fetchone()
    if user_data:
        return User(
            public_id=user_data['public_id'],
            name=user_data['name'],
            email=user_data['email'],
            tag=user_data['tag']
        )
    return None

# --------------------- API FETCH FUNCTION ---------------------
def get_market_data(api_key: str,
                    output_format: str = 'json',
                    limit: int = 200,
                    state: str = None,
                    district: str = None,
                    market: str = None,
                    commodity: str = None):
    """Fetches data from the Government of India Daily Market Price API."""
    base_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        'api-key': api_key,
        'format': output_format,
        'limit': limit
    }

    # Add optional filters
    if state:
        params['filters[state.keyword]'] = state
    if district:
        params['filters[district]'] = district
    if market:
        params['filters[market]'] = market
    if commodity:
        params['filters[commodity]'] = commodity

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()  # Return parsed JSON
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Market data fetch failed: {e}")
        return {"error": f"Failed to fetch data: {e}"}

# --------------------- ROUTES ---------------------

@app.route('/')
@login_required
def index():
    return render_template('welcome.html')

# 🧭 MARKET DATA PAGE (with clean parsed data)
@app.route('/market_data', methods=['GET'])
@login_required
def market_data():
    # Collect user form inputs (from GET params)
    form_params = {
        'state': request.args.get('state', ''),
        'district': request.args.get('district', ''),
        'market': request.args.get('market', ''),
        'commodity': request.args.get('commodity', '')
    }

    data = []
    # Fetch only if user clicked "Fetch Live Prices"
    if 'search' in request.args:
        api_response = get_market_data(
            api_key=SAMPLE_API_KEY,
            output_format='json',
            limit=200,
            state=form_params['state'] or None,
            district=form_params['district'] or None,
            market=form_params['market'] or None,
            commodity=form_params['commodity'] or None
        )

        # If valid JSON, extract "records"
        if isinstance(api_response, dict) and 'records' in api_response:
            data = api_response['records']
        else:
            data = []

    return render_template('market_data.html', form=form_params, data=data)

# --------------------- AUTH & USER MGMT ---------------------
@app.route('/auth')
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('onboarding.html')

@app.route('/register', methods=['POST'])
def register():
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
        db.execute(
            'INSERT INTO users (public_id, name, email, password, contact_number, tag, state) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (new_public_id, name, email, hashed_password, contact_number, tag, state)
        )
        db.commit()
        user = load_user(new_public_id)
        if user:
            login_user(user)
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
        user = User(
            public_id=user_data['public_id'],
            name=user_data['name'],
            email=user_data['email'],
            tag=user_data['tag']
        )
        login_user(user)
        return redirect(url_for('index'))
    else:
        flash("Invalid email or password.")
        return redirect(url_for('auth'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth'))

# --------------------- MAIN ---------------------
if __name__ == '__main__':
    app.run(debug=True)
