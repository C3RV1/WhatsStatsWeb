import base64
import hashlib
import json
import random
import shutil
import struct
import time
import datetime

from game import Game

from flask import Flask, redirect, url_for, render_template, request
import os

random.seed(time.time())
UPLOAD_FOLDER = './uploaded_games'
ALLOWED_EXTENSIONS = {'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
games = {}
START_DATE = None


# TODO: Auto remove after some time
# TODO: Individual player stats (per hours...)
# TODO: Choose start_date and end_date from webpage


@app.route("/")
def index():
    return render_template("index.html.jinja")


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('index'))
        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('index'))
        if file:
            while True:
                filename = base64.b64encode(struct.pack("I", random.randint(0, 10000))).decode("ascii")
                filename = filename.replace("/", "_")
                if not os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                    break
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open(os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.json"), "w") as json_file:
                json_data = json.dumps({
                    "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "name": ".".join(file.filename.rsplit(".")[:-1])
                })
                json_file.write(json_data)
            return redirect(url_for('visualize_data', game_id=filename))
    return redirect(url_for('index'))


@app.route('/visualize/<game_id>')
def visualize_data(game_id):
    game = get_game(game_id)
    if game is None:
        return redirect(url_for("index"))
    return render_template("visualize.html.jinja", id=game_id, game_name=game.name)


def get_game(game_id) -> Game:
    if game_id not in games:
        g = Game()
        path = os.path.join(app.config['UPLOAD_FOLDER'], game_id)
        if not os.path.isfile(path):
            return None
        msg_count = 0
        with open(f"{path}.json", "r") as json_file:
            json_data = json.loads(json_file.read())
            g.name = json_data["name"]
        if os.path.isfile(f"./base_chats/{g.name}.txt"):
            with open(f"./base_chats/{g.name}.txt", "rb") as base_game:
                for line in base_game.readlines():
                    line = line.decode("utf-8")
                    if g.process_line(line):
                        msg_count += 1
        with open(path, "rb") as game:
            for line in game.readlines():
                line = line.decode("utf-8")
                if g.process_line(line):
                    msg_count += 1
        print(f"Analysed game {g.name} with {msg_count} messages")
        games[game_id] = g
    return games[game_id]


@app.route("/clear", methods=["GET"])
def clear():
    secret = request.args.get("secret", None)
    if secret is None:
        return redirect(url_for('index'))
    if not hashlib.sha256(secret.encode("utf-8")).digest() == b'\xff\xd9F(2\x19\xb6\xde\xc8pQ\xbe\xd9\xb3\xca\xdf\xfd\xfd\xe6\x0f\xa9\x86\x90\xc0,\x90\xb8\xe6<\\/\xe8':
        return redirect(url_for('index'))
    do_clear()
    return '<html><body><h1>Games deleted</h1></body></html>'


def do_clear():
    global games
    games = {}
    if os.path.isdir("uploaded_games"):
        shutil.rmtree("uploaded_games")
    os.mkdir("uploaded_games")


@app.route("/loadGame", methods=["POST"])
def load_game():
    method = request.form.get("api-method", None)
    game_id = request.form.get("game-id", None)
    if method is None or game_id is None:
        return {}
    g: Game = get_game(game_id)
    if g is None:
        return {}
    print(f"Requested {method} for game with id {game_id} ({g.name})")
    if method == "get-counts":
        return g.construct_counts(start_date=START_DATE)
    elif method == "get-common-hour":
        player_name = request.form.get("player-name", None)
        if player_name is None:
            return {}
        hour = g.get_player_hour(player_name, start_date=START_DATE)
        return hour
    return {}


if __name__ == '__main__':
    do_clear()
    app.run(debug=True, host="0.0.0.0")
