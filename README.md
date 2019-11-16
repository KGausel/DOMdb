# DOMdb
An in-memory datastore leveraging the powerful V8 engine and python

Warning: This project is a joke
This project won the "Hacking Stupid" category during Aarhack in November 2019

# Getting started

## Installing
1. Install Chrome and the ChromeDriver (can be found [here](https://sites.google.com/a/chromium.org/chromedriver/downloads))
2. Put the ChromeDriver in your `PATH`
3. Install Python 3.5+ (has only been tested with Python 3.8)
4. Install the python dependencies using `pip install -r requirements.txt`

## Running the project
There is a demo included in the code. This can be run with
```
python domdb.py --debug --demo
```
(This project is most fun when run with `--debug` as you can see the browser we use to store data in)


Cool commands to try in the REPL:
```
TABle("tablename")  -- opens a new TABle or navigates to an existing TABle
insert({"anything": "goes here"})  -- inserts data into the database
delete_object("domXXXXXXX")  -- deletes a document from the database
snapshot("saveto.png", pixelbytes=3000)  -- create a snapshot of 3000 pixelbytes
DOMp("saveto.html") -- DOMps the database to a file
TABle("restored", seedpath="saveto.html") -- restore a database from a DOMp file
query('p[type="string"]')  -- query the database, this one selects all primitives of type string (play around with CSS selectors here)
pquery("div[id]")  -- like query, but instead of returning the result it pretty-prints it
```