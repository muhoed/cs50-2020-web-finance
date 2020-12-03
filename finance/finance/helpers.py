import os
import requests
import urllib.parse

# from cs50 import SQL
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, label
from sqlalchemy import asc, desc
from functools import wraps
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from finance.model import *

# Configure CS50 Library to use SQLite database
#db = SQL("sqlite:///finance.db")

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
            return redirect("login")
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
    # get suitable order direction SQLAlchemy object based on passed sort_order 
    if sort_order == "asc":
        direction = asc
    else:
        direction = desc

    try:
        holdings = db.session.query(Transactions.symbol, Transactions.name,
                                    func.sum(Transactions.number).label('shares'),
                                    func.sum(Transactions.amount).label('total'),
                                    (func.sum(Transactions.amount) / func.sum(Transactions.number)).label('avgprice')).\
                                    filter(Transactions.user_id == user_id).\
                                    group_by(Transactions.symbol).\
                                    having(func.sum(Transactions.number) != 0).\
                                    order_by(direction(sort_by)).all()
        
        funds = db.session.query(Users.cash).filter(Users.id == user_id).first()

    except Exception as error:
        #return error
        return "error"

    else:
        mktValueTotal, portfolioTotal, unrlzTotal = 0, 0, 0
        rows = []
        cash = funds.cash
        if len(holdings) < 1:
            investedTotal = portfolioTotal + cash
            fundsTotal = mktValueTotal + cash

        else:
            for row in holdings:
                quote = lookup(row.symbol)
                mktValue = row.shares * quote["price"]
                unrLz = row.shares * quote["price"] - float(row.total)
                rows.append({"symbol":row.symbol, "name":row.name,
                    "shares":row.shares, "price":quote["price"],
                    "total":row.total, "avgprice":row.avgprice,
                    "mktvalue":mktValue, "unrlz":unrLz
                })
                mktValueTotal = mktValueTotal + float(mktValue)
                portfolioTotal = portfolioTotal + row.total
                unrlzTotal = unrlzTotal + unrLz
                investedTotal = portfolioTotal + cash
                fundsTotal = mktValueTotal + cash

    totals = {"cash": cash, "mktValueTotal": mktValueTotal,
        "portfolioTotal": portfolioTotal, "unrlzTotal": unrlzTotal,
        "investedTotal": investedTotal, "fundsTotal": fundsTotal}
    return [totals, rows]

def get_history (sort_by, sort_order, filter_by):
    """prepare data for transaction history view"""
    user_id = session.get("user_id")
    # get suitable order direction SQLAlchemy object based on passed sort_order 
    if sort_order == "asc":
        direction = asc
    else:
        direction = desc
        
    try:
        if filter_by == "" or filter_by == "all":
            data = Transactions.query.filter(Transactions.user_id == user_id).order_by(direction(sort_by)).all()
        else:
            data = Transactions.query.filter(Transactions.user_id == user_id, 
                                            Transactions.symbol == filter_by.upper()).order_by(direction(sort_by)).all()
    except:
        return "error"
    else:
        if len(data) < 1:
            return "empty"
    return data

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)