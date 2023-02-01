import threading
from time import sleep
from flask import Flask, render_template
from flask import jsonify, request, session
from flask_sock import Sock
from skimmer import cSkimmer

app = Flask(__name__)
app.secret_key = 'BAD_SANTA'
sock = Sock(app)
app.config.from_pyfile('skimmerwebapp.cfg')
skimmer = cSkimmer(app.config)


@app.before_first_request
def start_skimmer():
    #kick off main skcc skimmer script
    skimmer.run()

    #kick off parsing thread
    t = threading.Thread(target=skimmer.read)
    t.start()
    print("read started")


@app.route("/")
def index():
    """Getting this route will make the skimmer immediately resend the spots
    and skeds.
    """
    skimmer.force_refresh()
    return render_template('index.html')


@app.route('/getstatus')
def get_status():
    """Gets the status of the SKCC Skimmer background application (at startup).
    
    This method gets all the text output lines of the skimmer during it's initial
    startup period. Afterwards it serves no function.
    """
    s = skimmer.get_status()
    j = s.get_lines()
    return jsonify(j)

@app.route('/clearspots')
def clear_spots():
    """Allow user to clear the current list of RBN spots.
    
    Returns "nothing" str
    """
    skimmer.clear_spots()
    return "nothing"

@app.route('/save/', methods=['POST'])
def save():
    """Allows a user to save a thingy"""
    data = request.get_json()
    print(data)
    if not session.get('stored_spots'):
        session['stored_spots'] = []

    session['stored_spots'].append(data)
    session.modified = True

    return jsonify(success=True)

@app.route('/load', methods=['GET'])
def load():
    """Allows a user to save a thingy"""
    if not session.get('stored_spots'):
        return jsonify(success=False, message='no stored spots')

    print('load' + str(session['stored_spots']))
    return jsonify(session['stored_spots'])


@sock.route('/getskedsws')
def get_skeds_ws(ws):
    """Provide a websocket connection that continually sends the current list of
    skeds.
    
    This loops forever and delays based on the app.config 'SKED_TIME' 
    """
    while True:
        sleep(app.config['SKED_TIME'] / 1000)
        (new_skeds, skeds) = skimmer.get_skeds()

        x = jsonify(skeds)
        ws.send(x.data.decode('utf-8'))


@sock.route('/getspotsws')
def get_spots_ws(ws):
    """Provide a websocket connection that continually sends the current list of
    RBN spots of SKCC members.
    
    This loops forever and delays based on the app.config 'SPOT_TIME' 
    """
    while True:
        sleep(app.config['SPOT_TIME'] / 1000)
        (new_spots, spots) = skimmer.get_spots()

        x = jsonify(spots)
        ws.send(x.data.decode('utf-8'))
