import json
import sys
from pathlib import Path

# Our framework pass eval result to python hook via argv[1] as a store path
# This common function read those and return proper python dict
def getEvalResult():
    return json.loads(Path(sys.argv[1]).read_text())
