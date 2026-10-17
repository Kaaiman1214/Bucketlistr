from flask import Blueprint, render_template, request, flash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html", boolean=True)

@auth.route('/logout')
def logout():
    return "<p>Logout</p>"

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        Username = request.form.get('Username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if len(email) < 4:
            flash('Must enter a valid Email Address.', category='error')
        elif len(Username) < 2:
            flash('Username must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 8:
            flash('Password must be atleast 8 characters.', category='error')
        elif not any(char in password1 for char in "!@#$%^&*()-_=+[{]}\|;:'\",<.>/?"):
            flash('Password must contain atleast one special character', category='error')
        else:
            flash('Account created successfully!', category='success')
            pass

    return render_template("sign_up.html")