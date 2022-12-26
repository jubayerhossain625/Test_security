import json
import logging
import os
from flask import Flask,request,jsonify
from fuzz import SimpleTest  #simpleTest
from fuzz import DirectlyTraversal #Directry traversal
from fuzz import PathTraversal #path traversal

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)

obj_derectry=DirectlyTraversal()
obj_path=PathTraversal()
obj_simple=SimpleTest()

feedback = ""
getdata =[]

app = Flask(__name__)
@app.route("/", methods=['GET', 'POST'])
def index():
   
    input =  request.get_json()
    if len(input.keys()) <3:
        geturl = str(input["url"])
      
       
        try:

         type = str(input["type"])
         match type:
            case "s":
                obj_simple._base_url=geturl
                obj_simple.start()

            case "d":
               obj_derectry._base_url="https://www.google.com"
               obj_derectry.start()
            case "p":
               obj_path._base_url="https://www.google.com"
               obj_path.start()

            case "b":
                 print("Burte Fource")

        except:
             print("Somet----g went wrong")
        finally:

            fileObject = open("data.json", "r")
            jsonContent = fileObject.read()
            data_loaded = json.loads(jsonContent)
            fileObject.close()
            os.remove('data.json')

            firstData = []
            print(len(data_loaded))
            firstData = data_loaded.copy()
            data_loaded.clear()
            print(len(data_loaded))
        
            return jsonify(firstData)
       
    else:
      
       return {
            "url":str(input["url"])
        }




if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=2000, debug=True)