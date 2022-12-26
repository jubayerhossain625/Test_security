# # -*- coding: utf-8 -*-
# import json

# # Make it work for Python 2+3 and with Unicode
# import io

# # Define data
# data = {"A":"a",
#         "B":"b"
# }

# # # Write JSON file
# with io.open('data.json', 'w', encoding='utf8') as outfile:
#     str_ = json.dumps(data,
#                       indent=4, sort_keys=True,
#                       separators=(',', ': '), ensure_ascii=False)
#     outfile.write(str_)

# # Read JSON file
# with open('data.json') as data_file:
#     data_loaded = json.load(data_file)

# print(data_loaded)


import json

# aList = [{"a":54, "b":87}, {"c":81, "d":63}, {"e":17, "f":39}]
# jsonString = json.dumps(aList)
# jsonFile = open("data.json", "w")
# jsonFile.write(jsonString)
# jsonFile.close()
fileObject = open("data.json", "r")
jsonContent = fileObject.read()
data_loaded = json.loads(jsonContent)
print(len(data_loaded))