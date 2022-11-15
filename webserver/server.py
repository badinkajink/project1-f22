#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy import exc
from sqlalchemy.pool import NullPool
import psycopg2
from flask import Flask, request, render_template, g, redirect, Response
from flask import Blueprint
import re


# blueprint = Blueprint('custom_template_filters, __name__)
# def register_template_filters(flask_app: Flask) -> None:
#     flask_app.register_blueprint(blueprint)
#     return None

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
# register_template_filters(flask_app=app)

# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "wx2214"
DB_PASSWORD = "0366"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"
search_result = []
query = ""
passphrase = "admin"
loggedin = False
error = False
database = {}

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

# https://stackoverflow.com/questions/18662898/jinja-render-text-in-html-preserving-line-breaks
@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def root():
  return redirect('/write')


# very crude login page via:
# https://www.reddit.com/r/flask/comments/k1bvw4/password_protect_pages/
def password_prompt(message):
    return f'''
                <form action="/write" method='post'>
                  <label for="password">{message}:</label><br>
                  <input type="password" id="password" name="password" value=""><br>
                  <input type="submit" value="Submit">
                </form>'''

def get_data():
  global database
  cursor = g.conn.execute("SELECT * FROM Shelter")
  shelters = list(cursor)
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Animal")
  animals = list(cursor)
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Intake")
  intakes = list(cursor)
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Location")
  locations = list(cursor)
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Outcome")
  outcomes = list(cursor)
  cursor.close()

  database = {"shelters": shelters, "animals": animals, "intakes": intakes, "locations": locations, "outcomes": outcomes, "searchresult": search_result}

@app.route('/write', methods=['GET', 'POST'])
def write():
  global loggedin
  global database
  get_data()
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
  print(request.method)
  if not loggedin:
    if request.method == 'GET':
        return password_prompt("Admin password:")
    elif request.method == 'POST':
        if request.form['password'] != passphrase:
            return password_prompt("Invalid password, try again. Admin password:")
        else:
          loggedin = True
      
  # DEBUG: this is debugging code to see what request looks like
  print(request.args)
  # example of a database query
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    print(result)
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Location")
  zipcodes = []
  for result in cursor:
    print(result)
    zipcodes.append(result['zipcode'])  
  cursor.close()
  # context = dict(data = n)

  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  context = dict(data = {"animalnames": names, "zipcodes": zipcodes})
  print(context)

  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

@app.route('/search')
def search():
  global search_result
  global query
  print(query)
  cursor = g.conn.execute("SELECT * FROM Shelter")
  shelters = list(cursor)
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Animal")
  animals = list(cursor)
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Intake")
  intakes = list(cursor)
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Location")
  locations = list(cursor)
  cursor.close()

  cursor = g.conn.execute("SELECT * FROM Outcome")
  outcomes = list(cursor)
  cursor.close()

  print(search_result)
  context = dict(data = {"shelters": shelters, "animals": animals, "intakes": intakes, "locations": locations, "outcomes": outcomes, "searchresult": search_result, "query": query})

  return render_template("search.html", **context)

