from datetime import datetime, timezone
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
