from flask import Blueprint, render_template, session, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, label
from werkzeug.exceptions import default_exceptions

transactions = Blueprint(
    'transactions', __name__,
    template_folder = 'templates')

from finance.helpers import login_required, apology, lookup, usd, get_history, errorhandler
from finance.model import *

@transactions.route("/buy", methods=["GET", "POST"])
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
    #fund = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = user_id)
    fund = Users.query.filter(Users.id == user_id).first()
    funds = float(fund.cash)

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
            new_transaction = Transactions (
                user_id = user_id,
                symbol = symbol,
                name = name,
                number = shares,
                price = price,
                amount = shares * price,
                type = "buy")
            db.session.add(new_transaction)
            db.session.commit()
            
            # update cash
            cur_user = Users.query.filter(Users.id == user_id).first()
            cur_user.cash = cash_after
            db.session.commit()

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
    return render_template("buy.html", quoteInfo = quoteInfo, shares = shares, price = quoteInfo["price"], cash = funds,
                            required = quoteInfo["price"] * int(shares))


@transactions.route("/history")
@login_required
def history():
    """Show history of transactions"""

    data = get_history("date", "desc", "all")

    if data[0] == "error":
        # return render_template('debug.html', fund = data[1])
        return apology("Database read error", 403)
    elif data == "empty":
        return apology("You did not make any transaction yet", 403)

    return render_template("history.html", history = data)


@transactions.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    user_id = session.get("user_id")

    # request a list of owned shares
    #holdings = db.execute("SELECT symbol, name, SUM(number) shares, SUM(amount) total, (SUM(amount) / SUM(number)) avgprice FROM transactions WHERE user_id = :user_id GROUP BY symbol", user_id = user_id)
    holdings = db.session.query(Transactions.symbol, Transactions.name,
                                func.sum(Transactions.number).label('shares'),
                                func.sum(Transactions.amount).label('total'),
                                label('avgprice', func.sum(Transactions.amount) / func.sum(Transactions.number))).\
                                filter(Transactions.user_id == user_id).group_by(Transactions.symbol).all()

    # return base sell page if no url variiables
    if not request.args and request.method == "GET":

        if holdings is not None:

            # prepare a list of owned shares to choose from
            list = []
            for row in holdings:
                list.append(row.symbol)

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
            for row in holdings:
                if symbol == row.symbol:
                    sharesOwned = row.shares
                    break

            # check number of shares available
            if int(shares) > sharesOwned:
                return apology("Sorry, you do not own enough number of shares ", 403)

            # prepare data to be inserted into db
            amount = round(int(shares) * price, 2) * -1

            #funds = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = user_id)
            funds =  Users.query.filter(Users.id == user_id).first()
            cash_after = float(funds.cash) - amount

            # fill in transactions table with new data
            new_transaction = Transactions (
                user_id = user_id,
                symbol = symbol,
                name = name,
                number = int(shares) * - 1,
                price = price,
                amount = amount,
                type = "sell")
            db.session.add(new_transaction)
            db.session.commit()

            cur_user = Users.query.filter(Users.id == user_id).first()
            cur_user.cash = cash_after
            db.session.commit()

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
    for row in holdings:
        if symbol == row.symbol:
            sharesOwned = row.shares
            avgPrice = row.avgprice
            amount = row.total
            break

    # load sell page with stock ticker information filled in
    return render_template("sell.html", quoteInfo = quoteInfo, sharesOwned = sharesOwned, avgPrice = avgPrice, amount = amount)

# Listen for errors
for code in default_exceptions:
    transactions.errorhandler(code)(errorhandler)