import json
  
# Read Existing JSON File
with open('data.json') as f:
    data = json.load(f)
  
# Append new object to list data
data["score"]["NahLogic#4109"] = 1
    
# Create new JSON file
with open('data.json', 'w') as f:
    json.dump(data, f, indent=4)
  
# Closing file
f.close()

# Read Existing JSON File
with open('data.json') as f:
    data = json.load(f)

data["playingGuilds"].append(ctx.guild.id)