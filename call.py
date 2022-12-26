import logging
from fuzz import DirectlyTraversal #Directry traversal
from fuzz import PathTraversal #path traversal
from fuzz import SimpleTest  #simpleTest

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)

#object
obj_derectry=DirectlyTraversal()
obj_path=PathTraversal()
obj_simple=SimpleTest()

#derectry._base_url="https://www.google.com"
#obj_derectry._base_url="https://www.google.com"

obj_path._base_url="https://www.google.com"
obj_path.start()

