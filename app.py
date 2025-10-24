from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

# ------------------ CONFIGURAÇÃO DO APP ------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-super-segura'

# Configuração do banco
base_dir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(base_dir, 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

db_path = os.path.join(instance_dir, 'finantrack.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ------------------ DICIONÁRIO DE BANCOS ------------------
BANK_ICONS = {
    'Itaú': 'itau.png',
    'Bradesco': 'bradesco.png',
    'Cresol': 'cresol.png',
    'Santander': 'santander.png',
    'Banco do Brasil': 'bb.png',
    'Picpay': 'picpay.png',
    'Inter': 'inter.png',
    'NuBank': 'nubank.png',
    'Caixa': 'caixa.png',
    'Sicoob': 'sicoob.png',
    'Sicredi': 'sicredi.png',
    'C6Bank': 'bank.png',
    'Mercado pago': 'pago.png',
    'PagBank': 'verde.png',
    'PayPal': 'Pal.png',
    'Outro': 'default.png'
}

# ------------------ MODELOS ------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    accounts = db.relationship('Account', backref='owner', lazy=True)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bank = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transactions = db.relationship('Transaction', backref='account', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # entrada, saida, transferencia
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    target_account_id = db.Column(db.Integer, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ ROTAS ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já em uso.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso! Faça login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    balances = {}
    for acc in accounts:
        saldo = 0
        for t in acc.transactions:
            if t.type == 'entrada':
                saldo += t.amount
            elif t.type == 'saida':
                saldo -= t.amount
            elif t.type == 'transferencia':
                if t.account_id == acc.id:
                    saldo -= t.amount
                elif t.target_account_id == acc.id:
                    saldo += t.amount
        balances[acc.id] = saldo
    return render_template('dashboard.html', accounts=accounts, balances=balances, bank_icons=BANK_ICONS)

@app.route('/conta/<int:account_id>')
@login_required
def conta(account_id):
    account = Account.query.get_or_404(account_id)
    if account.owner != current_user:
        flash('Acesso negado!')
        return redirect(url_for('dashboard'))

    saldo = 0
    for t in account.transactions:
        if t.type == 'entrada':
            saldo += t.amount
        elif t.type == 'saida':
            saldo -= t.amount
        elif t.type == 'transferencia':
            if t.account_id == account.id:
                saldo -= t.amount
            elif t.target_account_id == account.id:
                saldo += t.amount

    transactions = account.transactions
    return render_template('account_transactions.html', account=account, transactions=transactions, balance=saldo)

@app.route('/add_account', methods=['POST'])
@login_required
def add_account():
    name = request.form['name']
    bank = request.form.get('bank', 'Outro')
    if name:
        acc = Account(name=name, bank=bank, user_id=current_user.id)
        db.session.add(acc)
        db.session.commit()
        flash('Conta adicionada com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    account_id = int(request.form['account_id'])
    type_ = request.form['type']
    description = request.form['description']
    amount = float(request.form['amount'])
    target_account_id = request.form.get('target_account_id')
    target_account_id = int(target_account_id) if target_account_id else None
    category = request.form.get('category')

    transaction = Transaction(
        type=type_,
        description=description,
        amount=amount,
        account_id=account_id,
        target_account_id=target_account_id,
        category=category
    )
    db.session.add(transaction)
    db.session.commit()
    flash('Transação adicionada com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/delete_bank_account/<int:account_id>', methods=['POST'])
@login_required
def delete_bank_account(account_id):
    account = Account.query.get_or_404(account_id)
    if account.owner != current_user:
        flash('Acesso negado!')
        return redirect(url_for('dashboard'))

    Transaction.query.filter_by(account_id=account.id).delete()
    db.session.delete(account)
    db.session.commit()
    flash('Conta bancária e suas transações foram removidas com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/delete_all_accounts', methods=['POST'])
@login_required
def delete_all_accounts():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    for account in accounts:
        Transaction.query.filter_by(account_id=account.id).delete()
        db.session.delete(account)
    db.session.commit()
    flash('Todas as contas e transações foram removidas com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da conta.')
    return redirect(url_for('login'))

# ------------------ EXECUÇÃO ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Adiciona colunas extras se não existirem
        try:
            db.engine.execute('ALTER TABLE "transaction" ADD COLUMN category VARCHAR(50)')
        except Exception:
            pass
        try:
            db.engine.execute('ALTER TABLE "account" ADD COLUMN bank VARCHAR(50)')
        except Exception:
            pass
    app.run(debug=True)
