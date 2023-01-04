import json
  
# Read Existing JSON File
with open('data.json') as f:
    data = json.load(f)

leaderboardList = []

for user in data["score"]:
    score = data["score"][user]
    leaderboardList.append((score, user))

leaderboardList.sort(reverse = True)

leaderboard = "**Players**"
for i in range(10):
    if i < len(leaderboardList):
        score, user = leaderboardList[i]
        leaderboard += f"\n`{i+1}` {user[:-5]} `{score}`"
    else:
        leaderboard += f"\n`{i+1}` N/A `0`"

print(leaderboard)
  
# Closing file
f.close()
