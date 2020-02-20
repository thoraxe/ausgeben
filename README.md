# Ausgeben - giving tickets for workshops
Do you have some kind of use case for distributing simple users, passwords,
and arbitrary other information? Well, Ausgeben might be able to help you.

## Installation
requirements.txt
Other python venv things
Flasky flask

## Usage
1. Create a CSV file with the following format:

        username,password,urls_json_blob
        user1,password,
        user2,password,
        user3,password,

1. POST the CSV file to the `load_csv_data` endpoint:

        curl -F "file=@userdata.csv" http://ausgeben.url:5000/load_csv_data

    **Note:** There is no protection for uploading the file. If you upload it
    *again, you blow away any existing claims stored in the SQLite3 DB.

1. Send users to `/` and then they can click the link to retrieve the information

Ausgeben stores a cookie in the user's browser and will always send them the
same information. The third field, `urls_json_blob` can be filled with an
arbitrary JSON string. Python's `json2html` is used to convert everything to
a nice table to display to the end user. At this time, links are not rendered
as click-able.