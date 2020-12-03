import os
import re

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, get_portfolio, get_history

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# check all necessary tables exist, create if not
db.execute(
    '''CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    user_id INT NOT NULL,
    symbol CHAR(10) NOT NULL,
    name TEXT NOT NULL,
    number NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    amount NUMERIC NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type CHAR(4) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id))'''
    )

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # request necessary data
    data = get_portfolio("symbol", "asc")

    return render_template("index.html", rows = data[1], totals = data[0])


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # return base buy page if no url variiables
    if not request.args and request.method == "GET":
        return render_template("buy.html")

    # get user id
    user_id = session.get("user_id")

    # request stock ticker symbol from URL
    symbol = request.args.get("symbol", '')
    shares = request.args.get("shares", '')

    # set shares if no number is provided
    if not shares:
        shares = 0

    # check 'shares' is positive number
    if int(shares) < 0:
        return apology("Please enter positive number of shares to buy", 403)

    # get cash available
    fund = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = user_id)
    funds = float(fund[0]["cash"])

    # no stock ticker symbol was provided through GET method
    if not symbol:

        # User reached route via POST (as by submitting a form via POST)
        if request.method == "POST":

            symbol = request.form.get("symbol")
            name = request.form.get("name")
            shares = int(request.form.get("shares"))
            price = float(request.form.get("price"))

            # load apology if symbol is not provided
            if not symbol:
                return apology("please enter stock ticker symbol", 403)

             # load apology if number is not provided
            if not shares or shares <= 0:
                return apology("Please enter positive number of shares to buy", 403)

            # check funds available
            if funds < price * shares:
                return apology("Sorry, not enough funds for this transaction", 403)

            # prepare data to be inserted into db
            amount = round(shares * price, 2)
            cash_after = funds - amount

            # fill in transactions table with new data
            db.execute("INSERT INTO transactions (user_id, symbol, name, number, price, amount, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, symbol, name, shares, price, shares*price, "buy"))
            db.execute("UPDATE users SET cash = :cash_after WHERE id = :user_id", cash_after=cash_after, user_id=user_id)

            message = "You've successfully bought " + str(shares) + " shares of " + symbol
            flash(message)
            return redirect(url_for("index"))

        else:
            return apology("please enter stock ticker symbol", 403)

    # request symbol information from IEX cloud
    quoteInfo = lookup(symbol)

    # redirect to buy page with error message if no symbol was found
    if quoteInfo is None:
        return apology("The symbol was not found or something else went wrong.", 403)

    # load buy page with stock ticker information filled in
    return render_template("buy.html", quoteInfo = quoteInfo, shares = shares, price = usd(quoteInfo["price"]), cash = usd(funds),
                            required = usd(quoteInfo["price"] * int(shares)))


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    data = get_history("date", "desc", "all")

    if data == "error":
        return apology("Database read error", 403)
    elif data == "empty":
        return apology("You did not make any transaction yet", 403)

    return render_template("history.html", history = data)


@app.route("/account", methods = ["GET", "POST"])
@login_required
def account():
    """Show account management page"""
    user_id = session.get("user_id")

    # User reached route via POST (as by submitting a form with new username/password via POST)
    if request.method == "POST":

        username = request.form.get("newname")
        password = request.form.get("newpass")
        confirmation = request.form.get("confpass")

        if username or password:
            # if new password was submitted
            if password:
                # Check password matches pattern
                if not re.match("(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*(&|%|#)).{8,}", password):
                    return apology("Password must contain at least one number, one uppercase and lowercase letter, one special symbol (&,$,#) and has at least 8 characters", 403)
                # Ensure password confirmation matches password
                if password != confirmation or not confirmation:
                    return apology("confirmation does not match password", 403)

                # Udate password hash in database
                db.execute("UPDATE users SET hash = :hash WHERE id = :user_id", hash = generate_password_hash(password), user_id = user_id)

            # if  new username was submitted
            if username:
                # Ensure username is not in use
                if db.execute("SELECT * FROM users WHERE username = :username AND id != :user_id",
                            username=username, user_id = user_id):
                    return apology("username already exists", 403)

                # Udate username in database
                db.execute("UPDATE users SET username = :username WHERE id =  :user_id", username = username, user_id = user_id)

            # Flash success message
            flash("Your username / password were changed.")

            # Redirect user to home page
            return redirect(url_for("index"))

        else:
            # Flash no-change message
            flash("Your username / password were not changed")

            # Redirect user to home page
            return redirect(url_for("account"))

    else:
        user = db.execute("SELECT username, cash FROM users WHERE id = :user_id", user_id = user_id)
        return render_template("account.html", user = user)

@app.route("/changefund", methods = ["POST"])
@login_required
def changefund():
    """Manage cash funds in portfolio"""
    user_id = session.get("user_id")

    # User reached route via POST by submitting a form
    if request.method == "POST":

        operation = request.form.get("cashop")
        amount = int(request.form.get("amount"))

        if not amount or amount < 0:
            return apology("Please enter amount of cash you would like to add / withdraw a a positive number", 403)

        current = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = user_id)

        if operation == "add":
            new_amount = current[0]["cash"] + amount
            message = "You successfully added funds to your account"

        if operation == "withdraw":
            if amount > current[0]["cash"]:
                return apology("The amount of cash in your account is not enough", 403)
            new_amount = current[0]["cash"] - amount
            message = "You successfully withdrew funds from your account"

        # Udate username in database
        db.execute("UPDATE users SET cash = :new_amount WHERE id =  :user_id", new_amount = new_amount, user_id = user_id)

        # Flash success message
        flash(message)

        # Redirect user to home page
        return redirect(url_for("index"))

    else:
        return redirect(url_for("account"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Confirm successfull log out in flash message
    flash("You were successfully logged out")

    # Redirect user to login form
    return redirect(url_for("index"))


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")

        # load quore page again if symbol is not provided
        if not symbol:
            flash("Please enter stock ticker symbol")
            return redirect(url_for("quote"))

        # request symbol info from IEX cloud
        quoteInfo = lookup(symbol)

        if quoteInfo is None:
            flash("The symbol was not found or something else went wrong.")
            return redirect(url_for("quote"))

        # Redirect user to page with stock ticker(-s) info
        return render_template("quoted.html", symbol = quoteInfo["symbol"], name = quoteInfo["name"], price = usd(quoteInfo["price"]))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure username is uniq
        elif db.execute("SELECT * FROM users WHERE username = :username",
                        username=username):
            return apology("username already exists", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Check password matches pattern
        if not re.match("(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*(&|%|#)).{8,}", password):
            return apology("Password must contain at least one number, one uppercase and lowercase letter, one special symbol (&,$,#) and has at least 8 characters", 403)

        # Ensure password confirmation matches password
        elif password != confirmation or not confirmation:
            return apology("confirmation does not match password", 403)

        # Insert username in database
        id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                          username = username, hash = generate_password_hash(password))

        # log new registered user in
        session["user_id"] = id

        # Flash success message
        flash("Congratulation! You were successfully registered!")

        # Redirect user to home page
        return redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    user_id = session.get("user_id")

    # request a list of owned shares
    holdings = db.execute("SELECT symbol, name, SUM(number) shares, SUM(amount) total, (SUM(amount) / SUM(number)) avgprice FROM transactions WHERE user_id = :user_id GROUP BY symbol", user_id = user_id)

    # return base sell page if no url variiables
    if not request.args and request.method == "GET":

        if holdings is not None:

            # prepare a list of owned shares to choose from
            list = []
            for i in range(len(holdings)):
                list.append(holdings[i]["symbol"])

            # load sell page
            return render_template("sell.html", list = list)

        # return apology if user does not own any stock
        else:
            return apology("You do not own any stock to sell", 403)


    # request stock ticker symbol from URL
    symbol = request.args.get("symbol", '')

    # no stock ticker symbol was provided via GET
    if not symbol:

        # User reached route via POST (as by submitting a form via POST)
        if request.method == "POST":

            symbol = request.form.get("symbol")
            name = request.form.get("name")
            shares = request.form.get("shares")
            price = float(request.form.get("price"))

            # load apology if symbol is not provided
            if not symbol:
                return apology("Please choose ticker symbol of stock you want to sell", 403)

            # load apology if number is not provided
            if not shares or int(shares) <= 0:
                return apology("Please enter positive number of shares to sell", 403)

            # get owned number of stocks
            for i in range(len(holdings)):
                if symbol == holdings[i]["symbol"]:
                    sharesOwned = holdings[i]["shares"]
                    break

            # check number of shares available
            if int(shares) > sharesOwned:
                return apology("Sorry, you do not own enough number of shares ", 403)

            # prepare data to be inserted into db
            amount = round(int(shares) * price, 2) * -1
            funds = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = user_id)
            cash_after = float(funds[0]["cash"]) - amount

            # fill in transactions table with new data
            db.execute("INSERT INTO transactions (user_id, symbol, name, number, price, amount, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, symbol, name, int(shares) * -1, price, amount, "sell"))
            db.execute("UPDATE users SET cash = :cash_after WHERE id = :user_id", cash_after=cash_after, user_id=user_id)

            message = "You've successfully sold " + str(shares) + " shares of " + symbol
            flash(message)
            return redirect(url_for("index"))

        else:
            return apology("must enter stock ticker symbol", 403)

    # request symbol information from IEX cloud
    quoteInfo = lookup(symbol)

    # redirect to buy page with error message if no symbol was found
    if quoteInfo is None:
        return apology("The symbol was not found or something else went wrong.", 403)

    # get number of owned stocks and average price of aquisition
    for i in range(len(holdings)):
        if symbol == holdings[i]["symbol"]:
            sharesOwned = holdings[i]["shares"]
            avgPrice = holdings[i]["avgprice"]
            amount = holdings[i]["total"]
            break

    # load sell page with stock ticker information filled in
    return render_template("sell.html", quoteInfo = quoteInfo, sharesOwned = sharesOwned, avgPrice = avgPrice, amount = amount)

@app.route("/_sort_table", methods = ["GET", "POST"])
def sort_table():
    if request.method == "POST":
        sort_by = request.form.get("sortBy")
        sort_order = request.form.get("sortOrder")
        table_type = request.form.get("tableType")
        filter_by = request.form.get("filterBy")

        if not table_type:
            return redirect(url_for("index"))

        elif table_type == "portfolio":
            data = get_portfolio(sort_by, sort_order)
            return render_template("portfolio_table.html", rows = data[1], totals = data[0])

        elif table_type == "history":
            data = get_history(sort_by, sort_order, filter_by)
            return render_template("history_table.html", history = data)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
