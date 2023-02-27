import os, sys
import subprocess
import threading
from skimmer_parser import SkimmerParser
from datetime import datetime, timezone, timedelta
from skimmer_spot import Spot, SpotType


class SkccStatus:
    __config = {}
    __lines = []
    
    state = 'starting'

    def __str__(self) -> str:
        return '\r\n'.join(self.__lines)

    def add_cfg(self, cfg: str, data: str):
        self.__config[cfg] = data

    def add(self, line : str):
        self.__lines.append(line)

    def get_lines(self) -> list:
        return [self.state] + self.__lines


class cSkimmer:
    """The main class for parsing output from skcc_skimmer.py

    This class will spawn a python subprocess (of skcc_skimmer.py) with piped
    stdout which is then read forever. Call run() then read() <= which blocks 
    forever

    :param cfg: dictionary of configured values. Usually the ```app.config``` 
    object from Flask
    """

    def __init__(self, cfg : dict):
        if sys.platform == "win32":
            self.__cmd = ["skcc_skimmer.exe"]
        else:
            self.__cmd = ["python3", "skccskimmer\skcc_skimmer.py"]
        self.__status = SkccStatus()
        self.__spots = []
        self.__sked_spots = []
        self.__new_spot = False
        self.__new_skeds = False
        self.__parsing_skeds = True
        self.__is_running = False
        self.__config = cfg

    def run(self):
        """Create the python subprocess and run the main skimmer application.
        
        This should be done first.
        """

        if not self.__is_running:
            os.environ['PYTHONIOENCODING'] = 'utf-8'

            print('running cmd: ' + ' '.join(self.__cmd))
            print('in curr dir: ' + os.getcwd())

            self.__proc = subprocess.Popen(self.__cmd, 
                encoding='utf-8', 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)

            self.__is_running = True

            # kick off parsing thread
            self.__thread = threading.Thread(target=self.read)
            self.__thread.start()
            print("read thread started")


    def stop(self):
        """Stops the running skcc skimmer process
        
        """
        if (self.__proc != None and self.__is_running):
            print('killing process...')
            self.__proc.terminate()

            print('joining read thread...')
            self.__thread.join()

            self.__is_running = False
            self.__status.state = 'stopped'


    def read(self):
        """Reads and parses the skimmer subprocess' output. 
        
        This never returns.
        """

        if (self.__proc == None):
            return ""

        self.__status.state = 'starting'

        str = ""
        for line in iter(self.__proc.stdout.readline, ''):
            str = line.strip()
            self.__parse(str)

            if "SHOW_SKIMMER_OUTPUT" in self.__config and \
                self.__config['SHOW_SKIMMER_OUTPUT']:
                print(str)

        # we never get here
        return str


    def get_spots(self) -> tuple[bool, list]:
        """Returns the a tuple with the lists of spots and a flag indicating there are new spots
        
        Calling this method sets the above flag to False
        """
        result = (self.__new_spot, self.__spots)
        self.__new_spot = False
        return result


    def get_skeds(self) -> tuple[bool, list]:
        """Returns the a tuple with the lists of skeds and a flag indicating there are new skeds
        
        Calling this method sets the above flag to False. Also if this method is
        called while new skeds are being parsed. It returns the old skeds.
        """
        if (self.__parsing_skeds):
            return (False, self.__sked_spots)

        result = (self.__new_skeds, self.__sked_spots)
        self.__new_skeds = False
        return result


    def get_status(self) -> SkccStatus:
        ''' Gets the skimmer status object '''
        return self.__status


    def clear_spots(self):
        """ Clears the list of current spots (not skeds) from the object
        """
        self.__spots.clear()

        # force refresh of frontend spots list
        self.__new_spot = True


    def force_refresh(self):
        '''Sets the flags to indicate that there are new spots to see.'''
        self.__new_skeds = True
        self.__new_spot = True


    def __parse(self, line : str):
        if (self.__status.state == 'starting'):
            # if we're starting lets grab all the output for later 
            self.__parse_cfg_line(line, "GOALS:")
            self.__parse_cfg_line(line, "TARGETS:")
            self.__parse_cfg_line(line, "BANDS:")
            self.__status.add(line)
            if line.startswith("Running..."): 
                self.__status.state = 'running'

        if (self.__status.state == 'running'):
            # were running so lets parse all the juicy spots
            if (line == "=========== SKCC Sked Page ============"):
                print('new skeds incoming...')
                self.__parsing_skeds = True
                self.__sked_spots.clear()
            elif (line == "======================================="):
                print('skeds done.')
                self.__parsing_skeds = False
                self.__new_skeds = True
            else:
                self.__parse_line(line)

            self.__check_spots()


    def __parse_cfg_line(self, line : str, prefix : str):
        if line.startswith(prefix):
            self.__status.add_cfg(prefix, line)


    def __parse_line(self, line : str):
        spot = SkimmerParser.parse_spot(line)

        if (spot == None): 
            return

        #print(spot)

        if (self.__parsing_skeds):
            spot.kind = SpotType.SKED
            spot.spotter = "sked"
            self.__sked_spots.append(spot)
        else:
            spot.kind = SpotType.SPOT
            self.__new_spot = True
            self.__spots.append(spot)


    def __check_spots(self):
        '''Loop thru the spots list and remove any older than a certain time'''
        if "SPOT_EXPIRE_TIME" in self.__config:
            timeout = self.__config["SPOT_EXPIRE_TIME"]
        else:
            timeout = 3600

        for spot in self.__spots:
            t = datetime.now(tz=timezone.utc)
            # print(f'spot time {spot.utc_time} == current {t}')
            delta = t - spot.utc_time

            # if its been an hour remove the spot from the list
            if delta >= timedelta(seconds=timeout):
                print("removing old spot")
                self.__spots.remove(spot)
