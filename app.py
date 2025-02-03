from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate  # Import Flask-Migrate for database migrations
from database import db, Expense, User
from bank_api import BankAPI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key

db.init_app(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()  # Create database tables if they don't exist

bank = BankAPI()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Use session.get() for user loading

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Login failed. Check your username and/or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    data = request.json
    new_expense = Expense(desc=data['desc'], amount=data['amount'], category=data['category'], user_id=current_user.id)

    # Add expense only if amount is valid
    if new_expense.amount > 0:
        db.session.add(new_expense)
        db.session.commit()

    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    total_expenses = sum(exp.amount for exp in expenses)

    alert = total_expenses > 1000  # Budget limit

    return jsonify({'total': total_expenses, 'alert': alert,
                    'expenses': [{'category': exp.category, 'amount': exp.amount} for exp in expenses]})

@app.route('/save_money', methods=['POST'])
@login_required
def save_money():
    data = request.json
    amount_to_save = data['amount']

    # Check if amount is valid (minimum 10 rupees)
    if amount_to_save >= 10:
        current_user.saved_amount += amount_to_save
        db.session.commit()
        return jsonify({'success': True, 'saved_amount': current_user.saved_amount})

    return jsonify({'success': False, 'message': 'Minimum save amount is 10 rupees.'})

@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    data = request.json
    amount_to_withdraw = data['amount']

    # Check if withdrawal amount is valid (minimum 10 rupees)
    if amount_to_withdraw >= 10 and amount_to_withdraw <= current_user.saved_amount:
        current_user.saved_amount -= amount_to_withdraw
        db.session.commit()
        return jsonify({'success': True, 'balance': current_user.saved_amount})

    return jsonify({'success': False, 'message': 'Invalid withdrawal amount.'})

if __name__ == '__main__':
    app.run(debug=True)


