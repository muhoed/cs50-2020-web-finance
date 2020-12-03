from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.exceptions import default_exceptions

from finance.helpers import login_required, lookup, usd, get_portfolio, get_history, apology, errorhandler

home = Blueprint('home', __name__)

@home.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # request necessary data
    data = get_portfolio("symbol", "asc")
    if data == "error":
        return apology("database read error", 403)
    #return render_template('debug.html', fund = data)
    return render_template("index.html", rows = data[1], totals = data[0])

@home.route("/quote", methods=["GET", "POST"])
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

@home.route("/_sort_table", methods = ["GET", "POST"])
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

# Listen for errors
for code in default_exceptions:
    home.errorhandler(code)(errorhandler)
