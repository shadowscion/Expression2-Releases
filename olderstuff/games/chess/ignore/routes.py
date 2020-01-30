
from sunfish import getAIMove as get_move_sf
from sunfish import selfPlay as get_aigame_sf
from hexchess import getAIMove as get_move_hex

from pool import runsim as runsim

from flask import Flask, render_template, request

app = Flask(__name__)

gametypes = {
	"stdchess" : get_move_sf,
	"stdaivai" : get_aigame_sf,
}

@app.route("/ai", methods=["GET"])
def ai():
	try:
		if request.method == "GET":
			game = request.args.get("game")
			user = request.args.get("input")

			if game in gametypes:
				return gametypes[game](user)
			else:
			    raise ValueError("Invalid gametype")

	except Exception as e:
		return "ERROR: " + str(e)


@app.route("/")
def home():
	return render_template("home.html")


if __name__ == "__main__":
    app.run()
