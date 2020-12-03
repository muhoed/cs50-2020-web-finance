import re

from flask import Blueprint, session, request, flash, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

admin = Blueprint(
    'admin', __name__,
    template_folder = 'templates')

from finance.helpers import apology, login_required, errorhandler
from finance.model import *


@admin.route("/account", methods = ["GET", "POST"])
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
                cur_user = Users.query.filter(Users.id ==  user_id).first()
                cur_user.hash = generate_password_hash(password)
                db.session.commit()

            # if new username was submitted
            if username:
                # Ensure username is not in use
                if Users.query.filter(Users.username == username, Users.id != user_id).first() is not None:
                    return apology("username already exists", 403)

                # Udate username in database
                cur_user = Users.query.filter(Users.id == user_id).first()
                cur_user.username = username
                db.session.commit()

            # Flash success message
            flash("Your username / password were changed.")

            # Redirect user to home page
            return redirect(url_for("home.index"))

        else:
            # Flash no-change message
            flash("Your username / password were not changed")

            # Redirect user to home page
            return redirect(url_for("admin.account"))

    else:
        user = db.session.query(Users.username, Users.cash).filter(Users.id == user_id)
        return render_template("account.html", user = user)

@admin.route("/changefund", methods = ["POST"])
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

        #current = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = user_id)
        current = Users.query.filter(Users.id == user_id).first()

        if operation == "add":
            new_amount = current.cash + amount
            message = "You successfully added funds to your account"

        if operation == "withdraw":
            if amount > current.cash:
                return apology("The amount of cash in your account is not enough", 403)
            new_amount = current.cash - amount
            message = "You successfully withdrew funds from your account"

        # Udate cash amount in database
        current.cash = new_amount
        db.session.commit()

        # Flash success message
        flash(message)

        # Redirect user to home page
        return redirect(url_for("home.index"))

    else:
        return redirect(url_for("admin.account"))

# Listen for errors
for code in default_exceptions:
    admin.errorhandler(code)(errorhandler)