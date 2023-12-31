import requests
import math

# Define the base URL for FPL API
BASE_URL = "https://fantasy.premierleague.com/api/"
GENERAL_INFO = "bootstrap-static/"
TEAM_IDS = 0
OWNERSHIP = 1
PLAYER_NAME = 2
TEAM_NAME = 0
VALUE_TO_PRINT = 1
GAMEWEEK = 1
TEAM_ENTRIES = 0
STARTING_GW = 1
BENCH_POS = 11
IN_PLAYERS_LIST = 0
IN_POINTS = 1
OUT_PLAYERS_LIST = 2
OUT_POINTS = 3
FINE = 4


# Function to make a GET request to the FPL API
def fpl_api_get(endpoint):
    url = f'{BASE_URL}{endpoint}'
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error: {response.status_code}')
        return None


# Function to get info on a player
def getPlayerInfo(playerID):
    playerData = f"element-summary/{playerID}/"
    data = fpl_api_get(playerData)
    return data


# Function to get info on a fpl team
def getTeamInfo(teamID):
    teamData = f"entry/{teamID}/"
    data = fpl_api_get(teamData)
    return data


# Function to get info on a fpl team's gameweek
def getTeamGWInfo(teamID, gw):
    gwEntry = f"entry/{teamID}/event/{gw}/picks/"
    data = fpl_api_get(gwEntry)
    return data


# Function to get info on a fpl team's transfers
def getTeamTransfersInfo(teamID):
    transfersData = f"entry/{teamID}/transfers/"
    data = fpl_api_get(transfersData)
    return data


# Function to get info on a fpl league
def getLeagueInfo(leagueID):
    leagueData = f"leagues-classic/{leagueID}/standings/"
    data = fpl_api_get(leagueData)
    return data


# Function to get Effective Ownership on players in the teams
def getEO(gw):
    EO = {}
    for team in teams:
        teamID = team['entry']
        data = getTeamGWInfo(teamID, gw)
        for pick in data["picks"][:BENCH_POS]:
            playerID = pick["element"]
            if playerID in EO.keys():
                EO[playerID][1] += pick['multiplier']
                EO[playerID][0].append(teamID)
            elif pick['multiplier']:
                EO[playerID] = [[teamID], pick['multiplier']]
    players = []
    for player in EO:
        players.append((EO[player][TEAM_IDS], round(100 * (EO[player][OWNERSHIP] / len(teams)), 2), idToName(player)))
    players = sorted(players, key=lambda x: x[OWNERSHIP], reverse=True)
    for player in players:
        print(player[PLAYER_NAME], "{0}%".format(player[OWNERSHIP]))
    return players


def idToName(pid):
    index = pid
    while pid != sgdata[index - 1]["id"]:
        index -= 1
    return sgdata[index - 1]["web_name"]


def teamIDtoName(teamID):
    for team in teams:
        if team["entry"] == teamID:
            return team["entry_name"]


def teamIDtoStruct(teamID):
    for team in teams:
        if team["entry"] == teamID:
            return team


def idToPStruct(pid):
    index = pid
    while pid != sgdata[index - 1]["id"]:
        index -= 1
    return sgdata[index - 1]


def getNumberOfSubs():
    teamList = []
    for team in teams:
        teamID = team['entry']
        tdata = getTeamInfo(teamID)
        teamList.append((tdata['name'], tdata['last_deadline_total_transfers']))
    teamList = sorted(teamList, key=lambda x: x[1], reverse=True)
    for p in teamList:
        print(p[TEAM_NAME], p[VALUE_TO_PRINT])


def bestBench(gw):
    teamList = []
    for team in teams:
        teamID = team['entry']
        tdata = getTeamGWInfo(teamID, gw)
        teamList.append((team['entry_name'], tdata['entry_history']['points_on_bench']))
    teamList = sorted(teamList, key=lambda x: x[1], reverse=True)
    for p in teamList:
        print(p[TEAM_NAME], p[VALUE_TO_PRINT])
    return teamList


def bestBenchOverAll():
    teamList = []
    for gw in range(1, currentGW):
        tempList = bestBench(gw)
        for tt in tempList:
            teamList.append((tt, gw))
    teamList = sorted(teamList, key=lambda x: x[TEAM_ENTRIES][VALUE_TO_PRINT], reverse=True)
    for p in teamList:
        print(p[TEAM_ENTRIES][TEAM_NAME], p[TEAM_ENTRIES][VALUE_TO_PRINT], "GW-{}".format(p[GAMEWEEK]))


