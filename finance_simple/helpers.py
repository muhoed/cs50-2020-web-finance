import os
import requests
import urllib.parse

from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def get_portfolio(sort_by, sort_order):
    # prepare data for portfolio view
    user_id = session.get("user_id")

    try:
        statement = "SELECT symbol, name, SUM(number) shares, SUM(amount) total, (SUM(amount) / SUM(number)) avgprice FROM transactions WHERE user_id = :user_id AND shares != 0 GROUP BY symbol ORDER BY " + sort_by + " " + sort_order.upper()
        holdings = db.execute(statement, user_id = user_id)
        funds = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = user_id)

    except:
        return apology("Database read error", 403)

    else:
        mktValueTotal, portfolioTotal, unrlzTotal = 0, 0, 0
        rows = []
        cash = funds[0]["cash"]
        if len(holdings) < 1:
            investedTotal = portfolioTotal + cash
            fundsTotal = mktValueTotal + cash

        else:
            for i in range(len(holdings)):
                quote = lookup(holdings[i]["symbol"])
                mktValue = holdings[i]["shares"] * quote["price"]
                unrLz = holdings[i]["shares"] * quote["price"] - holdings[i]["total"]
                rows.append({"symbol":holdings[i]["symbol"], "name":holdings[i]["name"],
                    "shares":holdings[i]["shares"], "price":usd(quote["price"]),
                    "total":usd(holdings[i]["total"]), "avgprice":usd(holdings[i]["avgprice"]),
                    "mktvalue":usd(mktValue), "unrlz":usd(unrLz)
                })
                mktValueTotal = mktValueTotal + float(mktValue)
                portfolioTotal = portfolioTotal + holdings[i]["total"]
                unrlzTotal = unrlzTotal + unrLz
                investedTotal = portfolioTotal + cash
                fundsTotal = mktValueTotal + cash

    totals = {"cash": usd(cash), "mktValueTotal": usd(mktValueTotal),
        "portfolioTotal": usd(portfolioTotal), "unrlzTotal": usd(unrlzTotal),
        "investedTotal": usd(investedTotal), "fundsTotal": usd(fundsTotal)}
    return [totals, rows]

def get_history (sort_by, sort_order, filter_by):

    user_id = session.get("user_id")

    try:
        if filter_by == "" or filter_by == "all":
            statement = "SELECT * FROM transactions WHERE user_id = :user_id ORDER BY " + sort_by + " " + sort_order.upper()
            data = db.execute(statement, user_id = user_id)
        else:
            statement = "SELECT * FROM transactions WHERE user_id = :user_id AND symbol = :symbol ORDER BY " + sort_by + " " + sort_order.upper()
            data = db.execute(statement, user_id = user_id, symbol = filter_by.upper())

    except:
        return "error"

    else:
        if data is None:
            return "empty"

    return data