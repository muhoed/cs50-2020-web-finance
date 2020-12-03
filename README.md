CS50 Finance implementation using Flask
Dmitry Argunov @ 'muhoed'
dargunov @ yahoo.com

The application is my solution for the CSS0 Intoduction to Computer science on-line course / block 'Tracks' / task 'Web - Finance'. 
Requirements and distribution base code are here: https://cs50.harvard.edu/x/2020/tracks/web/finance/.

Two variants of solution are presented:
1)  simplified variant with all-in-one Flask application aproach:
    no blueprints
    CS50 SQL library used to deal with SQLite
    - 'finance-simple'
2)  more advanced variant of Flask application implementation:
    using package approach with dynamic application creation in 'application factory'; 
    all main groups of functionality are divided into blueprints;
    blueprints have their own resources, i.e. 'templates';
    handling SQLite database connection and other operations through Flask-SQLAlchemy extension
    - 'finance'

The second variant is the main and can be run from current diirectory with 'flask run' assuming all dependencies are installed.
Flask's 'SECRET_KEY' is not provided assuming it is set in the application environment. Can be added to 'config.py' directly or exported in other suitable way.
IEX token @ 'API_KEY' IS NOT PROVIDED BUT IS REQUIRED ('export API_KEY = IEX token'). IEX token can be obtained upon free registration here: https://iexcloud.io/cloud-login#/register/.

Main functionality is the same between both variants. Functionality implemented beyond the task's formal requirements:
1) user is able to buy / sell stock from the portfolio page
2) all negatice values are showed in red color (JavaScript)
3) sorting of portfolio and transactions history tables (AJAX/Javascript)
4) filtering of table by ticker symbol in transactions history table (AJAX/Javascript)
5) calculation of estimated profit/losses and presenting it to the user through portfolio page (Javascript)
6) account management page where a user can change her/his username and password, add or withdraw cash (Javascript, Bootstrap's modals)
7) requirement to use passord containing at least 8 symbols, at least one of which should be small letter, capital letter, number,
    special symbols (&, ...)
8) all form input is validated both on client side through HTML5 validation tools and on the flask application side