def bestTransfers(startingGW=STARTING_GW, useTeams=[]):
    transferList = []
    if not useTeams:
        useTeams = teams
    for team in useTeams:
        teamID = team['entry']
        print(f"Analyzing the Transfers of: {teamID}")
        transfers = getTeamTransfersInfo(teamID)
        costs = {}
        for gw in range(startingGW, currentGW + 1):
            gwInfo = getTeamGWInfo(teamID, gw)
            costs[gw] = gwInfo["entry_history"]["event_transfers_cost"]
            if gwInfo["active_chip"] == 'wildcard':
                costs[gw] = 'wildcard'
        oldgw = 0
        for transfer in transfers:
            inPlayer = transfer['element_in']
            outPlayer = transfer['element_out']
            gw = transfer['event']
            if gw < startingGW:
                break
            if costs[gw] == 'wildcard':
                continue
            picks = getTeamGWInfo(teamID, gw)['picks']
            #multiplier = [pick["multiplier"] for pick in picks if pick["element"] == inPlayer][0]
            tempInfo = getPlayerInfo(inPlayer)
            inPoints = tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points'] #* multiplier
            tempInfo = getPlayerInfo(outPlayer)
            outPoints = getPlayerInfo(outPlayer)['history'][gw - 1 - (currentGW - len(tempInfo['history']))][
                            'total_points'] #* multiplier
            fine = 0
            if costs[gw]:
                fine = 4
                costs[gw] -= 4
            # t.append((f"{team['entry_name']} GW{gw}: {sgdata[outPlayer-1]['web_name']} ({outPoints}) -> {sgdata[
            # inPlayer-1]['web_name']} ({inPoints}) hit: {fine*-1} OVR: ",inPoints-outPoints-fine))
            if oldgw != gw:
                transferList.append([[inPlayer], inPoints, [outPlayer], outPoints, fine, team['entry_name'], gw])
            else:
                transferList[-1] = [transferList[-1][IN_PLAYERS_LIST] + [inPlayer],
                                    transferList[-1][IN_POINTS] + inPoints,
                                    transferList[-1][OUT_PLAYERS_LIST] + [outPlayer],
                                    transferList[-1][OUT_POINTS] + outPoints, transferList[-1][FINE] + fine,
                                    team['entry_name'], gw]
            oldgw = gw

    # t=sorted(t,key=lambda x : x[1],reverse=True)
    transferList = sorted(transferList, key=lambda x: x[IN_POINTS] - x[OUT_POINTS] - x[FINE], reverse=True)

    for p in transferList:
        top = f""
        top += f"{p[5]} GW{p[6]}: "
        top += f"IN ({p[IN_POINTS]} points): "
        for player in p[IN_PLAYERS_LIST]:
            top += f"{idToName(player)}, "
        top = top[:-2]
        top += f"|OUT ({p[OUT_POINTS]} points): "
        for player in p[OUT_PLAYERS_LIST]:
            top += f"{idToName(player)}, "
        top = top[:-2]
        top += f"|hit: {p[FINE] * -1}|"
        top += f"OVR - {p[IN_POINTS] - p[OUT_POINTS] - p[FINE]}"
        print(top)


def getUninqePlayers(gw):
    u = {}
    players = getEO(gw)
    for player in players:
        if len(player[TEAM_IDS]) > 1:
            continue
        else:
            if player[TEAM_IDS][0] in u.keys():
                u[player[TEAM_IDS][0]].append(player[PLAYER_NAME])
            else:
                u[player[TEAM_IDS][0]] = [player[PLAYER_NAME]]
    for team in teams:
        if team['entry'] in u.keys():
            print(team['entry_name'], u[team['entry']], "\n")
        else:
            print(team['entry_name'], "[]")
    return u


def getCaptaincy(gw):
    for team in teams:
        data = getTeamGWInfo(team["entry"], gw)
        for player in data["picks"]:
            if player["is_captain"]:
                print(team["entry_name"], idToName(player["element"]))


def getCaptain(teamID, gw):
    data = getTeamGWInfo(teamID, gw)
    for player in data["picks"]:
        if player["is_captain"]:
            return player["element"]


