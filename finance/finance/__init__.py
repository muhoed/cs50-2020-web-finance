import os

from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

def create_app():
    # Initialize core application and load configuration
    app = Flask(__name__)
    app.config.from_pyfile("config.py")

    # Ensure responses aren't cached
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

    # Initialize session
    Session(app)

    # Initialize database
    from finance.model import db
    db.init_app(app)

    # Make sure API key is set
    if not os.environ.get("API_KEY"):
        raise RuntimeError("API_KEY not set")

    with app.app_context():
        # import all parts of application
        from . import home
        from . import helpers
        from .admin import admin
        from .auth import auth
        from .transactions import transactions

        # initialize custom filter
        app.jinja_env.filters["usd"] = helpers.usd

        # register blueprints
        app.register_blueprint(home.home)
        app.add_url_rule('/', endpoint='index')

        app.register_blueprint(admin.admin)
        app.register_blueprint(auth.auth)
        app.register_blueprint(transactions.transactions)

        # create database
        db.create_all()

        return app