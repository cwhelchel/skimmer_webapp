# SKCC SKIMMER WEBAPP

This is a web wrapper to [K7MJG's SKCC skimmmer][1] python application.

It parses the output of a out-of-the box configuration of his application and displays
them in a web page.

Behind the scenes, the web app will kick off a process for K7MJG's SKCC skimmer
application. You won't normally see the output of this process. The web app will
translate the output that you would normally see and places it in a convenient
website that you can browse **from inside your network**. 

**It's not recommended that you expose this website to the outside world. You 
do so at your own risk!!!**

## Configure SKCC SKIMMER

Replace the included ```skcc_skimmer.cfg``` with your version of the file. If you
have already run the skimmer before then you just need to copy and paste it over
the file. If you have never run the skimmer before, open the file and update 
these three things: 

* Your callsign: `MY_CALLSIGN`
* Your QTHs Maidenhead GridSquare: `MY_GRIDSQUARE`
* the path to your master adi file (skcclogger): `ADI_FILE`

For example, here's what my ```skcc_skimmer.cfg``` looks like in the file (this 
is on Windows 10):

```python
    MY_CALLSIGN    = 'KQ4DAP'           
    MY_GRIDSQUARE  = 'EM82dl'           
    SPOTTER_RADIUS = 750          

    ADI_FILE       = r'C:\\SKCCLogger\\Logs\\skcc.adi'
```

You could also take the time to change your goals, targets, and bands. Refer to
the [skcc_skimmer configuration][2] for more information.

To configure web-app specific options open ```skimmerwebapp.cfg```.

## Running the Webapp - Windows

This section is for Windows users:

1) Download the release package
2) Extract to a location you will be able to find again
3) Update the included skcc_skimmer.cfg file inside the package by either:
   - copying an existing skcc_skimmer.cfg into here
   - open the file and update the needed settings
4) Execute the ```run_webapp.bat``` file.
5) Point your browser to http://127.0.0.1:5000 to see the website

You should see a command prompt appear with server status information and some other
output. This is the skimmer running and printing. It prints out a lot. If needed
this can be disabled, look in ```skimmwerwebapp.cfg```

## Running the Webapp - Others

This section is for non-Windows users and other cool people.

Run directly from source using Python. It's really not that hard, and the 
process is explained in the next sections:

### Install Dependencies

You need Python 3, Flask, and Flask_sock.

After installing Python, at the command prompt run these:

    $ python -m pip install flask
    $ python -m pip install flask_sock

Or, optionally

    $ python -m pip install -r requirements.txt    
    #  ^^^ will include pyinstaller which is needed for exe releases

### Running the WEB APP    

Once this file is updated and saved, you are ready to run the application at the command prompt, like so:

    $ python flask_app.py

Browse to the location it outputs (http://127.0.0.1:5000) and enjoy.


[1]: https://github.com/k7mjg/skcc_skimmer
[2]: https://www.k7mjg.com/#id_Configuration