def calcXPoints(pid, gw, is_captain):
    pInfo = getPlayerInfo(pid)
    pStruct = idToPStruct(pid)
    pos = pStruct["element_type"]
    gwStruct = pInfo['history'][gw - 1 - (currentGW - len(pInfo['history']))]
    xG = round(float(gwStruct['expected_goals']))
    xA = round(float(gwStruct['expected_assists']))
    xGC = round(float(gwStruct['expected_goals_conceded']))
    yellow_cards = gwStruct['yellow_cards']
    red_cards = gwStruct['yellow_cards']
    penalties_missed = gwStruct['penalties_missed']
    own_goals = gwStruct['own_goals']
    minutes = gwStruct['minutes']
    bonus = gwStruct['bonus']

    basePoints = yellow_cards * -1 + red_cards * -3 + penalties_missed * -2 + own_goals * -2 + math.ceil(
        minutes / 59) + xA * 3 + bonus
    match pos:
        case 1:
            additional_points = xG * 6 - math.floor(xGC / 2) + math.floor(gwStruct['saves'] / 3) + \
                                gwStruct['penalties_saved'] * 5 + (not bool(xGC)) * 4 * math.floor(minutes / 60)
        case 2:
            additional_points = xG * 6 - math.floor(xGC / 2) + (not bool(xGC)) * 4 * math.floor(minutes / 60)
        case 3:
            additional_points = xG * 5 + (not bool(xGC))
        case 4:
            additional_points = xG * 4
    return (basePoints + additional_points) * (1 + is_captain)


def luckiestPlayer(startingGW=STARTING_GW):
    points = []
    for team in teams:
        teamID = team['entry']
        print(f"Analyzing the Points of: {teamID}")
        temp_total = 0
        rPoints = 0
        for gw in range(startingGW, currentGW + 1):
            data = getTeamGWInfo(teamID, gw)
            for pick in data["picks"][:BENCH_POS]:
                pid = pick["element"]
                temp_total += calcXPoints(pid, gw, pick["is_captain"])
            rPoints += data["entry_history"]["points"] - data["entry_history"]["event_transfers_cost"]
            temp_total -= data["entry_history"]["event_transfers_cost"]
        points.append([team["entry_name"], rPoints, temp_total])
    points = sorted(points, key=lambda x: x[1] - x[2], reverse=True)
    for p in points:
        print(f"{p[0]} Scored {p[1]} Points while his Xpoints is {p[2]} Lucky Points: {p[1] - p[2]}\n")


def captaincyAccuracy():
    badList = []
    for team in teams:
        teamID = team["entry"]
        print(f"Analyzing the Captains of: {teamID}")
        badCaptains = 0
        for gw in range(STARTING_GW, currentGW + 1):
            gwInfo = getTeamGWInfo(teamID, gw)
            tempInfo = getPlayerInfo(getCaptain(teamID, gw))
            captainPoints = tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points']
            for pick in gwInfo["picks"]:
                tempInfo = getPlayerInfo(pick["element"])
                tempPoints = tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points']
                if tempPoints > captainPoints:
                    badCaptains += 1
                    break
        badList.append([team["entry_name"], currentGW - badCaptains])
    badList = sorted(badList, key=lambda x: x[1], reverse=True)
    for team in badList:
        print(f" {team[0]} captain accuracy is {team[1]}/{currentGW}\n")


def captaincyLoses():
    badList = []
    for team in teams:
        teamID = team["entry"]
        print(f"Analyzing the Captains of: {teamID}")
        loses = 0
        for gw in range(STARTING_GW, currentGW + 1):
            gwInfo = getTeamGWInfo(teamID, gw)
            best = 0
            # tempInfo = getPlayerInfo(getCaptain(teamID, gw))
            # captainPoints = tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points']
            for pick in gwInfo["picks"]:
                tempInfo = getPlayerInfo(pick["element"])
                tempPoints = tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points']
                if pick["is_captain"]:
                    captainPoints = tempPoints
                if tempPoints > best:
                    best = tempPoints
            loses += (best - captainPoints) * 2
        badList.append([team["entry_name"], loses])
    badList = sorted(badList, key=lambda x: x[1], reverse=True)
    for team in badList:
        print(f" {team[0]} captain inaccuracy lost him {team[1]} points\n")


