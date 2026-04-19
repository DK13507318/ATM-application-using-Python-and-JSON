from flask import Flask, render_template, request, redirect, session
import json, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

DB = "bank_data.json"

# ---------- LOAD DATA ----------
def load():
    if not os.path.exists(DB):
        with open(DB, "w") as f:
            json.dump({}, f)

    try:
        with open(DB, "r") as f:
            return json.load(f)
    except:
        return {}

# ---------- SAVE ----------
def save(data):
    with open(DB, "w") as f:
        json.dump(data, f, indent=4)


# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    data = load()

    if request.method == "POST":
        acc = request.form["acc"]
        pin = request.form["pin"]

        if acc in data and check_password_hash(data[acc]["pin"], pin):
            session["user"] = acc
            return redirect("/dashboard")

    return render_template("login.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    data = load()

    if request.method == "POST":
        name = request.form["name"]
        pin = generate_password_hash(request.form["pin"])
        acc = str(len(data) + 1001)

        data[acc] = {
            "name": name,
            "pin": pin,
            "balance": 0,
            "transactions": []
        }

        save(data)
        return f"Account Created! Your Account No: {acc}"

    return render_template("register.html")


# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    data = load()
    user = session["user"]

    if request.method == "POST":
        action = request.form["action"]
        amt = float(request.form.get("amount", 0))

        if action == "deposit":
            data[user]["balance"] += amt
            data[user]["transactions"].append(f"{datetime.now()}|Deposit|{amt}")

        elif action == "withdraw":
            if amt <= data[user]["balance"]:
                data[user]["balance"] -= amt
                data[user]["transactions"].append(f"{datetime.now()}|Withdraw|-{amt}")

        elif action == "transfer":
            target = request.form["target"]
            if target in data and amt <= data[user]["balance"]:
                data[user]["balance"] -= amt
                data[target]["balance"] += amt

                data[user]["transactions"].append(f"{datetime.now()}|Transfer|-{amt}")
                data[target]["transactions"].append(f"{datetime.now()}|Received|{amt}")

        save(data)

    # Chart data
    labels, values = [], []
    for t in data[user]["transactions"][-5:]:
        parts = t.split("|")
        labels.append(parts[1])
        values.append(float(parts[2]))

    return render_template(
        "dashboard.html",
        name=data[user]["name"],
        balance=data[user]["balance"],
        transactions=data[user]["transactions"][-5:],
        labels=labels,
        values=values
    )


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


app.run(debug=True)