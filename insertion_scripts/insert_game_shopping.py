import datetime
from aem import con
from appscript import app
import psycopg2
import random
import pandas as pd
import config

def insert_customers(connection, cursor):

    customers = pd.read_csv("customer.csv")
    
    for i, customer in customers.iterrows():
        query = f"""
        INSERT INTO 
        Customer 
        (customer_id, first_name, last_name, contact_number, email, DOB, Password) 
        values 
        ('{customer['customer_id']}',
        '{customer['first_name'].replace("'", '"').strip()}',
        '{customer['last_name'].replace("'", '"').strip()}',
        '{customer['contact_number']}', 
        '{customer['email']}', 
        '{customer['DOB']}', 
        '{customer['Password']}');
        """

        cursor.execute(query)
        connection.commit()

def insert_games(connection, cursor):

    games = pd.read_csv("steam-1.csv")
    game_descs = pd.read_csv("steam_description_data-1.csv")
    game_support = pd.read_csv("steam_support_info-1.csv")
    game_reviews = pd.read_csv("reviews.csv")

    games_data = pd.merge(games, game_descs, left_on='appid', right_on='steam_appid')
    games_data = pd.merge(games_data, game_support, left_on='appid', right_on='steam_appid')

    
    for i, game in games_data.iterrows():
        # Insert inton game table
        game_query = f"""
        INSERT INTO 
        Game 
        (game_id, game_name, developer, publisher, age_rating, price, synopsis, release_date) 
        values 
        ('{game['appid']}',
        '{game['name'].replace("'", '"').strip()}',
        '{game['developer'].replace("'", '"').strip()}',
        '{game['publisher'].replace("'", '"').strip()}', 
        '{game['required_age']}', 
        '{game['price']}', 
        '{game['detailed_description'].replace("'", '"').strip()}',
        '{game['release_date']}');
        """

        cursor.execute(game_query)

        # Insert into game_genre and game_category table
        genres = game['genres'].split(";")
        categories = game["categories"].split(";")

        for genre in genres:
            genre_query = f"""
            INSERT INTO
            game_genre
            (game_id, genre)
            values
            ('{game['appid']}', '{genre.replace("'", '"').strip()}')
            """

            cursor.execute(genre_query)
        
        for category in categories:
            category_query = f"""
            INSERT INTO
            game_category
            (game_id, category)
            values
            ('{game['appid']}', '{category.replace("'", '"').strip()}')
            """

            cursor.execute(category_query)    

        # Insert into game_review table

        game_review = game_reviews[game_reviews["app_id"] == game["appid"]]

        for i, review in game_review.iterrows():
            next_id = """select nextval('review_seq')"""
            
            cursor.execute(next_id)
            review_id = cursor.fetchone()
            review_id = int(review_id[-1])

            if review["review_score"] == -1:
                score = random.choice(range(0, 3))
            else:
                score = random.choice(range(3, 6))
            
            downvotes = random.choice(range(0,1000))
            upvotes = random.choice(range(100,100000))

            if not isinstance(review['review_text'], float):
                review = str(review['review_text']) 
            else:
                review = ''

            review_query = f"""
                INSERT INTO Review
                (Review_ID, Score, Comment, no_of_upvotes, no_of_downvotes)
                VALUES
                ('{review_id}', '{score}', '{review.replace("'", '"').strip()}', 
                '{upvotes}', '{downvotes}')
            """
            cursor.execute(review_query)

            customer = random.choice(range(1, 1001))

            game_review_query = f"""
            INSERT INTO Game_Review
            (game_id, customer_id, review_id)
            VALUES
            ('{game['appid']}', '{customer}', '{review_id}')
            """

            cursor.execute(game_review_query)

        # Insert into game_support table
        if not isinstance(game['website'], float):
            website = str(game['website']) 
        else:
            website = ''
        if not isinstance(game['support_url'], float):
            url = str(game['support_url'])
        else:
            url = ''
        if not isinstance(game['support_email'], float):
            email = str(game["support_email"])
        else:
            email = ''

        game_support_query = f"""
        INSERT INTO 
        game_support
        (game_id, website, support_url, support_email)
        values
        ('{game['appid']}', 
        '{website.replace("'", '"').strip()}', 
        '{url.replace("'", '"').strip()}', 
        '{email.replace("'", '"').strip()}')
        """

        cursor.execute(game_support_query)

        connection.commit()
    
    return pd.unique(games_data['appid']).tolist()