def teamRepresentation(gw):
    teamList = {}
    for pt in gdata["teams"]:
        teamList[pt["name"]] = 0
    for team in teams:
        teamID = team["entry"]
        gwInfo = getTeamGWInfo(teamID, gw)
        for pick in gwInfo["picks"]:
            playerID = pick["element"]
            playerInfo = idToPStruct(playerID)
            pTeam = gdata["teams"][playerInfo["team"] - 1]["name"]
            if pTeam in teamList.keys():
                teamList[pTeam] += 1
    teamsList = sorted(teamList.items(), key=lambda x: x[1], reverse=True)
    for t in teamsList:
        print(f"{t[0]} has {round(t[1] * 100 / (len(teams) * 15), ndigits=2)}% of the players in GW{gw}\n ")


def bestWildcard():
    transferList = []
    for team in teams:
        teamID = team['entry']
        GWs = []
        print(f"Analyzing the Transfers of: {teamID}")
        for gw in range(currentGW, STARTING_GW, -1):
            gwInfo = getTeamGWInfo(teamID, gw)
            if gwInfo["active_chip"] == 'wildcard':
                print (team["entry_name"], gwInfo)
                GWs.append(gw)
        if GWs:
            transfers = getTeamTransfersInfo(teamID)
        else:
            continue
        oldgw = 0
        for transfer in transfers:
            gw = transfer['event']
            if not gw in GWs:
                continue
            inPlayer = transfer['element_in']
            outPlayer = transfer['element_out']
            picks = getTeamGWInfo(teamID, gw)['picks']
            multipliers = [pick["multiplier"] for pick in picks if pick["element"] == inPlayer]
            if multipliers:
                multiplier = multipliers[0]
            else:
                continue
            tempInfo = getPlayerInfo(inPlayer)
            inPoints = tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points'] * multiplier
            tempInfo = getPlayerInfo(outPlayer)
            outPoints = getPlayerInfo(outPlayer)['history'][gw - 1 - (currentGW - len(tempInfo['history']))][
                            'total_points'] * multiplier
            fine = 0
            if oldgw != gw:
                transferList.append([[inPlayer], inPoints, [outPlayer], outPoints, fine, team['entry_name'], gw])
            else:
                transferList[-1] = [transferList[-1][IN_PLAYERS_LIST] + [inPlayer],
                                    transferList[-1][IN_POINTS] + inPoints,
                                    transferList[-1][OUT_PLAYERS_LIST] + [outPlayer],
                                    transferList[-1][OUT_POINTS] + outPoints, transferList[-1][FINE] + fine,
                                    team['entry_name'], gw]
            oldgw = gw
    transferList = sorted(transferList, key=lambda x: x[IN_POINTS] - x[OUT_POINTS], reverse=True)
    for p in transferList:
        top = f""
        top += f"{p[5]} GW{p[6]}: "
        top += f"IN ({p[IN_POINTS]} points): "
        for player in p[IN_PLAYERS_LIST]:
            top += f"{idToName(player)}, "
        top = top[:-2]
        top += f"|OUT ({p[OUT_POINTS]} points): "
        for player in p[OUT_PLAYERS_LIST]:
            top += f"{idToName(player)}, "
        top = top[:-2]
        top += f"|OVR - {p[IN_POINTS] - p[OUT_POINTS] - p[FINE]}"
        print(top)


def managerPointsAllocation(teamID):
    teamDict = {}
    for pt in gdata["teams"]:
        teamDict[pt["name"]] = 0
    for gw in range(STARTING_GW, currentGW):
        gwInfo = getTeamGWInfo(teamID, gw)
        for pick in gwInfo["picks"]:
            playerID = pick["element"]
            playerInfo = idToPStruct(playerID)
            tempInfo = getPlayerInfo(playerID)
            pTeam = gdata["teams"][playerInfo["team"] - 1]["name"]
            if pTeam in teamDict.keys():
                teamDict[pTeam] += pick["multiplier"] * \
                                   tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points']
    teamList = sorted(teamDict.items(), key=lambda x: x[1], reverse=True)
    totalPoints = sum(teamDict.values())
    for t in teamList:
        print(f"{t[0]} has {round(t[1] * 100 / totalPoints, ndigits=2)}% of {teamIDtoName(teamID)} points \n")
    return teamList


