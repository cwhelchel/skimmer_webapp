import subprocess
import re
import os
from datetime import datetime, timezone, timedelta
from flask import Flask
from dataclasses import dataclass

class SpotType:
    SKED = 1
    SPOT = 2
    UNKNOWN = 3

@dataclass
class Spot:
    '''This is the data object for a spot line.
    
    Objects of this type will be sent to the front end for display.'''

    time : str
    call : str
    kind : SpotType
    flag : bool = False
    freq : str = ""
    spotter : str = ""
    name : str = ""
    spc : str = ""
    num : str = ""
    you_need: str = ""
    they_need: str = ""
    sked_stat: str = ""
    utc_time : datetime = datetime.min

    def __post_init__(self):
        self.time = self.time[:2] + ':' + self.time[2:].lower()
        hour = self.time[:2]
        minute = self.time[3:5]
        self.utc_time = datetime.utcnow()
        self.utc_time = datetime(self.utc_time.year, \
            self.utc_time.month, \
            self.utc_time.day, \
            int(hour), \
            int(minute), \
            0, 0, tzinfo=timezone.utc)


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
        self.__cmd = ["python", "skcc_skimmer.py"]
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

            self.proc = subprocess.Popen(self.__cmd, encoding='utf-8', stdout=subprocess.PIPE)
            self.__is_running = True


    def read(self):
        """Reads and parses the skimmer subprocess' output. 
        
        This never returns.
        """

        if (self.proc == None):
            return ""

        str = ""
        for line in iter(self.proc.stdout.readline, ''):
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
        spot = Parser.parse_spot(line)

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



class Parser():
    '''This class handles the parsing of spot lines from the skimmer application'''

    # group 1 = zulu time, 2 = sked/spot flag, 3 = callsign
    spot_hdr = re.compile("([0-9]{4}Z)(\+| )([A-Z0-9\/]*)")

    # group 1 = frequency, 2 = spotter info
    freq = re.compile("on\s+([\d\.\d+]+)\sby\s([\w\-\/\\]+\([\d\w,\s]+\))")

    # group 1 = skcc num, 2 = fname, 3 = SPC
    skcc = re.compile("\(\s*(\d+\s(?:\w|\s)+)\s+([\w\-\']+)\s+([0-9A-Za-z]+)\)")

    @staticmethod
    def parse_spot(line : str) -> Spot:
        '''Parses a line from the skimmer and returns a Spot object.

        May return None if the spot header is invalid. '''
        spot = Parser._parse_spot_header(line)
        
        if (spot):
            spot = Parser._parse_spot_body(line, spot)

        return spot


    @staticmethod
    def _parse_spot_header(line : str) -> Spot:

        # sometimes the line has a bell char \x07 at the front (from the main skimmer)
        # we need to remove it (and other control chars) (this isn't all of them)
        line = re.sub(r'[\x00-\x1f]', '', line)

        match = Parser.spot_hdr.match(line)

        if match:
            x = match.group(1, 2, 3)

            # NOTE: for skeds, the flag indicator is for status updates to the 
            # sked page. for spots its to indicate that that call-sign is needed
            # for a goal.

            flag = True if x[1] == '+' else False

            spot = Spot(time = x[0], \
                        call = x[2], \
                        kind = SpotType.UNKNOWN,\
                        flag = flag)
            return spot
        
        #else: 
            #print("error spot header didn't match!")
        
        return None


    @staticmethod 
    def _parse_spot_body(line : str, spot : Spot) -> Spot:
        x = line.split(';')

        if len(x) <= 0:
            return spot
        
        # parse first split str (freq, name, num, etc.)
        if y := Parser.freq.search(x[0]):
            (freq, spotter) = y.group(1,2)
            spot.freq = freq.strip()
            spot.spotter = spotter.strip()

        if z := Parser.skcc.search(x[0]):
            (num, name, spc) = z.group(1,2,3)
            spot.num = num.strip()
            spot.name = name.strip()
            spot.spc = spc.strip()

        # pull out the "needs" and sked status if its there (it may be in idx 2)
        temp = x[1].strip() if len(x) > 1 else ""
        spot.you_need  = x[1][18:] if len(x) > 1 else ""
        spot.they_need = x[2].strip() if len(x) > 2 else ""
        spot.sked_stat = x[3].strip() if len(x) > 3 else ""

        if spot.they_need.startswith("STATUS:"):
            spot.sked_stat = spot.they_need
            spot.they_need = ""
        elif spot.they_need.startswith("THEY"):
            spot.they_need = spot.they_need[17:].strip()

        # if a sked dude is spotted then this gets inserted right after the 
        # callsign and skcc info 
        if temp.startswith("Last spotted"):
            t = re.search("([\d\.\d+]+)", spot.you_need)
            if t:
                spot.freq = t.group(1)
            spot.you_need = spot.they_need[18:]
            spot.they_need = spot.sked_stat[17:] if spot.sked_stat.startswith("THEY need") else ""
            spot.sked_stat = x[4].strip() if len(x) > 4 else spot.sked_stat

        return spot
