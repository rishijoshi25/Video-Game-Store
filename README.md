# Video-Game-Store
<pre>
1. Instructions to create tables and insert data into the relations

    I. Table Creation - Run all the scripts in the file create_script.txt inside pgadmin.

    II. Insert data into relations
            a. Go to insertion_scripts 
            b. Run the script insert_game_shopping.py
            c. Will take more than half an hour to complete the insertion.

2. Data files inside insertion_scripts
Apart from random values generated as a part of python script, we use the following CSV files as the datasets for insertion - 
    a. customer.csv - Dataset contaning personal information of customers
    b. cpu.csv - CPU information dataset used for random insertions
    c. gpu.csv - GPU information dataset used for random insertions
    d. achievements.csv - Dataset with Achievements (containing title)
    e. reviews.csv - Dataset contaning the review of the games
    f. steam_description_data-1.csv, steam-1.csv - Dataset containing information about all the games
    g. steam_support_info-1.csv - Dataset contaning the support information for the games

3. Steps to run the UI application
	I. Navigate to ui_app
	II. Configure Flask application
		a. export FLASK_APP=game_app
		b. export FLASK_DEBUG=1  ton enable debugging mode (No need to rerun after making changes)
	III. Run python script game_app.py (python game_app.py)
	IV. Go to link localhost:5000

4. Add configuration information for postgres
    I. Go to config.py in case of both insertion and UI application
    II. Enter the details for the variables such as - 
        a. user - For username used to access pgadmin
        b. password - Password used to access the database in pgadmin
        c. host - Host where the database is accessed from
        d. port - Post used to access the database
        e. database - Database name
</pre>
