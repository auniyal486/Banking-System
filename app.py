from flask import  request, Flask, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
import os
import datetime
from flask_sqlalchemy import SQLAlchemy
import os
from flask_bcrypt import Bcrypt
from datetime import date
from marshmallow import Schema, fields, ValidationError, validates,validate
import random

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]=os.environ.get("sql_url")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
app.secret_key = os.urandom(32)
login_manager = LoginManager(app)


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

from models import *

db.drop_all()
db.create_all()

@login_manager.user_loader
def load_user(customer_id):  
    return User.query.get(int(customer_id))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True,validate = validate.Length(max=64))

class SignupSchema(LoginSchema):
    username = fields.Str(required=True,validate = validate.Length(max=64))
    full_name = fields.Str(required=True,validate = validate.Length(max=256))
    phone_number = fields.Str(required=True,validate = validate.Length(max=128))
    dob = fields.Str(required=True,validate = validate.Length(max=64))
    address = fields.Str(required=True,validate = validate.Length(max=1000))
    @validates('dob')
    def dob_is_not_valid(schema, dob):
        try:
            datetime.datetime.strptime(dob, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")

charlist=[1]
for i in range(1,26):
    charlist.append(charlist[i-1]*2+(i+1))
 
def calculateAge(birthDate):
    today = date.today()
    age = today.year - birthDate.year -((today.month, today.day) <(birthDate.month, birthDate.day))
    return age

def generate_customer_id(val):
    val = val.upper()
    customer_id =''
    for i in range(len(val)):
        customer_id += str(charlist[val[i]-'A'])
    return customer_id

def generate_account_no():
    last_account_no = db.session.query(Account).order_by(Account.account_no.desc()).first()
    if last_account_no:
        return last_account_no+1
    return 10000000000

def generate_card_no():
    last_card_no = db.session.query(CardDetails).order_by(CardDetails.atm_card_no.desc()).first()
    if last_card_no:
        return last_card_no+1
    return 1000000000000000

@app.route('/',methods=['GET'])
def index():
    return jsonify(['Banking System Project'])

@app.route('/login',methods=['GET'])
def login():
    if current_user.is_authenticated:
        return jsonify("you're already logged in!")
    data = request.get_json()
    try:
        schema = LoginSchema()
        schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password,data['password']):
        login_user(user)
        return jsonify("you have successfully logged in.")
    else:
        return jsonify('email or password is incorrect') , 422

