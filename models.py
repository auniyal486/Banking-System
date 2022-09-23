from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    customer_id = db.Column(db.String(128), primary_key=True, nullable = False)
    full_name = db.Column(db.String(128),nullable = False)
    username =db.Column(db.String(64), unique=True, nullable = False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(264), nullable=False)
    phone_number = db.Column(db.String(128), nullable=False)
    dob = db.Column(db.String(64), nullable=False)
    address = db.Column(db.Text, nullable=False)
    def get_id(self):
        return (self.customer_id)

    def __repr__(self):
        return f"User('{self.customer_id}', '{self.username}')"

class Transaction(db.Model):
    transaction_id = db.Column(db.Integer, primary_key=True)
    account_no = db.Column(db.String(128), db.ForeignKey('account.account_no'), nullable=False)
    date = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    withdraw = db.Column(db.Boolean, default =False)
    deposited = db.Column(db.Boolean, default = False)
    def __repr__(self):
        return f"Post('{self.transaction_id}', '{self.account_no}')"

class AccountType(db.Model):
    type = db.Column(db.String(128),primary_key= True, nullable= False)
    minimum_amount = db.Column(db.Integer, default = 0)
    minimum_age = db.Column(db.Integer, default = 0)
    
class Account(db.Model):
    account_no = db.Column(db.String(128), primary_key=True, nullable=False)
    customer_id = db.Column(db.String(128), db.ForeignKey('user.customer_id'), nullable=False)
    account_type = db.Column(db.String(128), db.ForeignKey('account_type.type'), nullable=False)
    balance = db.Column(db.Integer, default =0)
    date = db.Column(db.String(128), nullable=False)
    def __repr__(self):
        return f"Post('{self.account_no}', '{self.customer_id}')"

class CardDetails(db.Model):
    account_no = db.Column(db.String(128), db.ForeignKey('account.account_no'), nullable=False)
    atm_card_no = db.Column(db.String(128), primary_key= True, nullable = False)
    cvv = db.Column(db.Integer, nullable= False)
    expiry_date = db.Column(db.String(128), nullable=False)

