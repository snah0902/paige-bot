import json

# Opening JSON file
f = open('test.json')
  
# returns JSON object as 
# a dictionary
data = json.load(f)

for key in data:
    print(key)

# Closing file
f.close()