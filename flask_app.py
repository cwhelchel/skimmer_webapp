import threading
from time import sleep
from flask import Flask
from flask import render_template
from flask import jsonify
from skimmer import cSkimmer

skimmer = cSkimmer()
app = Flask(__name__)
app.config.from_pyfile('skimmerwebapp.cfg')

@app.before_first_request
def start_skimmer():
    #kick off main skcc skimmer script
    skimmer.run()

    #kick off parsing thread
    t = threading.Thread(target=skimmer.read)
    t.start()
    print("read started")


@app.route("/")
def hello_world():
    skimmer.force_refresh()
    return render_template('index.html')

@app.route('/getstatus')
def get_status():
    s = skimmer.get_status()
    j = s.get_lines()
    return jsonify(j)

@app.route('/getspots')
def get_spots():
    ''' Returns the newest list of spots or returns "No new spots" 
    
    '''
    (new_spots, spots) = skimmer.get_spots()

    if (new_spots):
        return jsonify(spots)
    else:
        return "No new spots"


@app.route('/getskeds')
def get_skeds():
    ''' Returns the newest list of SKEDS or returns "No new spots" 
    
    '''
    (new_skeds, sekds) = skimmer.get_skeds()

    if (new_skeds):
        return jsonify(sekds)
    else:
        return "No new spots"

@app.route('/clearspots')
def clear_spots():
    skimmer.clear_spots()
    return "nothing"
