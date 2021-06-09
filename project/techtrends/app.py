import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

db_connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    incrementConnectionCount()    
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    incrementConnectionCount()
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.error('No article with the following id: %s', post_id)
      return render_template('404.html'), 404
    else:
      app.logger.info('Article "%s" retrieved', post['title'])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('"About Us" page is retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            incrementConnectionCount()
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info('New Article created with title: "%s"', title)

            return redirect(url_for('index'))

    return render_template('create.html')

# Define healthz check endpoint
@app.route('/healthz')
def healthz():
    return {"result": "OK - healthy"}

@app.route('/metrics')
def metrics():
     return {"db_connection_count": db_connection_count, "post_count": get_post_count()}

def get_post_count():
    connection = get_db_connection()
    count = connection.execute('SELECT COUNT(id) FROM posts').fetchone()[0]
    connection.close()
    return count

def incrementConnectionCount():
    global db_connection_count
    db_connection_count += 1

@app.errorhandler(404)
def resource_not_found(e):
    app.logger.error('Page not found - 404')
    return 'Page not found - 404', 404

def initLogger():
    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stderr = logging.StreamHandler(sys.stderr)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[handler_stdout, handler_stderr],
        format='%(levelname)s:%(name)s:%(asctime)s, %(message)s',
        datefmt='%m/%d/%Y, %H:%M:%S')

# start the application on port 3111
if __name__ == "__main__":
   # configure logging
   initLogger()
   # start flask app
   app.run(host='0.0.0.0', port='3111')
