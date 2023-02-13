import re
from skimmer_spot import Spot, SpotType

class SkimmerParser():
    '''This class handles the parsing of output from the skimmer.
    
    The main entry point parse_spot is a static method called like so
    
    `SkimmerParser.parse_spot(line)`
    
    It is used to convert an output line into the `Spot` type the webapp uses.
    '''

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
        spot = SkimmerParser._parse_spot_header(line)
        
        if (spot):
            spot = SkimmerParser._parse_spot_body(line, spot)

        return spot


    @staticmethod
    def _parse_spot_header(line : str) -> Spot:

        # sometimes the line has a bell char \x07 at the front (from the main skimmer)
        # we need to remove it (and other control chars) (this isn't all of them)
        line = re.sub(r'[\x00-\x1f]', '', line)

        match = SkimmerParser.spot_hdr.match(line)

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
        if y := SkimmerParser.freq.search(x[0]):
            (freq, spotter) = y.group(1,2)
            spot.freq = freq.strip()
            spot.spotter = spotter.strip()

        if z := SkimmerParser.skcc.search(x[0]):
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
