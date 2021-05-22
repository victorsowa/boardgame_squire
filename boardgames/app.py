import sys
import os

import flask

folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, folder)

import boardgames.data.db_session as db_session
import boardgames.services.filtered_games_service as fgs
from boardgames.services.collection_service import add_new_users_collection_to_db

app = flask.Flask(__name__)


def main():
    setup_db()
    add_new_users_collection_to_db('bobbaganush')
    app.run(debug=True)


def setup_db():
    db_file = os.path.join(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'db',
            'db.sqlite'
        )
    )
    print(db_file)
    db_session.global_init(db_file)


@app.route('/', methods=['GET'])
def index_get():
    return flask.render_template('index.html')


@app.route('/user_collection/<username>', methods=['GET'])
def index_get():
    return flask.render_template('user_collection.html', images=fgs.get_games())





if __name__ == '__main__':
    #DEBUG is SET to TRUE. CHANGE FOR PROD
    main()