# Example of adding new data to the database
@app.route('/submitsearch', methods=['POST'])
def submitsearch():
  global search_result
  global query
  dict = request.form
  keys = request.form.keys()
  print(keys)
  # print(request.form.values)
  query_dict = {}
  for k in keys:
    if dict[k] != 'Any':
      query_dict[k] = 'a'
  psycopg2.paramstyle = 'named'
  query = f"""SELECT distinct a.AnimalName, a.AnimalID, s.Sheltername, a.animaltype, a.animalsex, i.zipcode, i.intakeCondition, a.age
  FROM Animal as a
  INNER JOIN Shelter as s ON a.shelterid=s.shelterid
  INNER JOIN Intake as i ON a.animalid=i.animalid
  INNER JOIN Outcome as o ON a.animalid=o.animalid
  WHERE a.AnimalSex {"LIKE '%Female%'" if dict['animalsex'] == "Female" else ''} {"LIKE '% Male%'" if dict['animalsex'] == "Male" else ''} {"IS NOT NULL" if dict['animalsex'] == 'Any' else ''}
  AND s.ShelterName {"IS NOT NULL" if dict['sheltername'] == 'Any' else f"= '{dict['sheltername']}'"}
  AND a.AnimalType {"IS NOT NULL" if dict['animaltype'] == 'Any' else f"= '{dict['animaltype']}'"}
  AND i.zipcode {"IS NOT NULL" if dict['zipcode'] == 'Any' else f"= '{dict['zipcode']}'"}
  AND i.intakecondition {"IS NOT NULL" if dict['intakecondition'] == 'Any' else f"= '{dict['intakecondition']}'"}
  AND {"o.outcomesubtype IS NOT NULL" if dict['outcomesubtype'] == 'Any' else f"o.outcomesubtype = '{dict['intakecondition']}'"}
  """
  print(query)
  cursor = g.conn.execute(text(query))
  result = list(cursor)
  cursor.close()
  print(result)
  search_result = result
  return redirect('/search')

def check_existence(table, idname, id):
  # check existence
  cmd = f'SELECT COUNT(1) FROM {table} WHERE {idname} = :{idname}'
  exists = 0
  try:
    cursor = g.conn.execute(text(cmd), idname = id)
    exists = cursor.fetchall()[0][0]
    cursor.close()
    return exists
  except exc.SQLAlchemyError as e:
    print(e)
    return render_template('error.html')

@app.route('/addShelter', methods=['POST'])
def addShelter():
  global database
  ShelterID = request.form['ShelterID']
  print(ShelterID)
  ShelterLoc = request.form['ShelterLoc']
  print(ShelterLoc)
  Zip = request.form['Zip']
  print(Zip)
  Name = request.form['Name']
  print(Name)
  
  # check existence
  exists = check_existence("Shelter", "ShelterID", ShelterID)

  if not exists:
    cmd = 'INSERT INTO Shelter VALUES (:ShelterID, :ShelterLoc,:ShelterZip,:ShelterName);'
    try:
      g.conn.execute(text(cmd), ShelterID=ShelterID, ShelterLoc=ShelterLoc, ShelterZip=Zip, ShelterName=Name) 
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      print(e)
      if e == psycopg2.errors.UniqueViolation:
        print("yes")
      return render_template('error.html')
  else:
    cmd = f'UPDATE Shelter SET ShelterLoc= :ShelterLoc, ShelterZip= :ShelterZip, ShelterName= :ShelterName WHERE ShelterID={ShelterID};'
    try:
      g.conn.execute(text(cmd), ShelterLoc=ShelterLoc, ShelterZip=Zip, ShelterName=Name) 
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      print(e)
      return render_template('error.html')   

@app.route('/addAnimal', methods=['POST'])
def addAnimal():
  ShelterID = request.form['ShelterID']
  AnimalID = request.form['AnimalID']
  print(AnimalID)
  AnimalName = request.form['AnimalName']
  print(AnimalName)
  Type = request.form['Type']
  print(Type)
  Sex = request.form['Sex']
  print(Sex)
  Age = request.form['Age']

  # check existence
  exists = check_existence("Animal", "AnimalID", AnimalID)

  if not exists:
    cmd = 'INSERT INTO Animal VALUES (:ShelterID, :AnimalID, :AnimalName,:AnimalType,:AnimalSex,:Age);'
    try:
      g.conn.execute(text(cmd), ShelterID=ShelterID, AnimalID =AnimalID, AnimalName= AnimalName, AnimalType = Type, AnimalSex = Sex, Age=Age) 
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      print(e)
      return render_template('error.html')
  else:
    cmd = f'UPDATE Animal Set ShelterID=:ShelterID, AnimalName=:AnimalName, AnimalType=:AnimalType, AnimalSex=:AnimalSex, Age=:Age WHERE AnimalID=:AnimalID;'
    try:
      g.conn.execute(text(cmd), AnimalID=AnimalID, ShelterID=ShelterID, AnimalName= AnimalName, AnimalType = Type, AnimalSex = Sex, Age=Age) 
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      print(e)
      return render_template('error.html')   

