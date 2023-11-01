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


def bestTransfers(startingGW=STARTING_GW):
    transferList = []
    for team in teams:
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
            tempInfo = getPlayerInfo(inPlayer)
            inPoints = tempInfo['history'][gw - 1 - (currentGW - len(tempInfo['history']))]['total_points']
            tempInfo = getPlayerInfo(outPlayer)
            outPoints = getPlayerInfo(outPlayer)['history'][gw - 1 - (currentGW - len(tempInfo['history']))][
                'total_points']
            # print (costs,gw)
            fine = 0
            if inPlayer in [p['element'] for p in getTeamGWInfo(teamID, gw)['picks'][BENCH_POS:]]:
                inPoints = 0
                outPoints = 0
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


def getCaptaincy(gw):
    for team in teams:
        data = getTeamGWInfo(team["entry"], gw)
        for player in data["picks"]:
            if player["is_captain"]:
                print(team["entry_name"], idToName(player["element"]))


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
        print (teamID)
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
    points = sorted(points, key=lambda x: x[1]-x[2], reverse=True)
    for p in points:
        print(f"{p[0]} Scored {p[1]} Points while his Xpoints is {p[2]} Lucky Points: {p[1]-p[2]}\n")


def main():
    #getCaptaincy(10)
    #getUninqePlayers(10)
    #luckiestPlayer(9)
    bestTransfers(10)


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