def insert_payment_details(conn, cursor, appid):
    
    for i in range(1000):
        customer_id = random.choice(range(1, 1001))
        payment_id_query = """SELECT nextval('payment_seq')"""

        cursor.execute(payment_id_query)
        payment_id = cursor.fetchone()
        payment_id = int(payment_id[-1])
        
        payment_types = ['Credit/Debit Card', 'BitCoin', 'Paypal', 'Store Credit']
        payment_type = random.choice(payment_types)

        payment_query = f"""
        INSERT INTO payment
        (payment_id, customer_id, cost, payment_method)
        VALUES
        ('{payment_id}', '{customer_id}', '0.0',  '{payment_type}')
        """

        cursor.execute(payment_query)

        no_of_games = random.choice(range(1, 6))

        for j in range(no_of_games):
            rand_app = random.choice(appid)
            
            purchase_query = f"""
            INSERT INTO purchase
            (payment_id, game_id)
            VALUES
            ('{payment_id}', '{rand_app}')
            """

            cursor.execute(purchase_query)
        
        total_price_query = f"""
        SELECT 
        SUM(g.price) 
        FROM
        game g, purchase p 
        where 
        g.game_id = p.game_id and p.payment_id = '{payment_id}'
        """

        cursor.execute(total_price_query)

        total_price = cursor.fetchone()
        total_price = int(total_price[-1])

        update_payment_query = f"""
        UPDATE Payment SET cost = '{total_price}', payment_time = CURRENT_TIMESTAMP
        """

        cursor.execute(update_payment_query)

    
    conn.commit()

def randomtimes(start, end):
    frmt = '%Y-%m-%d %H:%M:%S'
    stime = datetime.datetime.strptime(start, frmt)
    etime = datetime.datetime.strptime(end, frmt)
    td = etime - stime
    return random.random() * td + stime

def insert_stats_data(connection, cursor, appid):

    for i in range(5001):
        hours_played = random.choice(range(1, 800))
        ingame_amt = random.choice(range(0, 500))
        customer = random.choice(range(1, 1001))
        app = random.choice(appid)
        last_played = randomtimes('2000-01-01 00:00:00', '2022-04-25 00:00:00')
        
        stats_id_query = f"""select nextval('stats_seq')"""
        
        cursor.execute(stats_id_query)
        stats_id = cursor.fetchone()
        stats_id = int(stats_id[-1])

        stats_query = f"""
        INSERT INTO Stats
        (stats_id, hours_played, last_played, ingame_purchase_amt)
        VALUES
        ('{stats_id}', '{hours_played}', '{last_played}', '{ingame_amt}')
        """

        cursor.execute(stats_query)

        game_stats_query = f"""
        INSERT INTO Game_Stats
        (game_id, customer_id, stats_id)
        VALUES
        ('{app}', '{customer}', '{stats_id}')
        """

        cursor.execute(game_stats_query)
    
    connection.commit()
    
def insert_achievements_data(connection, cursor, appid):
    achievements = pd.read_csv("achievements.csv")
    for i in range(5001):
        badge = random.choice(['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'])
        customer = random.choice(range(1, 1001))
        app = random.choice(appid)
        achievement = random.choice(achievements['Achievements'])
        
        achieve_id_query = f"""select nextval('achieve_seq')"""
        
        cursor.execute(achieve_id_query)
        achieve_id = cursor.fetchone()
        achieve_id = int(achieve_id[-1])

        achieve_query = f"""
        INSERT INTO Achievements
        (achieve_id, title, badge)
        VALUES
        ('{achieve_id}', '{achievement.replace("'", '"').strip()}', '{badge}')
        """

        cursor.execute(achieve_query)

        game_achieve_query = f"""
        INSERT INTO Game_Achievements
        (game_id, customer_id, achieve_id)
        VALUES
        ('{app}', '{customer}', '{achieve_id}')
        """

        cursor.execute(game_achieve_query)
    
    connection.commit()
    
def insert_game_requirements(conn, cursor, appid):
    cpus = pd.read_csv("cpu.csv")
    gpus = pd.read_csv("gpu.csv")

    for app in appid:
        min_mem = random.choice(range(2, 17, 2))
        min_storage = random.choice(range(200, 900))
        min_cpu = random.choice(cpus["Name"])
        min_gpu = random.choice(gpus["ProductName"])

        rec_mem = random.choice(range(min_mem, 20, 2))
        rec_storage = random.choice(range(min_storage, 1000))
        rec_cpu = min_cpu
        rec_gpu = min_gpu

        require_id_query = f"""select nextval('requirements_seq')"""
        
        cursor.execute(require_id_query)
        require_id = cursor.fetchone()
        require_id = int(require_id[-1])

        requirements_query = f"""
        INSERT INTO Requirement
        (Req_ID, min_memory, rec_memory, min_GPU, rec_GPU, min_storage, rec_storage, min_CPU, rec_CPU)
        VALUES
        ('{require_id}', '{min_mem}', '{rec_mem}', '{min_gpu}',
        '{rec_gpu}', '{min_storage}', '{rec_storage}', '{min_cpu}', '{rec_cpu}')
        """

        cursor.execute(requirements_query)

        game_requirements_query = f"""
        INSERT INTO game_requirement
        (req_id, game_id, platform)
        VALUES
        ('{require_id}', '{app}', 'PC')
        """

        cursor.execute(game_requirements_query)
    
    conn.commit()

if __name__ == "__main__":
    connection = psycopg2.connect(**config.POSTGRES_CONFIG)
    cursor = connection.cursor()

    insert_customers(connection, cursor)
    appid = insert_games(connection, cursor)

    insert_payment_details(connection, cursor, appid)
    insert_stats_data(connection, cursor, appid)
    insert_achievements_data(connection, cursor, appid)
    insert_game_requirements(connection, cursor, appid)

    connection.close()