def managerAllstars(teamID):
    teamDict = {}
    for gw in range(STARTING_GW, currentGW):
        gwInfo = getTeamGWInfo(teamID, gw)
        for pick in gwInfo["picks"]:
            playerID = pick["element"]
            playerInfo = idToPStruct(playerID)
            pos = playerInfo["element_type"]
            tempInfo = getPlayerInfo(playerID)
            # pTeam = gdata["teams"][playerInfo["team"] - 1]["name"]
            if not (playerID in teamDict.keys()):
                teamDict[playerID] = [pick["multiplier"] * \
                                      tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))] \
                                          ['total_points'], pos]
            else:
                teamDict[playerID] = [pick["multiplier"] * \
                                      tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))] \
                                          ['total_points'] + teamDict[playerID][0], pos]
    teamList = sorted(teamDict.items(), key=lambda x: x[1][0], reverse=True)
    # totalPoints = sum(teamDict.values())
    allstars = {1: [], 2: [], 3: [], 4: []}
    for t in teamList:
        # print(f"{t[0]} has {round(t[1] * 100 / totalPoints, ndigits=2)}% of {teamIDtoName(teamID)} points \n")
        if (len(allstars[1]) + len(allstars[2]) + len(allstars[3]) + len(allstars[4])) == 15:
            break
        tmpPos = t[1][1]
        match tmpPos:
            case 1:
                if len(allstars[tmpPos]) < 2:
                    allstars[tmpPos].append(t)
                else:
                    continue
            case 2:
                if len(allstars[tmpPos]) < 5:
                    allstars[tmpPos].append(t)
                else:
                    continue
            case 3:
                if len(allstars[tmpPos]) < 5:
                    allstars[tmpPos].append(t)
                else:
                    continue
            case 4:
                if len(allstars[tmpPos]) < 3:
                    allstars[tmpPos].append(t)
                else:
                    continue
    return allstars


def pointsAllocation():
    for team in teams:
        managerPointsAllocation(team['entry'])
        print("-----------------------------------------------------------")


def mostPopularCaptain(teamID):
    captains = {}
    for gw in range(STARTING_GW, currentGW):
        tempCaptain = getCaptain(teamID, gw)
        if tempCaptain in captains.keys():
            captains[tempCaptain] += 1
        else:
            captains[tempCaptain] = 1
    return idToName(max(captains, key=captains.get))


def bestBenchByManager(teamID):
    benchPoints = []
    for gw in range(STARTING_GW, currentGW):
        tdata = getTeamGWInfo(teamID, gw)
        benchPoints.append(tdata['entry_history']['points_on_bench'])
    maxPoints = max(benchPoints)
    return f"{maxPoints} in GW{benchPoints.index(maxPoints)}"


def pointsByManager(teamID):
    for gw in range(STARTING_GW, currentGW):
        tdata = getTeamGWInfo(teamID, gw)
        print(tdata['entry_history']['points'])


def worldAvg():
    for event in gdata["events"]:
        print(event["average_entry_score"])


def leagueAvg():
    for gw in range(STARTING_GW, currentGW):
        gwPoints = 0
        for team in teams:
            teamID = team["entry"]
            tdata = getTeamGWInfo(teamID, gw)
            gwPoints += tdata['entry_history']['points']
        print(round(gwPoints / len(teams)))


def managerProfile(teamID):
    #print (mostPopularCaptain(teamID))
    #print (bestBenchByManager(teamID))
    # pAlloc = managerPointsAllocation(teamID)
    #bestTransfers(useTeams=[teamIDtoStruct(teamID)])
    '''allStars = managerAllstars(teamID)
    for pos in allStars:
        for p in allStars[pos]:
            print(idToName(p[0]), p[1][0])'''
    pointsByManager(teamID)
    #worldAvg()
    #leagueAvg()


def mostUniqueManager():
    uniqueCount={}
    for gw in range(STARTING_GW,currentGW+1):
        u = getUninqePlayers(gw)
        for team in u.keys():
            if team in uniqueCount.keys():
                uniqueCount[team] += len(u[team])
            else:
                uniqueCount[team] = len(u[team])

    uniqueCount = sorted(uniqueCount.items(),key=lambda x: x[1],reverse=True)
    for team in uniqueCount:
        print (teamIDtoName(team[0])," ", team[1])

def getCosts():
    costs = {}
    for gw in range(STARTING_GW, currentGW + 1):
        for team in teams:
            teamID = team["entry"]
            data = getTeamGWInfo(teamID, gw)
            if team["entry_name"] in costs.keys():
                costs[team["entry_name"]] += data["entry_history"]["event_transfers_cost"]
            else:
                costs[team["entry_name"]] = data["entry_history"]["event_transfers_cost"]
    costs = sorted(costs.items(), key=lambda x: x[1],reverse=True)
    for cost in costs:
        print(f"{cost[0]} - {cost[1]} ({int(cost[1]/4)} hits)")


