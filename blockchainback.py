from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import json
from web3 import Web3

app = Flask(__name__)
CORS(app)

# Connect to Ethereum (Use Infura or Ganache for local dev)
infura_url = "https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID"
w3 = Web3(Web3.HTTPProvider(infura_url))

# Dummy database (store in MongoDB/PostgreSQL later)
users = {
    "user1": {"finnocoins": 10000, "finnopoints": 0},
    "user2": {"finnocoins": 5000, "finnopoints": 0}
}
loans = []
blockchain = []

# 🔹 SHA-256 Hashing Function
def hash_transaction(transaction_data):
    transaction_string = json.dumps(transaction_data, sort_keys=True).encode()
    return hashlib.sha256(transaction_string).hexdigest()

# 🔹 Add to Blockchain (Python-based)
def add_to_blockchain(transaction):
    transaction_hash = hash_transaction(transaction)
    block = {
        "index": len(blockchain) + 1,
        "timestamp": time.time(),
        "transaction": transaction,
        "hash": transaction_hash
    }
    blockchain.append(block)

# ✅ Add Funds (with 2% fee)
@app.route("/add-funds", methods=["POST"])
def add_funds():
    data = request.json
    user = data.get("user")
    amount = int(data.get("amount"))
    if user not in users:
        return jsonify({"error": "User not found"}), 404

    fee = amount * 0.02  # 2% fee
    net_amount = amount - fee
    users[user]["finnocoins"] += net_amount
    return jsonify({"message": f"Added {net_amount} Finnocoins after fee deduction"})

# ✅ Withdraw Funds (with 2% fee)
@app.route("/withdraw-funds", methods=["POST"])
def withdraw_funds():
    data = request.json
    user = data.get("user")
    amount = int(data.get("amount"))
    if user not in users or users[user]["finnocoins"] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    fee = amount * 0.02  # 2% fee
    net_amount = amount - fee
    users[user]["finnocoins"] -= amount
    return jsonify({"message": f"Withdrawn {net_amount} Finnocoins after fee deduction"})

# ✅ Request a Loan
@app.route("/request-loan", methods=["POST"])
def request_loan():
    data = request.json
    borrower = data.get("borrower")
    amount = int(data.get("amount"))
    duration = int(data.get("duration"))  # in days
    if borrower not in users:
        return jsonify({"error": "User not found"}), 404

    loan = {
        "borrower": borrower,
        "amount": amount,
        "interest": amount * 0.035,  # 3.5% interest
        "due": time.time() + (duration * 86400),
        "funded": False,
        "lender": None
    }
    loans.append(loan)
    return jsonify({"message": "Loan request submitted", "loan": loan})

# ✅ Fund a Loan
@app.route("/fund-loan", methods=["POST"])
def fund_loan():
    data = request.json
    lender = data.get("lender")
    borrower = data.get("borrower")
    amount = int(data.get("amount"))

    for loan in loans:
        if loan["borrower"] == borrower and not loan["funded"] and loan["amount"] == amount:
            if users[lender]["finnocoins"] < amount:
                return jsonify({"error": "Insufficient funds"}), 400

            users[lender]["finnocoins"] -= amount
            users[borrower]["finnocoins"] += amount
            loan["funded"] = True
            loan["lender"] = lender
            add_to_blockchain(loan)
            return jsonify({"message": "Loan funded", "loan": loan})

    return jsonify({"error": "Loan not found or already funded"}), 400

# ✅ Repay Loan
@app.route("/repay-loan", methods=["POST"])
def repay_loan():
    data = request.json
    borrower = data.get("borrower")
    amount = int(data.get("amount"))

    for loan in loans:
        if loan["borrower"] == borrower and loan["funded"]:
            total_due = loan["amount"] * 1.035  # 3.5% interest
            installment_fee = total_due * 0.015  # 1.5% Finnovate fee
            final_payment = total_due + installment_fee

            if users[borrower]["finnocoins"] < final_payment:
                return jsonify({"error": "Insufficient funds to repay"}), 400

            users[borrower]["finnocoins"] -= final_payment
            users[loan["lender"]]["finnocoins"] += total_due
            users[loan["lender"]]["finnopoints"] += 5  # Reward lender
            loans.remove(loan)
            add_to_blockchain({"loan_repaid": loan})
            return jsonify({"message": "Loan repaid successfully"})

    return jsonify({"error": "No active loan found"}), 400

# ✅ View Blockchain Ledger
@app.route("/blockchain", methods=["GET"])
def view_blockchain():
    return jsonify(blockchain)

if __name__ == "__main__":
    
    app.run(debug=True)