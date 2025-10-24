from app import db

class Conta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_banco = db.Column(db.String(100))
    saldo_inicial = db.Column(db.Float)

class Lancamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10))  # entrada ou saída
    valor = db.Column(db.Float)
    categoria = db.Column(db.String(50))
    descricao = db.Column(db.String(200))
    data = db.Column(db.String(20))
