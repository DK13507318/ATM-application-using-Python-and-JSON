from flask import Flask, render_template, request, redirect, session
import json, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "nexus_secure_key_123"

DB = "bank_data.json"

def load():
    if not os.path.exists(DB):
        with open(DB, "w") as f:
            json.dump({}, f)
    with open(DB, "r") as f:
        return json.load(f)

def save(data):
    with open(DB, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = load()
        acc = request.form.get("acc")
        pin = request.form.get("pin")
        if acc in data and check_password_hash(data[acc]["pin"], pin):
            session["user"] = acc
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = load()
        name = request.form.get("name")
        pin = generate_password_hash(request.form.get("pin"))
        acc = str(len(data) + 1001)
        data[acc] = {"name": name, "pin": pin, "balance": 0, "transactions": []}
        save(data)
        return f"Account Created! Your Account No: {acc}. <a href='/'>Login here</a>"
    return render_template("register.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    data = load()
    user = session["user"]
    u_data = data[user]

    if request.method == "POST":
        action = request.form.get("action")
        amt = float(request.form.get("amount") or 0)
        ts = datetime.now().strftime("%d %b, %H:%M")

        if action == "deposit" and amt > 0:
            u_data["balance"] += amt
            u_data["transactions"].append(f"{ts}|Deposit|{amt}")
        elif action == "withdraw" and 0 < amt <= u_data["balance"]:
            u_data["balance"] -= amt
            u_data["transactions"].append(f"{ts}|Withdraw|-{amt}")
        elif action == "transfer" and amt > 0:
            target = request.form.get("target")
            if target in data and target != user and amt <= u_data["balance"]:
                u_data["balance"] -= amt
                data[target]["balance"] += amt
                u_data["transactions"].append(f"{ts}|Transfer|-{amt}")
                data[target]["transactions"].append(f"{ts}|Received|{amt}")
        save(data)

    # Calculate Card Metrics
    t_dep = sum(float(t.split('|')[2]) for t in u_data["transactions"] if t.split('|')[1] in ['Deposit', 'Received'])
    t_wit = sum(abs(float(t.split('|')[2])) for t in u_data["transactions"] if t.split('|')[1] in ['Withdraw', 'Transfer'])
    t_tra = sum(abs(float(t.split('|')[2])) for t in u_data["transactions"] if t.split('|')[1] == 'Transfer')

    # Chart Data (Last 7)
    recent = u_data["transactions"][-7:]
    labels = [t.split('|')[1] for t in recent]
    values = [float(t.split('|')[2]) for t in recent]

    return render_template("dashboard.html", 
        name=u_data["name"], 
        balance=f"{u_data['balance']:,.2f}",
        total_deposit=f"{t_dep:,.2f}",
        total_withdraw=f"{t_wit:,.2f}",
        total_transfer=f"{t_tra:,.2f}",
        transactions=u_data["transactions"][::-1],
        labels=labels, values=values)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)