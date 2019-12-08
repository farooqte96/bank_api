from flask import Flask, jsonify,  request
from flask_restful import Api, Resource
from pymongo import  MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")

db = client.BankDB # create a new database named BankDB
users = db["Users"] #Create a new collection called Users

#Some helper functions first
#0. Generate JSON Dictionary as response
def GenerateResponse(status, message):
    response_dict = {
    "status": status,
    "message": message
    }
    return response_dict
#1. Check if user exist
def UserExist(username):
    if users.find({"Username":username}).count() == 0:
        return False
    else:
        return True
#2.Verify user password

def VerifyPassword(username, password):
    if not UserExist(username):
        return False
    stored_password = users.find({"Username": username})[0]["Password"]
    if bcrypt.hashpw(password.encode('utf8'), stored_password) == stored_password:
        return True
    else:
        return False

# 3. Check user balance
def UserBalance(username):
    balance = users.find({
    "Username": username
    })[0]["Balance"]
    return balance

#4. Check user debt
def UserDebt(username):
    debt = users.find({
    "Username": username
    })[0]["Debt"]
    return debt

#5. Check user credentials will return Error dictionary, True/False
def VerifyCredentials(username, password):
    if not UserExist(username):
        return GenerateResponse(301, "Invalid username"), True

    if not VerifyPassword(username, password):
        return GenerateResponse(302, "Invalid Password"), True
    return None, False

#6. Update Balance
def UpdateBalance(username, amount):
    users.update({"Username": username},
    {
        "$set":{
             "Balance": amount

            }
    })

#7. Update Debt
def UpdateDebt(username, debt):
    users.update({"Username": username},
    {
        "$set":{
            "Debt": debt
        }
    })

#8. User balance already insufficient
def CheckBalanceZero(user_balance):
    if user_balance <= 0:
        status = 303
        message = "Not sufficient Funds available"
        return GenerateResponse(status, message), True
    else:
        return None,False
#Add our register class as Register resource

class Register(Resource):
    def post(self):
        #Step1: Get posted data
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]

        if UserExist(username):

            message =  "User with {} Already exists".format(username)
            status = 301
            response = GenerateResponse(status,message)
            return jsonify(response)
        else:
            #hash its password
            hashed_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
            users.insert({
                "Username": username,
                "Password": hashed_password,
                "Balance": 0,
                "Debt": 0
            })

            status = 200
            message = "User Registered Successfully"
            response = GenerateResponse(status, message)
            return jsonify(response)

#Create ADD class to add some amount in our account
class Add(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data["username"]
        password = posted_data["password"]
        amount = posted_data["amount"]

        #First verify user credentials...username and password
        response_dict, error = VerifyCredentials(username, password)
        if error:
            return jsonify(response_dict)
        #Now check if money is not negative
        if amount < 0:
            status = 304
            messgae = "Enter positive amount to add"
            response = GenerateResponse(status, message)
            return jsonify(response)

        user_balance = UserBalance(username) #query current balance of user
        service_charge = 1
        amount = amount - service_charge
        bank_balance = UserBalance("BANK")
        bank_balance += service_charge #Add service_charge which we get from user
        UpdateBalance("BANK", bank_balance) #Update balance of BANK account
        UpdateBalance(username, amount + user_balance)  #Update balance of username

        status = 200
        message = "Amount added Successfully"
        return jsonify(GenerateResponse(status, message))

#Create Transfer class
class Transfer(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]
        recipient = posted_data["recipient"]
        money = posted_data["amount"]

        response_dict, error = VerifyCredentials(username, password)
        if error:
            return jsonify(response_dict)
        if money < 0:
            status = 304
            messgae = "Enter positive amount to add"
            response = GenerateResponse(status, message)
            return jsonify(response)

        user_balance = UserBalance(username)
        if user_balance <= 0:
            status = 304
            message = "You are out of balance. Please add or take loan"
            response = GenerateResponse(status, message)
            return jsonify(response)

        bank_balance = UserBalance("BANK")
        recipient_balance = UserBalance(recipient)
        service_charge = 1
        bank_balance += service_charge
        user_balance -= service_charge + money
        recipient_balance += money

        if user_balance <= 0:
            status = 304
            message = "Not sufficient Funds available"
            response = GenerateResponse(status, message)
            return jsonify(response)

        if not UserExist(recipient):
            status = 301
            message = "Recipient doesn't exist"
            response = GenerateResponse(status, message)
            return jsonify(response)

        UpdateBalance("BANK", bank_balance)
        UpdateBalance(username, user_balance)
        UpdateBalance(recipient, recipient_balance)

        status = 200
        message = "Amount Transferred Successfully"
        response = GenerateResponse(status, message)
        return jsonify(response)

#How much balance does user have?
class Balance(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]

        response_dict, error = VerifyCredentials(username, password)
        if error:
            return jsonify(response_dict)

        response = users.find(
        {"Username": username},
        {
            "Password": 0,
            "_id": 0
        }
        )[0]

        return jsonify(response)

class PayLoan(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]
        amount = posted_data["amount"]

        response_dict, error =  VerifyCredentials(username, password)
        if error:
            return jsonify(response_dict)

        if amount <= 0:
            status = 304
            message = "Amount less than equal to 0 not allowed"
            response = GenerateResponse(status, message)
            return jsonify(response)
        #Get current Balance
        user_balance = UserBalance(username)
        response_dict, balance_zero = CheckBalanceZero(user_balance)
        if balance_zero:
            return jsonify(response_dict)

        if user_balance - amount <= 0:
            status = 303
            message = "Not sufficient Funds available"
            response = GenerateResponse(status, message)
            return jsonify(response)

        user_debt = UserDebt(username)
        #Get current debt
        #check if user not going to pay more than Debt
        if user_debt - amount < 0:
            status = 305
            message = "Dont pay more than your debt"
            response = GenerateResponse(status, message)
            return jsonify(response)

        bank_balance = UserBalance("BANK")
        bank_balance += amount
        user_balance -= amount
        user_debt -= amount
        UpdateDebt(username, user_debt)
        UpdateBalance(username, user_balance)
        UpdateBalance("BANK", bank_balance)

        status = 200
        message = "Loan Paid Successfully"
        response = GenerateResponse(status, message)

        return jsonify(response)
        #Check if amount not equals zero after paying loan

#Add class to take Loan
class TakeLoan(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]
        amount = posted_data["amount"]

        response_dict, error = VerifyCredentials(username, password)
        if error:
            return jsonify(response_dict)
        #Query current balance of user
        user_balance = UserBalance(username)
        user_debt = UserDebt(username)
        new_balance = user_balance + amount
        new_debt = user_debt + amount
        UpdateBalance(username, new_balance)
        UpdateDebt(username, new_debt)

        return jsonify(GenerateResponse(200, "Loan Taken Successfully"))







#Bind resources with api end points
api.add_resource(Register, "/register")
api.add_resource(Add, "/add")
api.add_resource(Transfer, "/transfer")
api.add_resource(Balance, "/balance")
api.add_resource(TakeLoan, "/takeloan")
api.add_resource(PayLoan, "/payloan")

if __name__ == "__main__":
    app.run(debug=True, host = '0.0.0.0')
