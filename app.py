import os

from flask import (g, Flask, request, json, render_template, make_response)
from json2html import *
import pandas as pd
import sqlite3

UPLOAD_FOLDER = 'tmp/'
ALLOWED_EXTENSIONS = {'csv'}
DB_FILENAME = 'tmp/database.db'


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def hello_world():
    # here we should show the user a button to allow them to fetch a user
    # we don't want to send them directly to /get_user because it may take time to
    # handle sqlite3 database locking with a lot of people doing the same thing
    # at the same time
    return render_template('hello.html')


@app.route('/get_user')
def get_user():
    # fetch username from cookie
    username = request.cookies.get('username')

    # establish a connection to the database
    conn = get_db()

    # if there's no username in the cookie, fetch a user
    if username is None:
        # grab the first user that is not claimed
        # user ends up being an array with a single tuple inside
        # the database columns are username,password,urls_json_blob,claimed
        # user[0] is the only value returned and user[0][0] is the first column, which is the username
        user = conn.execute("SELECT * FROM userinfo WHERE claimed='0' LIMIT 1").fetchall()
    
        # immediately claim the user
        conn.execute("UPDATE userinfo SET claimed=1 WHERE username='%s'" % user[0][0])
        conn.commit()

        # close the database connection to be friendly to others
        conn.close()

    else:
        # the user had a cookie, so re-fetch the same information
        user = conn.execute("SELECT * FROM userinfo WHERE username='%s'" % username).fetchall()

        # close the database connection to be friendly to others
        conn.close()

    # build some happy JSON to convert to show the user
    username = user[0][0]
    password = user[0][1]
    json_additional = user[0][2]

    user_password_dict = {'Username': username, 'Password': password}

    if json_additional is not None:
        json_additional_dict = json.loads(json_additional)
        json_response = dict(user_password_dict, **json_additional_dict)
    else:
        json_response = user_password_dict

    # build a response object before setting cookies
    resp = make_response(json2html.convert(json=json_response))
    resp.set_cookie('username', user[0][0])
    return resp


@app.route('/load_csv_data', methods=['POST'])
def load_csv_data():
    if 'file' not in request.files:
        response = app.response_class(
            response=json.dumps({'status': 'error: no file found'}),
            status=400,
            mimetype='application/json'
        )
        return response
    file = request.files['file']

    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        response = app.response_class(
            response=json.dumps({'status': 'error: no filename'}),
            status=400,
            mimetype='application/json'
        )
        return response

    if not is_allowed_file(file.filename):
        response = app.response_class(
            response=json.dumps({'status': 'error: invalid filename'}),
            status=400,
            mimetype='application/json'
        )
        return response

    filename = 'userdata.csv'
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = get_db()
    df = pd.read_csv('tmp/userdata.csv')

    # Add extra fields to initialize in the database
    df['claimed'] = False

    # Populate the database with all of the users, re-creating the table if found
    df.to_sql('userinfo', conn, if_exists='replace', index=False)

    response = app.response_class(
        response=json.dumps({'status': 'file uploaded'}),
        status=200,
        mimetype='application/json'
    )
    return response


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_FILENAME)
    return db



@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def is_allowed_file(filename):
    # https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/#uploading-files
    # restrict files to CSVs
    is_valid = '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if not is_valid:
        # replace with a logging framework eventually
        print('Filename [%s] is not valid' % filename)

    return is_valid


app.run(debug=True, host='0.0.0.0', port=8080)
