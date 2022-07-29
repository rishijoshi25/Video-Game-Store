from crypt import methods
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import psycopg2
import config

app = Flask(__name__, template_folder="templates")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def get_db_connection():
    conn = psycopg2.connect(**config.POSTGRES_CONFIG)
    return conn
    
@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    msg = ''

    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        
        email = request.form['email']
        password = request.form['password']
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute(f"SELECT customer_id, email, first_name FROM customer WHERE email = '{email}' AND password = '{password}'") 
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['email'] = account[1]
            session['first'] = account[2]
            return redirect(url_for('dashboard', customer_id=session['id']))
        else:
            msg = 'Incorrect username/password!'

    return render_template('signin.html', msg=msg)

@app.route("/register", methods = ['GET', 'POST'])
def register():
    msg = ''
    
    if request.method == 'POST':
        if request.form.get("firstname") and request.form.get("lastname") and request.form.get("email") and request.form.get("contact") and request.form.get("password"):
            first = request.form.get("firstname")
            last = request.form.get("lastname")
            email = request.form.get("email")
            contact = request.form.get("contact")
            password = request.form.get("password")
            dob = request.form.get("DOB")

            db_conn = get_db_connection()
            cursor = db_conn.cursor()
            cursor.execute(f"SELECT * FROM customer WHERE email = '{email}' AND first_name = '{first}' AND contact_number = '{contact}'")
            account = cursor.fetchone()
            # If account exists show error and validation checks
            if account:
                msg = 'Account already exists!'
            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                max_cust_id = f"SELECT MAX(customer_id) + 1 from customer"
                cursor.execute(max_cust_id)
                cust_id = int(cursor.fetchone()[-1])

                insert_customer_query = f"""
                INSERT INTO customer(customer_id, first_name, last_name, contact_number, email, dob, password) 
                VALUES 
                ('{cust_id}', '{first}', '{last}', '{contact}', '{email}', '{dob}', '{password}')"""
                cursor.execute(insert_customer_query)
                db_conn.commit()
                msg = 'You have successfully registered!'

        else:
            msg = 'Please fill out the form!'
    
    return render_template('register.html', msg=msg)

@app.route('/dashboard/<customer_id>/', methods=['GET', 'POST'])
def dashboard(customer_id, customer= None, 
purchases=None, game_achievements=None, game_stats=None):
    
    if 'loggedin' in session:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        select_customer_details = f"""SELECT * from customer where customer_id = '{customer_id}'"""
        
        cursor.execute(select_customer_details)
        customer_details = cursor.fetchall()

        select_customer_purchase_details = f"""
            SELECT g.game_id, g.game_name, p.payment_method FROM 
            customer c INNER JOIN payment p 
            on c.customer_id = p.customer_id
            INNER JOIN purchase pu
            on p.payment_id = pu.payment_id
            INNER JOIN game g
            on g.game_id = pu.game_id where c.customer_id = '{customer_id}'
            and pu.purchased_flag = 1
            order by p.payment_time,p.payment_id desc;
        """

        cursor.execute(select_customer_purchase_details)
        purchase_details = cursor.fetchall()

        select_game_achievements_data = f"""
        select g.game_name, a.title, a.badge from customer c inner join game_achievements ga 
        on c.customer_id = ga.customer_id inner join achievements a on
        ga.achieve_id = a.achieve_id inner join game g on g.game_id = ga.game_id where c.customer_id = {customer_id};"""

        cursor.execute(select_game_achievements_data)
        game_achievements_data = cursor.fetchall()

        select_game_stats_data = f"""   
        select s.hours_played, s.last_played, s.ingame_purchase_amt, g.game_name from customer c inner join game_stats gs
        on c.customer_id = gs.customer_id inner join stats s on
        gs.stats_id = s.stats_id inner join game g on g.game_id = gs.game_id where c.customer_id = {customer_id};"""
        
        cursor.execute(select_game_stats_data)
        game_stats_data = cursor.fetchall()
        
        return render_template('dashboard.html', customer_id=session['id'], 
        purchases = purchase_details, game_achievements = game_achievements_data, 
        game_stats=game_stats_data, customer = customer_details)
    
    return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search_games(search_term = None, games=None):
    if 'loggedin' in session and request.method == 'POST':
        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        game_text = request.form.get("gameText")

        if game_text:
            search_game_query = f"""
            SELECT game_name, game_id, developer, publisher
            FROM game 
            where 
            game_name ILIKE '%{game_text}%' or game_name ILIKE '%{game_text}' or game_name ILIKE '{game_text}%'"""

            cursor.execute(search_game_query)
            games = cursor.fetchall()

            return render_template('gamesearch.html', search_term = game_text, games=games)

        else:
            return render_template('dashboard.html', customer_id=session['id'])


    return redirect(url_for('login'))

