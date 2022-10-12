import time
from winsound import PlaySound
import requests
from colored import fg, attr
import datetime
import os
import tls_client
from bs4 import BeautifulSoup as bs
import sys

sys.setrecursionlimit(999999)
appToken = ""

session = tls_client.Session(
    client_identifier="chrome_105"
)

def log(msg, type):
    if type == 1:
        print(f"%s[{str(datetime.datetime.now())}]%s " % (fg(21), attr(0)) + msg)
    elif type == 2:
        print(f"%s[{str(datetime.datetime.now())}]%s " % (fg(196), attr(0)) + msg)
    elif type == 3:
        print(f"%s[{str(datetime.datetime.now())}]%s " % (fg(82), attr(0)) + msg)

def printStartScreen():
    os.system("cls")

    print("""%s
  __  __             _ _             ____  _       
 |  \/  |           (_| |           |  _ \(_)      
 | \  / | ___  _ __  _| |_ ___  _ __| |_) |_ _ __  
 | |\/| |/ _ \| '_ \| | __/ _ \| '__|  _ <| | '_ \ 
 | |  | | (_) | | | | | || (_) | |  | |_) | | | | |
 |_|  |_|\___/|_| |_|_|\__\___/|_|  |____/|_|_| |_| V0.1                                                                                                     %s""" % (fg(200), attr(0)))
    print("---------------------------------------------------------------------------")

def getPlayerDetails():
    
    playerName = input("%s[%s" % (fg(21), attr(0)) + "·" + "%s]%s" % (fg(21), attr(0)) + f"%s[INPUT]%s " % (fg(21), attr(0)) + "Player Name (As shown on card): ")
    playerRating = input("%s[%s" % (fg(21), attr(0)) + "·" + "%s]%s" % (fg(21), attr(0)) + f"%s[INPUT]%s " % (fg(21), attr(0)) + "Player Rating (As shown on card): ")
    
    print("---------------------------------------------------------------------------")
    log(f"Fetching Player {playerName} - {playerRating}", 1)
    
    response = session.get(f"https://www.futbin.com/search?year=23&v=1&term={playerName}")

    if response.status_code != 200:
        log("Error fetching player info... ", 2)
    
    playersList = response.json()

    for player in playersList:
        if playerName.lower() in (player["name"]).lower():
            if player["rating"] == playerRating:
                
                imgLink = player["image"]
                playerId = imgLink.split("/")[-1].split(".png")[0]
                futbinId = player["id"]
                displayName = player["full_name"]
                playerVersion = player["version"]

                response = session.get(f"https://www.futbin.com/23/player/{futbinId}/")

                if response.status_code == 200:
                    soup = bs(response.text, 'html.parser')

                    try:
                        specialId = soup.find("div", {"id" : "page-info"})["data-player-resource"]
                    except:
                        log("Error scraping player details", 2)

                    playerDetails = {
                        "img" : imgLink,
                        "playerId" : playerId,
                        "specialId" : specialId,
                        "playerName" : playerName,
                        "displayName" : displayName,
                        "playerVersion" : playerVersion
                    }

                    log(f"Fetched player {displayName} ({playerId})", 3)

                    return playerDetails

                else:
                    log("Error reaching futbin", 2)
                    time.sleep(1000000)

def sendAppNotification(msg):
    
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "to" : f"ExponentPushToken[{appToken}]",
        "title" : msg["playerName"] + " " + msg["cardType"],
        "body" : "Previous: " + msg["prevPrice"] + " | Now: " + msg["newPrice"]
    }

    try:

        response = requests.post("https://exp.host/--/api/v2/push/send", headers=headers, json=data)
        if response.status_code == 200:
            log("Sent notification to app...", 3)
        else:
            log("Error sending notification to app...", 2)
    
    except Exception as e:
        print("Error: " + str(e))

def monitorPlayerId(playerDetails):

    playerId = playerDetails["playerId"]
    specialId = playerDetails["specialId"]
    playerName = playerDetails["playerName"]
    prevPrice = playerDetails["prevPrice"]
    imgLink = playerDetails["img"]
    displayName = playerDetails["displayName"]
    playerVersion = playerDetails["playerVersion"]


    log(f"Getting prices for {displayName} ({playerVersion}) - Previous price: {prevPrice}", 1)

    try:
        response = session.get(f"https://www.futbin.com/23/playerPrices?player={specialId}&rids={playerId}")

    except:
        log("Error getting Futbin Price", 2)
        
        return(playerDetails)

    if response.status_code == 200:
        newPrice = response.json()[str(specialId)]["prices"]["ps"]["LCPrice"].replace(",", "")
    
    else:
        log("Error getting Futbin Price", 2)
        return prevPrice
    
    if int(prevPrice) != int(newPrice):

        notificationDetails = {
                "playerName" : str(displayName),
                "cardType" : str(playerVersion),
                "prevPrice" : str(prevPrice),
                "newPrice" : str(newPrice)
            }
        
        sendAppNotification(notificationDetails)

        return

    else:    
        time.sleep(1.5)

        playerDetails = {
                            "img" : imgLink,
                            "playerId" : playerId,
                            "specialId" : specialId,
                            "playerName" : playerName,
                            "prevPrice" : newPrice,
                            "displayName" : displayName,
                            "playerVersion" : playerVersion
                        }

        monitorPlayerId(playerDetails)
        
def getMonitoringPrice(playerDetails):

    playerId = playerDetails["playerId"]
    specialId = playerDetails["specialId"]
    playerName = playerDetails["playerName"]
    imgLink = playerDetails["img"]
    displayName = playerDetails["displayName"]
    playerVersion = playerDetails["playerVersion"]
    
    log(f"Getting prices for {displayName}", 1)

    try:
        response = session.get(f"https://www.futbin.com/23/playerPrices?player={specialId}&rids={playerId}")

    except:
        log("Error getting Futbin Price", 2)

    if response.status_code == 200:
        initialPrice = response.json()[str(specialId)]["prices"]["ps"]["LCPrice"].replace(",", "")
    
    else:
        log("Error fetching futbin price during initial process.", 2)
        time.sleep(10)
        return
    
    
    playerDetails = {
                        "img" : imgLink,
                        "playerId" : playerId,
                        "specialId" : specialId,
                        "playerName" : playerName,
                        "prevPrice" : initialPrice,
                        "displayName" : displayName,
                        "playerVersion" : playerVersion
                    }
    
    print("---------------------------------------------------------------------------")

    return(playerDetails)


def initiateFutbinMonitor():

    printStartScreen()

    playerDetails = getPlayerDetails()

    while True:
        playerDetailsWithPrice = getMonitoringPrice(playerDetails)

        monitorPlayerId(playerDetailsWithPrice)

initiateFutbinMonitor()