@app.route('/signup',methods=['POST'])
def signup():
    if current_user.is_authenticated:
        return jsonify("you're already logged in!")
    user_data = request.get_json()
    try:
        schema = SignupSchema()
        schema.load(user_data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    user = User.query.filter_by(email=user_data['email']).first()
    if user:
        return jsonify('That email is taken. Please choose a different one.') , 422

    hashed_password = bcrypt.generate_password_hash(user_data['password']).decode('utf-8')
    user = User(customer_id = generate_customer_id(user_data['username']), full_name=user_data['full_name'],\
        username= user_data['username'],email=user_data['email'], password=hashed_password, \
        phone_number= user_data['phone_number'],dob= user_data['dob'], address = user_data['address'] )
    
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify("you have successfully registered and logged in.")

@login_required
@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify("you have successfully logged out")

@login_required
@app.route('/open-account',methods=['GET'])
def open_account():
    data = request.headers
    account_type =data.get('account_type',None, str),
    amount = data.get('amount',None, int)
    if account_type and amount:
        account_type_obj = AccountType.query.filter_by(type=account_type.title()).first()
        year = calculateAge(datetime.datetime.strftime(current_user.dob,'%Y-%m-%d'))
        if account_type_obj and account_type_obj.minimum_amount >=amount and year > account_type_obj.minimum_age:
            account_no = generate_account_no()
            account = Account(balance=amount, account_no= account_no,\
                account_type=type, customer_id=current_user.customer_id, date = datetime.datetime.now.strftime('%Y-%m-%d'))
            db.session.add(account)
            expiry_date = datetime.date.today()
            expiry_date.year = datetime.date.today().year+10
            card = CardDetails(account_no=account.account_no,atm_card_no=generate_card_no(),cvv=random.randint(100,999),expiry_date=expiry_date.strftime('%Y-%m-%d'))
            db.session.add(card)
            db.session.commit()
            return jsonify("account created successfully")
        return jsonify("amount is very low or you're not eligible") , 422
    return jsonify('please provide correct information'), 400

@login_required
@app.route('/deposit-money')
def deposit_money():
    data = request.headers
    account_no = data.get('account_no',None,int)
    money = data('money',None, int)
    if money and account_no:
        account = Account.query.filter_by(account_no=account_no).first()
        if account :
            if account.account_type=='Current':
                account.balance += money -min(500,float(0.5/100)*money)
            else:
                account.balance +=money
            db.session.commit()
            return jsonify('money deposited')
    return jsonify('invaild details')


@login_required
@app.route('/transfer-money')
def transfer_money():
    data = request.headers
    current_account_no = data.get('current_account_no',None,int)
    transfer_account_no = data('transfer_account_no',None,int)
    if transfer_account == current_account_no:
        return jsonify('provide other transfer account')
    money = data.get('money',None,int)
    current_account = Account.query.filter_by(account_no=current_account_no).first()
    transfer_account = Account.query.filter_by(account_no=transfer_account_no).first()
    if current_account and transfer_account and current_account.type == 'Current'  :
        total_value = min(500,float(0.5/100)*money)+money
        if current_account.balance >= total_value:
            current_account.balance  -= total_value
            transfer_account.balance += money
            db.session.commit()
            return jsonify('money deposited')
        return jsonify('unable to processed due to low bank balance'), 422
    return jsonify('invaild details'), 400

@login_required
@app.route('/account-details')
def account_details():
    accounts = Account.query.filter_by(customer_id= current_user.customer_id).first()
    if accounts:
        result =[]
        for account in accounts:
            item = {}
            item['Account Number'] = account.account_no
            item['Current Balance'] = account.balance
            item['Account Opening Date'] = account.date
            result.append(item)
        return jsonify(result)
    return jsonify('invaild details')

@login_required
@app.route('/get-passbook')
def get_passbook():
    data = request.headers
    account_no = data['account_no']
    transactions = Transaction.query.filter_by(account_no=account_no).all()
    if transactions :
        result = []
        for transaction in transactions:
            item = {}
            item['date'] = transaction.date
            item['amount'] = transaction.amount
            if transaction.withdraw:
                item['transaction type'] = 'Withdraw'
            else:
                item['transaction type'] = 'Deposite'
            result.append(item)
        return jsonify(result)
    return jsonify('invaild details')

#need a lot improvement.
@login_required
@app.route('/withdraw-by-atm')
def withdraw_by_atm():
    data = request.headers
    card_no = data.get('card_no',None)
    expiry_date = data.get('expiry_date',None)
    cvv = data.get('cvv',None)
    amount = data.get('amount', None)
    if card_no and expiry_date and cvv and amount :
        card = CardDetails.query.filter_by(atm_card_no=card_no).first()
        if card and card.cvv == cvv and expiry_date == card.expiry_date:
            account = Account.query.filter_by(account_no=card.account_no).first()
            if account.account_type=='Current':
                total_value= min(500,float(0.5/100)*amount)+amount
                if account.balance >=total_value:
                    account.balance -= total_value
                    db.session.commit()
                    return jsonify('money withdrawed')
            elif account.account_type== 'Saving':
                # transactions = Transaction.query.filter_by(account_no=account.account_no,\
                # withdraw=True).order_by(Transaction.transaction_id.desc()).all()
                # count =0
                # total_amount=0
                
                # for transaction in transactions:
                if account.balance >=amount:
                    account.balance -= amount
                    db.session.commit()
                    return jsonify('money withdrawed')
            return jsonify('unable to processed due to low bank balance'), 422
    return jsonify('wrong information') , 400

@login_required
@app.route('/withdraw-by-direct-transaction')
def withdraw_by_direct_transaction():
    data = request.headers
    account_no = data.get('account_no',None,int)
    amount = data.get('amount', None,int)
    if account_no and amount :
        account = Account.query.filter_by(account_no=account_no).first()
        if account:
            if account.account_type=='Current':
                total_value= min(500,float(0.5/100)*amount)+amount
                if account.balance >=total_value:
                    account.balance -= total_value
                    db.session.commit()
                    return jsonify('money withdrawed')
            elif account.account_type== 'Saving':
                # transactions = Transaction.query.filter_by(account_no=account.account_no,\
                # withdraw=True).order_by(Transaction.transaction_id.desc()).all()
                # count =0
                # total_amount=0
                
                # for transaction in transactions:
                if account.balance >=amount:
                    account.balance -= amount
                    db.session.commit()
                    return jsonify('money withdrawed')
            return jsonify('unable to processed due to low bank balance'), 422
    return jsonify('wrong information'), 400

if __name__=="__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port)