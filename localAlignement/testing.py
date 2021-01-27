
from deformationcytometer.detection.includes.UNETmodel import *

if __name__ == "__main__":
    import clickpoints.launch
    print(clickpoints.__file__)
    clickpoints.launch.main(r"/home/andreas/Software/localAlignement/test_data/KO_analyzed/database.cdb")