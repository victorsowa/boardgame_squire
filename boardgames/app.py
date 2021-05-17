import sys
import os

import flask

folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, folder)

import boardgames.data.db_session as db_session

app = flask.Flask(__name__)


def main():
    setup_db()
    app.run(debug=True)


def setup_db():
    db_file = os.path.join(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'db',
            'boardgames.sqlite'
        )
    )
    print(db_file)
    db_session.global_init(db_file)


@app.route('/', methods=['GET'])
def index_get():
    return flask.render_template('index.html')


if __name__ == '__main__':
    #DEBUG is SET to TRUE. CHANGE FOR PROD
    main()
