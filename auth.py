from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, db, Order
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # getting data from the user
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        # checking if password is correct and the user exists
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in successlufly!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash("Incorrect password, please try again.", category='error')
        else:
            flash("Email not registered.", category='error')

    return render_template('login.html', user=current_user)

# logging out


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        # getting data from the user
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        surname = request.form.get('surname')
        mobile = request.form.get('mobile')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # sign up restrictions
        user = User.query.filter_by(email=email).first()

        # checking if the email is already registered, passwords match and are at least 8 char long
        if user:
            flash("Email already registered", category='error')
        elif password1 != password2:
            flash("Passwords don't match", category='error')
        elif len(password1) < 8:
            flash("Password must be at least 8 characters long", category='error')
        else:
            new_user = User(email=email, first_name=first_name, surname=surname,
                            mobile=mobile, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()

            flash("Account created!", category="success")
            return redirect(url_for('views.home'))

    return render_template('sign_up.html', user=current_user)