@app.route('/addIntake', methods=['POST'])
def addIntake():
  IntakeID = request.form['IntakeID']
  print(IntakeID)
  AnimalID = request.form['AnimalID']
  print(AnimalID)
  IntakeDate = request.form['IntakeDate']
  IntakeCondition = request.form['IntakeCondition']
  zipcode = request.form['zipcode']

  exists = check_existence("Intake", "IntakeID", IntakeID)

  if not exists:
    cmd = 'INSERT INTO Intake VALUES (:AnimalID, :IntakeID, :IntakeDate, :IntakeCondition, :zipcode);'
    try:
      g.conn.execute(text(cmd), AnimalID=AnimalID, IntakeID = IntakeID, IntakeDate=IntakeDate, IntakeCondition=IntakeCondition, zipcode=zipcode) 
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      print(e)
      return render_template('error.html')
  else:
    cmd = 'UPDATE Intake Set AnimalID=:AnimalID, IntakeDate=:IntakeDate, IntakeCondition=:IntakeCondition, zipcode=:zipcode WHERE IntakeID=:IntakeID;'
    try:
      g.conn.execute(text(cmd), AnimalID=AnimalID, IntakeID = IntakeID, IntakeDate=IntakeDate, IntakeCondition=IntakeCondition, zipcode=zipcode) 
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      print(e)
      return render_template('error.html')


@app.route('/addLocation', methods=['POST'])
def addLocation():
  print(request.form)
  Location = request.form['location']
  print(Location)
  LocationAddress = request.form['address']
  print(LocationAddress)

  exists = check_existence("Location", "Location", Location)

  if not exists:
    cmd = 'INSERT INTO Location VALUES (:location, :address);'
    try:
      g.conn.execute(text(cmd), location = Location, address= LocationAddress)
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      error = True
      print(e)
      return render_template('error.html')
  else:
    cmd = 'UPDATE Location SET Address= :address WHERE zipcode=:location;'
    try:
      g.conn.execute(text(cmd), location = Location, address= LocationAddress)
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      error = True
      print(e)
      return render_template('error.html')

@app.route('/addOutcome', methods=['POST'])
def addOutcome():
  AnimalID = request.form['AnimalID']
  OutcomeID = request.form['OutcomeID']
  print(OutcomeID)
  OutcomeDate = request.form['OutcomeDate']
  print(OutcomeDate)
  Subtype = request.form['OutcomeSubtype']
  print(Subtype)
  
  exists = check_existence("Outcome", "OutcomeID", OutcomeID)

  if not exists:
    cmd = 'INSERT INTO Outcome VALUES (:AnimalID, :OutcomeID, :OutcomeDate, :OutcomeSubtype);'
    try:
      g.conn.execute(text(cmd), AnimalID=AnimalID, OutcomeID=OutcomeID, OutcomeDate = OutcomeDate, OutcomeSubtype=Subtype) 
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      error = True
      print(e)
      return render_template('error.html')
  else:
    cmd = 'UPDATE Outcome Set AnimalID=:AnimalID, OutcomeDate=:OutcomeDate, OutcomeSubtype=:OutcomeSubtype WHERE OutcomeID=:OutcomeID;'
    try:
      g.conn.execute(text(cmd), AnimalID=AnimalID, OutcomeID=OutcomeID, OutcomeDate = OutcomeDate, OutcomeSubtype=Subtype) 
      return redirect('/search')
    except exc.SQLAlchemyError as e:
      error = True
      print(e)
      return render_template('error.html')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
