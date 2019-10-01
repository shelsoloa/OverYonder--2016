import sys
from game import OverYonderEngine

if __name__ == "__main__":
    debug = None
    try:
        debug = sys.argv[1]
    except IndexError:
        pass

    game = OverYonderEngine(debug is not None)
    game.run()
