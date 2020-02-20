import os

from flask import Flask, request, json, render_template, make_response
from json2html import *
import pandas as pd
import sqlite3

UPLOAD_FOLDER = 'tmp/'
ALLOWED_EXTENSIONS = {'csv'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    # https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/#uploading-files
    # restrict files to CSVs
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    conn = sqlite3.connect("database.db")

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
    resp = make_response(json2html.convert(json = json_response))
    resp.set_cookie('username', user[0][0])
    return resp


@app.route('/load_csv_data', methods=['POST'])
def load_csv_data():
    if 'file' not in request.files:
        response = app.response_class(
            response=json.dumps({'status':'error: no file found'}),
            status=500,
            mimetype='application/json'
        )
        return response
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        response = app.response_class(
            response=json.dumps({'status':'error: no filename'}),
            status=500,
            mimetype='application/json'
        )
        return response
    if file and allowed_file(file.filename):
        filename = 'userdata.csv'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # establish the sqlite3 database from the file
        # there is no protection from overwriting
        conn = sqlite3.connect('tmp/database.db')
        df=pd.read_csv('tmp/userdata.csv')

        # add a "claimed" field and initialize it to false
        df['claimed'] = False
        df.to_sql('userinfo',conn, if_exists='replace', index=False)

        response = app.response_class(
            response=json.dumps({'status':'file uploaded'}),
            status=200,
            mimetype='application/json'
        )
        return response


app.run(debug=True, host='0.0.0.0', port=8080)
