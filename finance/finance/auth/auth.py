import re

from flask import Blueprint, request, render_template, flash, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions

auth = Blueprint(
    'auth', __name__,
    template_folder='templates'
)

from finance.helpers import apology, errorhandler
from finance.model import db, Users

@auth.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        try:
            cur_user = Users.query.filter(Users.username == username).first()
        except Exception as error:
            return apology("database read error", 403)

        # Ensure username exists
        if cur_user is None:
            return apology("Invalid username", 403)

        # Ensure password is correct
        if not check_password_hash(cur_user.hash, password):
            return apology("invalid password", 403)

        # Remember which user has logged in
        session["user_id"] = cur_user.id

        # Redirect user to home page
        return redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/login.html")


@auth.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Confirm successfull log out in flash message
    flash("You were successfully logged out")

    # Redirect user to login form
    return redirect(url_for("home.index"))

@auth.route("/register", methods=["GET", "POST"])
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
        elif Users.query.filter(Users.username == username).first() is not None:
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
        new_user = Users(
            username = username,
            hash = generate_password_hash(password))
        db.session.add(new_user)
        db.session.flush()

        # log newly registered user in
        #id = db.session.query(Users.id).filter(Users.username == username).first()
        session["user_id"] = new_user.id
        
        # finalize changes to database
        db.session.commit()
        
        # Flash success message
        flash("Congratulation! You were successfully registered!")

        # Redirect user to home page
        return redirect(url_for("home.index"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

# Listen for errors
for code in default_exceptions:
    auth.errorhandler(code)(errorhandler)
