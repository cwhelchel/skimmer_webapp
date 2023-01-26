import subprocess
import io
import re
from time import sleep
from skimmer import cSkimmer
from skimmer import Parser

# spawn a subprocess that redirects the main skcc_skimmer output from stdout
# to a file (the skimmer displays info only at the console)
def start_skimmer():
    x = cSkimmer()
    x.run()
    return x

data = "1906Z W2NR   ( 1050 Sx6  Randy      NH); YOU need them for K3Y/1 (20m); STATUS: K3Y/1 working down the bands 14.117"
#"2357Z+VE3KZ  (22804 Sx5  Bob        ON) on   7059.0 by K9LC(734mi, 37dB); YOU need them for BRAG,C,P(new +22804)"
# "0009Z WB4HNL (22010      Rick       FL) on   7052.0 by WE9V(735mi, 17dB); YOU need them for BRAG,C,WAS,P(new +22010); THEY need you for C"
# "0013Z W0GV   ( 7889 S    Gerry      CO) on   7055.5 by K9LC(734mi, 19dB); YOU need them for BRAG,C,WAS-S,P(new +7889)"
# 
# 0023Z N4DT   (16533      Danny      SC) on   7055.9 by W8WWV(637mi, 13dB); YOU need them for BRAG,C,WAS; THEY need you for C
# 0023Z N4DT   (16533      Danny      SC) on   7055.9 by W8WTS(631mi, 9dB); YOU need them for BRAG,C,WAS; THEY need you for C"    

if __name__ == '__main__':
    print("test")

    spot = Parser.parse_spot(data)

    print(spot)

    # if m:
    #     print(m.groups())
    #     print("ih")
    
    # proc = start_skimmer()

    # while True:
    #     print(proc.read())
    #     sleep(500)