def bestFreeHit():
    '''for team in teams:
        teamID = team["entry"]
        for gw in range(currentGW, STARTING_GW, -1):
            gwInfo = getTeamGWInfo(teamID, gw)
            if gwInfo["active_chip"] == 'freehit':
                print(gwInfo, teamIDtoName(teamID))'''
    transferList = []
    for team in teams:
        teamID = team['entry']
        GWs = []
        print(f"Analyzing the Transfers of: {teamID}")
        for gw in range(currentGW, STARTING_GW, -1):
            gwInfo = getTeamGWInfo(teamID, gw)
            if gwInfo["active_chip"] == 'freehit':
                #print(team["entry_name"], gwInfo)
                GWs.append(gw)
        if GWs:
            transfers = getTeamTransfersInfo(teamID)
        else:
            continue
        oldgw = 0
        for transfer in transfers:
            gw = transfer['event']
            if not gw in GWs:
                continue
            inPlayer = transfer['element_in']
            outPlayer = transfer['element_out']
            picks = getTeamGWInfo(teamID, gw)['picks']
            multipliers = [pick["multiplier"] for pick in picks if pick["element"] == inPlayer]
            if multipliers:
                multiplier = multipliers[0]
            else:
                continue
            tempInfo = getPlayerInfo(inPlayer)
            inPoints = tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points'] * multiplier
            tempInfo = getPlayerInfo(outPlayer)
            outPoints = getPlayerInfo(outPlayer)['history'][gw - 1 - (currentGW - len(tempInfo['history']))][
                            'total_points'] * multiplier
            fine = 0
            if oldgw != gw:
                transferList.append([[inPlayer], inPoints, [outPlayer], outPoints, fine, team['entry_name'], gw])
            else:
                transferList[-1] = [transferList[-1][IN_PLAYERS_LIST] + [inPlayer],
                                    transferList[-1][IN_POINTS] + inPoints,
                                    transferList[-1][OUT_PLAYERS_LIST] + [outPlayer],
                                    transferList[-1][OUT_POINTS] + outPoints, transferList[-1][FINE] + fine,
                                    team['entry_name'], gw]
            oldgw = gw
    transferList = sorted(transferList, key=lambda x: x[IN_POINTS] - x[OUT_POINTS], reverse=True)
    for p in transferList:
        top = f""
        top += f"{p[5]} GW{p[6]}: "
        top += f"IN ({p[IN_POINTS]} points): "
        for player in p[IN_PLAYERS_LIST]:
            top += f"{idToName(player)}, "
        top = top[:-2]
        top += f"|OUT ({p[OUT_POINTS]} points): "
        for player in p[OUT_PLAYERS_LIST]:
            top += f"{idToName(player)}, "
        top = top[:-2]
        top += f"|OVR - {p[IN_POINTS] - p[OUT_POINTS] - p[FINE]}"
        print(top)


def generalSeasonStats():
    #mostUniqueManager()
    #getNumberOfSubs()
    #getCosts()
    #bestTransfers()
    #bestWildcard()
    bestFreeHit()


def main():
    #mostUniqueManager()
    #bestFreeHit()
    #getCosts()
    #generalSeasonStats()
    #managerProfile(teams[0]["entry"])
    #managerProfile(teams[1]["entry"])
    #for team in teams:
    #    print(pointsByManager(team["entry"]), "\n---------\n")
    # getCaptaincy(15)
    #luckiestPlayer()
    captaincyAccuracy()
    # bestBench(11)
    # getUninqePlayers(15)
    # bestBenchOverAll()
    # bestTransfers()
    # captaincyLoses()
    # teamRepresentation(13)
    # bestWildcard()
    # pointsAllocation()


if __name__ == "__main__":

    # initial info gathering
    # --------------------------------------------------#
    gdata = fpl_api_get(GENERAL_INFO)
    sgdata = sorted(gdata["elements"], key=lambda x: x['id'])
    i = 0
    while gdata['events'][i]:
        if gdata['events'][i]['is_next']:
            currentGW = i
            break
        i += 1

    leagueID = "19528"
    ldata = getLeagueInfo(leagueID)
    teams = ldata['standings']['results']

    # ---------------------------------------------------#
    main()
