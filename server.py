from flask import Flask, render_template, redirect, request,flash, session
from flask_bcrypt import Bcrypt 
from mysqlconnection import connectToMySQL
import re
EMAIL_REGEX = re.compile(r'^[a-za-z0-9\.\+_-]+@[a-za-z0-9\._-]+\.[a-za-z]*$')
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$')
app = Flask(__name__)
app.secret_key="Helloo"
bcrypt = Bcrypt(app) 

# LOG IN/SIGN UP PAGE
@app.route('/')
def index():
    mysql = connectToMySQL("usersdb")
    users = mysql.query_db("SELECT * FROM users")

    return render_template('index.html', users = users)
@app.route("/signup/process", methods =['POST'])
def create():
    mysql = connectToMySQL("usersdb")
    form = request.form
    

    if len(form['first_name'])<1:
        flash("First name must be written!", "first_name")
    if any(char.isdigit() for char in request.form['first_name']) == True:
        flash('First name cannot have  any numbers!', "first_name")
    if len(form['first_name'])<1:
        flash("Last name must be written!", "last_name")
    if any(char.isdigit() for char in request.form['last_name']) == True:
        flash('Last name cannot have any numbers!', "last_name")
    if len(form['email'])<1:
        flash("Email must be written!", "email")
    if len(form['password'])<1:
        flash("Password must be written!", "password")
    if len(form['password'])<8:
        flash("Password should be more than 8 characters!","password")
    if not  EMAIL_REGEX.match(request.form['email']):
        flash("You should enter a valid email!", "email")
    if not  PASSWORD_REGEX.match(request.form['password']):
        flash("Your password should have at least  1 uppercase letter and 1 numeric value", "password")
    if request.form['confirm_password'] != request.form['password']:
        flash("Passwords should match!", "confirm_password")
   
    query = "SELECT id FROM users WHERE email= %(email)s;"
    data = {
                "email" : request.form['email']

    }
    email_list = mysql.query_db(query, data)

    if len(email_list)>0:
            flash("Email is already taken!", "email")
    

    
    
    if '_flashes' in session.keys():
        return redirect("/")
    else:
        
    
        session['email'] = form['email']
        session['first_name'] = form['first_name']
        session['last_name'] = form['last_name']
        session['password'] = form['password']
        session['confirm_password'] = form['confirm_password']
        

        
        
        
        return redirect('/users')

@app.route("/login/process", methods=['POST'])
def login():
    mysql = connectToMySQL("usersdb")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form["email"] }
    result = mysql.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0]['psw_hash'], request.form['password']):
            
            session['userid'] = result[0]['id']
            session['first_name'] = result[0]['first_name']
            session['email']= result[0]['email']
            
            return redirect('/success')

    
    flash("Email or Password Incorrect", "login")
    return redirect("/")

# INSERT NEW USERS
@app.route("/users")
def email():
    

    mysql = connectToMySQL("usersdb")
    pw_hash = bcrypt.generate_password_hash(session['password'])
    query = "INSERT INTO users (first_name, last_name, email, psw_hash, created_at,updated_at) VALUES (%(first_name)s,%(last_name)s,%(email)s,%(pw_hash)s,NOW(), NOW());"
    data = {    
                'first_name': session['first_name'],
                'last_name': session['last_name'],
                "email" : session['email'],
                'pw_hash': pw_hash

                
        }
    mysql.query_db(query, data)
    mysql = connectToMySQL("usersdb")
    
    query = "SELECT * FROM users WHERE email = %(email)s "
    data = {    
        "email" : session['email']

                
    }
    res = mysql.query_db(query, data)
    if res:
        
        flash("You have successfully signed up. Please log in!", "successfully")

    
    
        return redirect("/")


# SUCCESS PAGE

@app.route("/success", methods=["GET","POST"])
def success():
   
        
    if "first_name" in session:
        mysql = connectToMySQL("usersdb")

        

        
        query = "SELECT * FROM users WHERE NOT ( email = %(email)s );"
        data = {
        "email": session["email"],
        
    
        }
        user= mysql.query_db(query,data)
        



        if user:
            session['id_to'] = user[0]['id']
            
            print("id_to",session['id_to'])
            
        
            print(session["first_name"])
            mysql = connectToMySQL("usersdb")
            query = "SELECT * FROM messages WHERE id_to = %(userid)s  ORDER BY created_at DESC;"
            data = {
            "userid": session['userid'], 

            
            
            }
            messages= mysql.query_db(query,data)

            mysql = connectToMySQL("usersdb")
            query = "SELECT COUNT(*) AS nr_msg FROM messages  WHERE id_to = %(userid)s ;"
            data = {
            "userid": session['userid'], 
            }
            
            nr_msg = mysql.query_db(query,data)

            mysql = connectToMySQL("usersdb")
            query = "SELECT COUNT(*) AS sent FROM messages  WHERE first_name_from = %(first_name_from)s ;"
            data = {
            "first_name_from": session['first_name'], 
            }
            
            sent = mysql.query_db(query,data)


            
        


            if messages:
               
                    
                return render_template("success.html", user=user, messages=messages, nr_msg = nr_msg, sent=sent)


            elif not messages:

                return render_template("success.html", user=user, messages=messages, sent=sent)
            
        else:
            return redirect("/")

   


        
        



# SEND MESSAGES


@app.route("/send", methods=["POST"])
def send():
    mysql = connectToMySQL("usersdb")
    query = "INSERT INTO messages (first_name_from,id_from, id_to, message, created_at,updated_at) VALUES (%(from)s,%(users_id)s,%(id)s,%(message)s,NOW(), NOW());"
    data = {    
                "from": session['first_name'],
                'users_id': session['userid'],
                "id": request.form['id'],
                "message" : request.form['message'],
                
                
        }
    mysql.query_db(query, data)


    
    return redirect("/success")
# DELETE MESSAGES


@app.route("/delete/message/<id>", methods = ['POST'])
def delete(id):
    
        mysql = connectToMySQL("usersdb")
        query = "DELETE FROM messages WHERE id = %(id)s"
        data = {

            'id': request.form['id'],
        }
        mysql.query_db(query, data)
        
    
    
        return redirect("/success")

    
# LOG OUT 

@app.route("/logout", methods=["POST"])
def logout():
    
    

    session.clear()

    return redirect('/')





    



if __name__ == "__main__":
    app.run(debug=True)
   

        
        