@app.route('/game/<game_id>', methods=['GET', 'POST'])
def game_dashboard(game_id, game_details=None, categories=None,
 genres=None, game_requirements=None, purchased=None, game_support=None):
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    if 'loggedin' in session:
        
        if request.method=="POST" and 'add_cart' in request.form:
            get_payment_id_if_exists = f"""
                SELECT coalesce(pa.payment_id, 0) 
                from payment pa inner join purchase pu 
                on pu.payment_id = pa.payment_id 
                where 
                pa.customer_id = '{session["id"]}' and pu.purchased_flag = 0;
            """
            print(get_payment_id_if_exists)
            cursor.execute(get_payment_id_if_exists)
            payment_id = cursor.fetchone()

            print(payment_id)
            if not payment_id:
                payment_id_query = """SELECT nextval('payment_seq')"""

                cursor.execute(payment_id_query)
                payment_id = cursor.fetchone()
                payment_id = int(payment_id[-1])
                print(payment_id)

                insert_payment_details = f"""
                    INSERT INTO payment 
                    (payment_id, customer_id, cost)
                    VALUES
                    ('{payment_id}', '{session.get("id")}', '0.0')
                    """
                cursor.execute(insert_payment_details)
            else:
                payment_id = int(payment_id[-1])

            insert_purchase_details = f"""
                INSERT INTO purchase
                (payment_id, game_id, purchased_flag)
                VALUES
                ('{payment_id}', '{game_id}', 0)
            """

            cursor.execute(insert_purchase_details)
            print("Inserted purchase")

            update_purchase = f"""
                UPDATE Payment 
                SET cost = 
                (SELECT 
                SUM(g.price) 
                FROM
                game g, purchase p 
                where 
                g.game_id = p.game_id 
                and p.payment_id = '{payment_id}' 
                and p.purchased_flag = 0), payment_time = CURRENT_TIMESTAMP
                """
            cursor.execute(update_purchase)
            print("Updated payment")
            db_conn.commit()
            
        select_game_details = f"""
        select g.*, coalesce(sum(s.hours_played), 0) as hours_played 
        from game g left join game_stats gs 
        on gs.game_id = g.game_id 
        left join stats s 
        on gs.stats_id = s.stats_id 
        where 
        g.game_id='{game_id}' group by g.game_id, g.game_name;
        """

        cursor.execute(select_game_details)
        game_details = cursor.fetchone()
        
        game_categories_details = f"""
            select gc.category from game g inner join game_category gc 
            on g.game_id = gc.game_id where g.game_id='{game_id}';
        """

        cursor.execute(game_categories_details)
        categories = cursor.fetchall()

        game_genres_details = f"""
            select gg.genre from game g inner join game_genre gg 
            on g.game_id = gg.game_id where g.game_id='{game_id}';
        """

        cursor.execute(game_genres_details)
        genres = cursor.fetchall()

        select_game_requirements = f"""
            select gr.platform, r.* 
            from 
            game g inner join game_requirement gr 
            on g.game_id = gr.game_id 
            inner join requirement r 
            on r.req_id = gr.req_id 
            where g.game_id = '{game_id}';
        """

        cursor.execute(select_game_requirements)
        game_requirements = cursor.fetchall()

        check_purchased_game = f"""
        select count(*) from customer c inner join payment p 
        on c.customer_id = p.customer_id 
        inner join purchase pu 
        on pu.payment_id = p.payment_id 
        where 
        c.customer_id = '{session.get("id")}' 
        and pu.game_id = '{game_id}' 
        and pu.purchased_flag = 1;
        """

        cursor.execute(check_purchased_game)
        game_purchased = bool(cursor.fetchone()[-1])
        
        select_game_support = f"""
            select gs.* 
            from 
            game g inner join game_support gs 
            on g.game_id = gs.game_id
            where
            g.game_id = '{game_id}'
        """

        cursor.execute(select_game_support)
        game_support = cursor.fetchone()

        return render_template('game_dashboard.html', game_id=game_id,
        game_details = game_details,
        categories=categories, genres=genres, game_requirements = game_requirements, purchased = game_purchased,
        game_support = game_support)
        
    return redirect(url_for('login'))

@app.route('/cart', methods=['POST', 'GET'])
def cart(added_games=None, payment_id=None, game_id=None):
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    if 'loggedin' in session:

        if request.method == "POST" and "payment" in request.form:
            pay_method = request.form.get("payment")

            place_order_query = f"""
                WITH src AS (
                    UPDATE payment pa
                    SET payment_method = '{pay_method}'
                    FROM purchase pu
                    WHERE pu.payment_id = pa.payment_id and 
                    pa.customer_id = '{session.get("id")}' and 
                    pu.purchased_flag = 0
                    RETURNING pu.payment_id
                    )
                UPDATE purchase dst
                SET purchased_flag = 1
                FROM src
                WHERE dst.payment_id = src.payment_id;
                        ;
                """
            
            cursor.execute(place_order_query)
            db_conn.commit()

        elif request.method == "POST" and 'game_to_delete' in request.form and 'payid_to_delete' in request.form:
            game_id = int(request.form.get("game_to_delete"))
            payment_id = int(request.form.get("payid_to_delete"))
            print(game_id)
            delete_game_order = f"""
                DELETE FROM 
                purchase 
                where 
                game_id = '{game_id}' 
                and payment_id = '{payment_id}'
            """

            cursor.execute(delete_game_order)

            update_purchase = f"""
                UPDATE Payment 
                SET cost = 
                (SELECT 
                coalesce(SUM(g.price), 0)
                FROM
                game g, purchase p 
                where 
                g.game_id = p.game_id 
                and p.payment_id = '{payment_id}' 
                and p.purchased_flag = 0), payment_time = CURRENT_TIMESTAMP
                """
            cursor.execute(update_purchase)
            print("Updated payment")

            delete_payment = f"""
                DELETE FROM payment
                WHERE payment_id = '{payment_id}' 
                and 
                (SELECT cost from payment where payment_id = '{payment_id}') = 0
            """
            cursor.execute(delete_payment)
            db_conn.commit()


        select_added_games = f"""
        select pa.cost, g.game_name, g.price, g.game_id, pa.payment_id 
        from payment pa inner join purchase pu 
        on pu.payment_id = pa.payment_id inner join game g 
        on g.game_id = pu.game_id 
        where 
        pa.customer_id = {session.get("id")} and pu.purchased_flag=0;"""

        cursor.execute(select_added_games)
        added_games_list = cursor.fetchall()
        
        return render_template("cart.html", added_games=added_games_list)

    return redirect(url_for('login'))

@app.route('/logout')
def logout():

   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   session.pop('first', None)

   return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)