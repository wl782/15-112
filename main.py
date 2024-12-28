from cmu_graphics import *
from PIL import ImageFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time 
import pandas as pd
from RandomForest_Final import RandomForest
from cmu_graphics import *
from cmu_graphics import pygameEvent

#from Austin --> following 5 lines are to handle scroll wheel
def handlePygameEvent(event, callUserFn, app):
    # pygame.MOUSEWHEEL == 1027
    if event.type == 1027:
        callUserFn('onMouseWheel', (event.x, event.y))

pygameEvent.connect(handlePygameEvent)

def getData(nameOfPlayer):
    dateOfGames = []
    data = {
    'Minutes':[],
    'Points':[],
    'FGM':[],
    'FGA':[],
    'FG%':[],
    '3PM':[],
    '3PA':[],
    '3P%':[],
    'FTM':[],
    'FTA':[],
    'FT%':[],
    'OREB':[],
    'DREB':[],
    'Rebounds':[],
    'Assists':[],
    'STL':[],
    'BLK':[],
    'TOV':[],
    'PF':[],
    '+/-':[],
}
    #learned webscraping from these series: https://www.youtube.com/watch?v=Xjv1sY630Uc&list=PLzMcBGfZo4-n40rB1XaJ0ak1bemvlqumQ, https://www.youtube.com/watch?v=b5jt2bhSeXs&list=PLzMcBGfZo4-n40rB1XaJ0ak1bemvlqumQ&index=2, and https://www.youtube.com/watch?v=U6gbGk5WPws&list=PLzMcBGfZo4-n40rB1XaJ0ak1bemvlqumQ&index=3
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get("https://www.nba.com/stats/players/boxscores?")
    try:
        cookiesButton = driver.find_element(By.XPATH, "//*[@id='onetrust-accept-btn-handler']")
        cookiesButton.click()
    except:
        pass  

    button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "CromFiltersAdd_button__WNMWN"))
        )
    button.click()
    inputSpace = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "CromFiltersInput_ddVal__ZGVeO"))
        )
    inputSpace.send_keys(nameOfPlayer) #inputing the name into the input box
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "Anchor_anchor__cSc3P"))  #wait for data to show up 
    ) 
    heading = driver.find_element(By.CLASS_NAME, 'Crom_headers__mzI_m') 
    statisticList = heading.find_elements(By.XPATH, './/th')
    tableofGames = driver.find_element(By.CLASS_NAME, 'Crom_body__UYOcU') 
    gameList = tableofGames.find_elements(By.XPATH, ".//tr")
    for game in gameList: 
        statisticList = game.find_elements(By.XPATH, ".//td") #getting the list of statistics 
        gameStat = []
        for stat in statisticList:
            if 'Crom_text__NpR1_ Crom_primary__EajZu Crom_sticky__uYvkp' in stat.get_attribute("class"):
                continue #getting rid of attributes we dont want 
            if 'Crom_text__NpR1_' in stat.get_attribute("class"):
                link = stat.find_element(By.TAG_NAME, "a") 
                href = link.get_attribute("href") 
                if '/games?date' in href:
                    dateOfGames.append(stat.text)
                if "/game/" not in href:
                    continue #getting rid of attributes we dont want 
            if 'vs.' in stat.text or '@' in stat.text or 'W' in stat.text or 'L' in stat.text: #removing the statistics not with numbers with them (helps taking the median of the each column for prediction)
                continue 
            gameStat.append(stat.text)
        for index, key in enumerate(data.keys()): 
            data[key].append(gameStat[index])
    df = pd.DataFrame(data)
    return df, dateOfGames
    
def onMouseWheel(app, dx, dy): #handling scrolling 
    if app.guidePage:
        app.scrollYGuide += dy 
        app.scrollYGuide = max(min(0, app.scrollYGuide),-480-110) #can't go above 0, and can't go below -480
    elif app.displayButtonColor == 'Season Stats' and app.pressPlayerBox:
        app.maxScroll = len(app.playerBoxScore['Minutes'])*10-10
        app.scrollY += dy
        app.scrollY = max(min(0, app.scrollY),-app.maxScroll) #canot go above 0, and can't go below "maxscroll"
        
def getOdds(nameOfPlayer, playerStat):
    oddsForPlayer = []
    driver = webdriver.Chrome()
    driver.maximize_window()

    # Navigate to the webpage
    dictOfStat = {
        "Points": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-points&subcategory=points-o%2Fu",
        "Rebounds": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-rebounds&subcategory=rebounds-o%2Fu",
        "Assists": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-assists&subcategory=assists-o%2Fu"
    }
    driver.get(dictOfStat[playerStat])

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sportsbook-event-accordion__children-wrapper"))
    )
    gameList = driver.find_elements(By.CLASS_NAME, "sportsbook-event-accordion__children-wrapper") #getting a list of th games 
    for game in gameList:
        playerList = game.find_elements(By.XPATH, ".//tr") #getting the list of players 
        for player in playerList:
            try:
                nameSpace = player.find_element(By.CLASS_NAME, "sportsbook-row-name__wrapper") #the space containing the name
                name = nameSpace.find_element(By.CLASS_NAME, "sportsbook-row-name").text
                outcomeSpace = player.find_elements(By.CLASS_NAME, 'sportsbook-outcome-cell') #the space containing the outcomes
                if nameOfPlayer != name:
                    continue 
                for index, outcome in enumerate(outcomeSpace): #there are two "outcomes"; over and under 
                    line = outcome.find_element(By.CLASS_NAME, 'sportsbook-outcome-cell__line').text #accessing the line
                    odds = outcome.find_element(By.CLASS_NAME, 'sportsbook-odds').text #accessing the odds
                    oddsForPlayer.append(('Over', line, odds)) if index == 0 else oddsForPlayer.append(('Under', line, odds))
            except:
                continue #Handling a weird edge case that occurs before the first name in each "nameSpace"
    return oddsForPlayer 

def getDataFrame(name, playerStat, dataFrameForPlayer):
    oddsForPlayer = getOdds(name, playerStat)
    #dataFrameForPlayer = getData(name)
    underList = [1 if float(stat) < float(oddsForPlayer[1][1]) else 0 for stat in dataFrameForPlayer[playerStat]] #The points were under that what the line projected
    overList = [1 if float(stat) >= float(oddsForPlayer[0][1]) else 0 for stat in dataFrameForPlayer[playerStat]] #The points were over that what the line projected
    dataFrameForPlayer["PointsUnder"] = underList
    dataFrameForPlayer["PointsOver"] = overList
    #Y = dataFrameForPlayer.iloc[:,-1] 
    return dataFrameForPlayer, oddsForPlayer

def getInformation(playerName):
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get("https://www.nba.com/players")

    test = driver.find_element(By.CLASS_NAME, "Block_blockAd__1Q_77") 
    inputSpace = WebDriverWait(test, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "Input_input__7s5ug")) 
        )
    inputSpace.send_keys(playerName) #inputing the name into the input box
    time.sleep(2) 
    secondName = driver.find_elements(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/main/div[2]/section/div/div[2]/div[2]/div/div/div/table/tbody/tr[2]')

    if secondName != []: #if there is a second Name
        return None, None, None, None, None
    image = driver.find_element (By.XPATH, "//*[@id='__next']/div[2]/div[2]/main/div[2]/section/div/div[2]/div[2]/div/div/div/table/tbody/tr/td[1]/a/div[1]/img") 
    team = driver.find_element(By.XPATH, "//*[@id='__next']/div[2]/div[2]/main/div[2]/section/div/div[2]/div[2]/div/div/div/table/tbody/tr[1]/td[2]/a").text
    position = driver.find_element(By.XPATH, "//*[@id='__next']/div[2]/div[2]/main/div[2]/section/div/div[2]/div[2]/div/div/div/table/tbody/tr[1]/td[4]").text
    firstName = driver.find_element(By.XPATH, "//*[@id='__next']/div[2]/div[2]/main/div[2]/section/div/div[2]/div[2]/div/div/div/table/tbody/tr/td[1]/a/div[2]/p[1]").text
    lastName = driver.find_element(By.XPATH, "//*[@id='__next']/div[2]/div[2]/main/div[2]/section/div/div[2]/div[2]/div/div/div/table/tbody/tr/td[1]/a/div[2]/p[2]").text
    pngFile = image.get_attribute('src')
    return team, position, pngFile, firstName, lastName

def onAppStart(app):
    app.paused = False
    app.stepsPerSecond = 2
    app.counter = 0
    app.inputBoxWidth = (app.width - app.width//5)
    app.inputBoxHeight = 30
    app.inputBoxRadius = (1/40)*app.inputBoxWidth
    app.xCoordinateBox = 20
    app.yCoordinateBox = 20
    app.borderWidth = 1
    app.cursorInBox = False 
    app.input = ''
    app.cursor = True #tracks the blinking of the cursor 
    app.url = None
    app.search = False 
    app.team = None
    app.position = None
    app.firstName = None
    app.lastName = None
    app.pressPlayerBox = False 
    app.shiftDown = 110 #shifting the buttons down (probably should make into argument)
    app.displayButton = 'Season Stats'
    app.displayButtonColor = 'Season Stats'
    app.pressExitButton = False 
    app.hoverOverExitButton = False
    app.playerPointsOdds = [] 
    app.playerReboundsOdds = [] 
    app.playerAssistsOdds = []
    app.dataFramePoints = None
    app.dataFrameRebounds = None
    app.dataFrameAssists = None
    app.nTrees = 15
    app.playerData = None 
    app.oddsForPlayerPoints = None
    app.oddsForPlayerRebounds = None 
    app.oddsForPlayerAssists = None 
    app.gameDates = None
    app.scrollY = 0
    app.maxScroll = 180
    app.playerBoxScore = None
    app.guidePage = False 
    app.scrollYGuide = 0
    app.introductionPage = True 
    app.start = True 
    app.hoverOverExitButtonHome = False #for the homePage 
    app.hoverOverStart = False
    app.hoverOverExitButtonGuide = False 
    app.hoverOverGuide = False 
    app.noGames = False 
    app.hoverOverPlayer = False
    app.noName = True 

def drawIntroductionPage(app):
    drawLabel('NBA Betting Odds', app.width//2, 100, size = 40, bold = True, align = 'center')
    #stretchX, offsetY, stretchY, offsetX
    drawBoxHomePage(app, -50, 150, 20, 56)
    drawBoxHomePage(app, -50, 230, 20, 56)
    if app.hoverOverStart:
        drawLabel('Start', app.width//2, 195, size = 30, bold = True )
    else:
        drawLabel('Start', app.width//2, 195, size = 30, bold = True, fill = 'lightgrey')
    if app.hoverOverGuide:
        drawLabel('Guide', app.width//2, 275, size = 30, bold = True )
    else:
        drawLabel('Guide', app.width//2, 275, size = 30, bold = True, fill = 'lightgrey')

def drawGuidePage(app):
    drawExitButton(app)
    drawLabel('Overview.', 15,30 + app.scrollYGuide, size = 15, bold = True, align = 'left')
    drawLabel('This program will help you find out whether or not the NBA odds', 20,50 + app.scrollYGuide, size = 13, align = 'left')
    drawLabel('for the night are worth betting on. The program will allow you', 20,70 + app.scrollYGuide, size = 13,align = 'left')
    drawLabel("to search for a specific NBA player, and then look at the player", 20,90 + app.scrollYGuide, size = 13, align = 'left')
    drawLabel("over/under lines.", 20,110 + app.scrollYGuide, size = 13, align = 'left')

    #Drawing Step 1
    drawLabel('1.', 20,30 + 110 + app.scrollYGuide, size = 15, bold = True)
    drawBoxHomePage(app, 0,30+ app.scrollYGuide + 110,0,0)
    drawLabel('LeBron James', 75, 65+ app.scrollYGuide + 110, size = 15)
    drawLine(125, 55+ app.scrollYGuide + 110, 125, 55+app.inputBoxHeight - app.inputBoxRadius+ app.scrollYGuide + 110, lineWidth = 1, fill = 'black')
    drawLine(80,80+ app.scrollYGuide + 110,100,100+ app.scrollYGuide + 110, arrowStart = True, fill = 'red')
    drawLabel('Please type in the player who you want to search for', 60, 115+ app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('Then, press "enter"', 60, 133+ app.scrollYGuide + 110, align = 'left', size = 13)

    #Drawing Step 2
    drawLabel('2.', 20,170+ app.scrollYGuide + 110, size = 15, bold = True)
    drawImage('https://cdn.nba.com/headshots/nba/latest/260x190/2544.png', app.xCoordinateBox, app.yCoordinateBox + 50 +120 + app.scrollYGuide + 110, width = 100*26/19, height = 100)
    drawLabel('LeBron James', app.inputBoxWidth/2 + 70, app.yCoordinateBox + 80+120+ app.scrollYGuide + 110, size = 25)
    drawLabel(f'F - LAL', app.inputBoxWidth/2 + 70, app.yCoordinateBox + 105+120+ app.scrollYGuide + 110)
    drawBoxHomePage(app, 10, 50+120+ app.scrollYGuide + 110, 70,0 )
    drawLine(170,280+ app.scrollYGuide + 110,145,305+ app.scrollYGuide + 110, arrowStart = True, fill = 'red')
    drawLabel('Press inside the box. You will be taken to a different page', 30, 320+ app.scrollYGuide + 110, align = 'left', size = 13)

    #Drawing Step 3
    drawLabel('3.', 20,350+ app.scrollYGuide + 110, size = 15, bold = True)
    drawBigBox(app, 7, 0+app.scrollYGuide + 260 + 110)
    drawSmallBox(app, 0, 205, 0 + app.scrollYGuide + 260 + 110)

    #drawing the words in the buttons 
    drawLabel('Season Stats', 67, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) + app.scrollYGuide + 260 + 110, font  = 'Arial', size = 14, fill = 'blue')
    drawLabel('Points', 150, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) + app.scrollYGuide + 260 + 110, font  = 'Arial', size = 14)
    drawLabel('Rebounds', 220, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) + app.scrollYGuide + 260 + 110, font  = 'Arial', size = 14)
    drawLabel('Assists', 295, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) + app.scrollYGuide + 260 + 110, font  = 'Arial', size = 14)
    drawLabel ('In the new page, you will see multiple buttons:', 20, 370 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLine (80, 420 + app.scrollYGuide + 110, 100, 440 + app.scrollYGuide + 110, arrowStart = True, fill = 'red')
    drawLabel('The page will initially be on Season Stats', 20, 450 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('Press on the different buttons to navigate around', 20, 470 + app.scrollYGuide + 110, align = 'left', size = 13)


    #Drawing Step 4
    drawLabel('4.', 20, 500+ app.scrollYGuide + 110, size = 15, bold = True)
    drawBigBox(app, 7, 0+app.scrollYGuide + 410 + 110)
    drawSmallBox(app, 165, 230,0+ app.scrollYGuide + 410 + 110)
    drawLabel('In the Points, Rebounds, Assists page, you will see this:', 20, 520 +  app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('Season Stats', 67, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) + app.scrollYGuide + 410 + 110, font  = 'Arial', size = 14)
    drawLabel('Points', 150, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) + app.scrollYGuide + 410 + 110, font  = 'Arial', size = 14)
    drawLabel('Rebounds', 220, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) + app.scrollYGuide + 410 + 110, font  = 'Arial', size = 14 , fill = 'blue')
    drawLabel('Assists', 295, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) + app.scrollYGuide + 410 + 110, font  = 'Arial', size = 14)
    drawLabel('Prop     Proj        Odd      Cover Prob.', 30, 590 + app.scrollYGuide + 110, size = 18, align = 'left')
    drawLabel(f'Over    O 6.5     -120', 30, 590 + 30 + app.scrollYGuide + 110, size = 18, align = 'left')
    drawLabel(f'80%', 270, 590 + 30 + app.scrollYGuide + 110, size = 18, fill = 'green')
    drawLabel(f'Under  U 6.5     -110', 30, 590 + 60 + app.scrollYGuide + 110, size = 18, align = 'left')
    drawLabel(f'10%', 270, 590 + 60 + app.scrollYGuide + 110, size = 18, fill = 'red')
    drawLine (250, 660 + app.scrollYGuide + 110, 235, 680 + app.scrollYGuide + 110, arrowStart = True, fill = 'red')
    drawLabel('These probabilities are calculated via a Random Forest', 20, 690 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('Algorithm. A total of 15 trees are in the Forest. Considering the', 20, 710 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('small size of the dataset (and to reduce run-time), I limited', 20, 730 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('the number of trees to 15. I took the majority outcome of the trees', 20, 750 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('as the result, and then got the cover probability by weighing the', 20, 770 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('outcomes of the over/under with the total number of trees.', 20, 790 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('The algorithm was used to estimate the probability of each line', 20, 810 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('of each statistic (points, rebounds...) individually, which often led', 20, 830 + app.scrollYGuide + 110, align = 'left', size = 13)
    drawLabel('to the probablities of the over/under not adding up to 100%', 20, 850 + app.scrollYGuide + 110, align = 'left', size = 13)

def redrawAll(app):
    if app.introductionPage:
        drawIntroductionPage(app)
    elif app.guidePage:
        drawGuidePage(app)
    elif app.pressPlayerBox:
        drawPlayerPage(app)
    else:
        drawHomePage(app)

def drawBigBox(app, stretch, offsetY):
    #top line 
    drawLine(app.xCoordinateBox+app.inputBoxRadius, app.yCoordinateBox + app.inputBoxHeight + app.shiftDown +offsetY, app.inputBoxWidth-app.inputBoxRadius + stretch, app.yCoordinateBox + app.inputBoxHeight + app.shiftDown + offsetY, lineWidth = app.borderWidth, fill = 'black')
    drawLine(app.xCoordinateBox+app.inputBoxRadius, app.yCoordinateBox + app.shiftDown+ offsetY, app.inputBoxWidth-app.inputBoxRadius + stretch, app.yCoordinateBox + app.shiftDown+ offsetY, lineWidth = app.borderWidth)
    
    #top left
    drawArc(app.xCoordinateBox+app.inputBoxRadius, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown+ offsetY, app.inputBoxHeight+2, app.inputBoxHeight+2, 90, 90, fill = None, border = 'grey', borderWidth = 2)
    drawArc(app.xCoordinateBox+app.inputBoxRadius, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown+ offsetY, app.inputBoxHeight-2, app.inputBoxHeight-2, 90, 90, fill = 'white')
    
    #bottom left
    drawArc(app.xCoordinateBox+app.inputBoxRadius, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown+ offsetY, app.inputBoxHeight+2, app.inputBoxHeight+2, 180, 90, fill = None, border = 'grey', borderWidth = 2)
    drawArc(app.xCoordinateBox+app.inputBoxRadius, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown+ offsetY, app.inputBoxHeight-2, app.inputBoxHeight-2, 180, 90, fill = 'white')
    
    #bottom right
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown+ offsetY, app.inputBoxHeight+2, app.inputBoxHeight+2, 270, 90, fill = None, border = 'grey', borderWidth = 2)
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown+ offsetY, app.inputBoxHeight-2, app.inputBoxHeight-2, 270, 90, fill = 'white')
    
    #top right 
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown+ offsetY, app.inputBoxHeight+2, app.inputBoxHeight+2, 0, 90, fill = None, border = 'grey', borderWidth = 2)
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown+ offsetY, app.inputBoxHeight-2, app.inputBoxHeight-2, 0, 90, fill = 'white')
    
def drawSmallBox(app, move, shorten, offsetY):
    #move = offsetX 
    #similar code to drawBigBox but includes an offset (because I want it to be a little smaller )
    drawLine(app.xCoordinateBox+app.inputBoxRadius + move, app.yCoordinateBox + app.inputBoxHeight + app.shiftDown - 3  + offsetY, app.inputBoxWidth-app.inputBoxRadius - shorten + move, app.yCoordinateBox + app.inputBoxHeight + app.shiftDown - 3 + offsetY, lineWidth = app.borderWidth, fill = 'lightgrey')
    drawLine(app.xCoordinateBox+app.inputBoxRadius + move, app.yCoordinateBox + app.shiftDown + 3 + offsetY, app.inputBoxWidth-app.inputBoxRadius - shorten + move, app.yCoordinateBox + app.shiftDown + 3  + offsetY, lineWidth = app.borderWidth, fill = 'lightgrey')
    
    #top left
    drawArc(app.xCoordinateBox+app.inputBoxRadius + move, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown  + offsetY, app.inputBoxHeight-4, app.inputBoxHeight-4, 90, 90, fill = None, border = 'lightgrey', borderWidth = 2)
    drawArc(app.xCoordinateBox+app.inputBoxRadius + move, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown  + offsetY, app.inputBoxHeight - 8, app.inputBoxHeight-8, 90, 90, fill = 'white')
    
    #bottom left
    drawArc(app.xCoordinateBox+app.inputBoxRadius + move, app.yCoordinateBox  + offsetY + app.inputBoxHeight/2 + app.shiftDown, app.inputBoxHeight-4, app.inputBoxHeight-4, 180, 90, fill = None, border = 'lightgrey', borderWidth = 2)
    drawArc(app.xCoordinateBox+app.inputBoxRadius + move, app.yCoordinateBox + offsetY + app.inputBoxHeight/2 + app.shiftDown, app.inputBoxHeight-8, app.inputBoxHeight-8, 180, 90, fill = 'white')
    
    #bottom right
    drawArc(app.inputBoxWidth-app.inputBoxRadius - shorten + move, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown + offsetY, app.inputBoxHeight-4, app.inputBoxHeight-4, 270, 90, fill = None, border = 'lightgrey', borderWidth = 2)
    drawArc(app.inputBoxWidth-app.inputBoxRadius - shorten + move, app.yCoordinateBox  + app.inputBoxHeight/2 + app.shiftDown + offsetY, app.inputBoxHeight-8, app.inputBoxHeight-8, 270, 90, fill = 'white')
    
    #top right 
    drawArc(app.inputBoxWidth-app.inputBoxRadius - shorten + move, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown  + offsetY, app.inputBoxHeight-4 , app.inputBoxHeight-4, 0, 90, fill = None, border = 'lightgrey', borderWidth = 2)
    drawArc(app.inputBoxWidth-app.inputBoxRadius - shorten + move, app.yCoordinateBox + app.inputBoxHeight/2 + app.shiftDown + offsetY, app.inputBoxHeight-8, app.inputBoxHeight-8, 0, 90, fill = 'white')
    
def drawExitButton(app):
    if app.hoverOverExitButton or app.hoverOverExitButtonHome or app.hoverOverExitButtonGuide:
        drawLine (357.5, 30, 372.5, 30, rotateAngle = 45, fill = 'black')
        drawLine (357.5, 30, 372.5, 30, rotateAngle = 135, fill = 'black')
        drawCircle(365, 30, 15, fill = None, border = 'black')
    else:
        drawLine (357.5, 30, 372.5, 30, rotateAngle = 45, fill = 'grey')
        drawLine (357.5, 30, 372.5, 30, rotateAngle = 135, fill = 'grey')
        drawCircle(365, 30, 15, fill = None, border = 'grey')
 
def drawStatBox(app):
    for index, row in enumerate(app.playerBoxScore['Minutes']):
        drawLabel(f'{app.gameDates[index]}', 48, 195+index*20+app.scrollY, size = 13)
        drawLabel(row, 120, 195+index*20+app.scrollY, size = 13) 
        drawLine(18, 185+index*20+app.scrollY, 340, 185+index*20+app.scrollY, fill = 'lightgrey')

    for index, row in enumerate(app.playerBoxScore['Points']):
        drawLabel(row, 180, 195+index*20+app.scrollY, size = 13) 

    for index, row in enumerate(app.playerBoxScore['Rebounds']):
        drawLabel(row, 245, 195+index*20+app.scrollY, size = 13) 

    for index, row in enumerate(app.playerBoxScore['Assists']):
        drawLabel(row, 310, 195+index*20+app.scrollY, size = 13) 
    

    scrollMove = -176*app.scrollY/app.maxScroll #176 comes from the lower bound (187) and the upperBound (363)
    drawRect(0,0, app.width, 185, fill = 'white') #covering the data - handles scrolling; draws this first before everything (excluding the boxscore)
    drawLabel('Minutes     Points     Rebounds     Assists', 100, 175, size = 13, align = 'left') 
    drawRect(360, 185, 10, 210, fill = None, border = 'grey', borderWidth = 1) #scroll bar
    drawRect(362, 187+scrollMove, 6, 30, fill = 'grey') #scroll rect; offset by 2

def drawPlayerPage(app):
    if app.displayButtonColor == 'Season Stats':
        drawStatBox(app) 
    elif app.displayButtonColor == 'Points':
        if app.noGames:
            drawLabel(f'{app.firstName} {app.lastName} does not play tonight', 175, 190, size = 15)
        else:
            probOver = int(app.playerPointsOdds[0][1] * 100)
            if 0 <= probOver <= 33:
                probOverfill = 'red'
            elif 33<probOver <= 66:
                probOverfill = 'orange'
            elif 66<probOver <= 100:
                probOverfill = 'green'
            probUnder = int(app.playerPointsOdds[1][1] * 100)
            if 0 < probUnder <= 33:
                probUnderfill = 'red'
            elif 33<probUnder <= 66:
                probUnderfill = 'orange'
            elif 66<probUnder <= 100:
                probUnderfill = 'green'
            drawLabel('Prop     Proj        Odd      Cover Prob.', 30, 180, size = 18, align = 'left')
            drawLabel(f'Over    O {app.oddsForPlayerPoints[0][1]}    {app.oddsForPlayerPoints[0][2]}', 30, 210, size = 18, align = 'left')
            drawLabel(f'{probOver}%', 270, 210, size = 18, fill = probOverfill)
            drawLabel(f'Under  U {app.oddsForPlayerPoints[1][1]}    {app.oddsForPlayerPoints[1][2]}', 30, 240, size = 18, align = 'left')
            drawLabel(f'{probUnder}%', 270, 240, size = 18, fill = probUnderfill)
    elif app.displayButtonColor == 'Rebounds':
        if app.noGames:
            drawLabel(f'{app.firstName} {app.lastName} does not play tonight', 175, 190, size = 15)
        else:
            probOver = int(app.playerReboundsOdds[0][1] * 100)
            if 0 < probOver <= 33:
                probOverfill = 'red'
            elif 33<probOver <= 66:
                probOverfill = 'orange'
            elif 66<probOver <= 100:
                probOverfill = 'green'
            probUnder = int(app.playerReboundsOdds[1][1] * 100)
            if 0 < probUnder <= 33:
                probUnderfill = 'red'
            elif 33<probUnder <= 66:
                probUnderfill = 'orange'
            elif 66<probUnder <= 100:
                probUnderfill = 'green'
            drawLabel('Prop     Proj        Odd      Cover Prob.', 30, 180, size = 18, align = 'left')
            drawLabel(f'Over    O {app.oddsForPlayerRebounds[0][1]}    {app.oddsForPlayerRebounds[0][2]}', 30, 210, size = 18, align = 'left')
            drawLabel(f'{probOver}%', 270, 210, size = 18, fill = probOverfill)
            drawLabel(f'Under  U {app.oddsForPlayerRebounds[1][1]}    {app.oddsForPlayerRebounds[1][2]}', 30, 240, size = 18, align = 'left')
            drawLabel(f'{probUnder}%', 270, 240, size = 18, fill = probUnderfill)
    elif app.displayButtonColor == 'Assists':
        if app.noGames:
            drawLabel(f'{app.firstName} {app.lastName} does not play tonight', 175, 190, size = 15)
        else:
            probOver = int(app.playerAssistsOdds[0][1] * 100)
            if 0 < probOver <= 33:
                probOverfill = 'red'
            elif 33<probOver <= 66:
                probOverfill = 'orange'
            elif 66<probOver <= 100:
                probOverfill = 'green'
            probUnder = int(app.playerAssistsOdds[1][1] * 100)
            if 0 < probUnder <= 33:
                probUnderfill = 'red'
            elif 33<probUnder <= 66:
                probUnderfill = 'orange'
            elif 66<probUnder <= 100:
                probUnderfill = 'green'
            drawLabel('Prop     Proj        Odd      Cover Prob.', 30, 180, size = 18, align = 'left')
            drawLabel(f'Over    O {app.oddsForPlayerAssists[0][1]}    {app.oddsForPlayerAssists[0][2]}', 30, 210, size = 18, align = 'left')
            drawLabel(f'{probOver}%', 270, 210, size = 18, fill = probOverfill)
            drawLabel(f'Under  U {app.oddsForPlayerAssists[1][1]}    {app.oddsForPlayerAssists[1][2]}', 30, 240, size = 18, align = 'left')
            drawLabel(f'{probUnder}%', 270, 240, size = 18, fill = probUnderfill)
    drawExitButton(app)
    #draw the player box 
    drawImage(app.url, app.xCoordinateBox, app.yCoordinateBox, width = 100*26/19, height = 100)
    if len(app.firstName + app.lastName) > 15:
        sizeName = 17
    else:
        sizeName = 25
    drawLabel(f'{app.firstName} {app.lastName}', app.inputBoxWidth/2 + 70, app.yCoordinateBox + 30, size = sizeName)
    drawLabel(f'{app.position}  - {app.team}', app.inputBoxWidth/2 + 70, app.yCoordinateBox + 55)
    drawBoxHomePage(app, 10, 0, 70,0 )
    
    # the labels for the buttons
    drawBigBox(app, 7,0)

    #drawing the grey boxes around the buttons 
    if app.displayButton == 'Season Stats' or app.displayButtonColor == 'Season Stats':
        drawSmallBox(app, 0, 205,0)
    if app.displayButton == 'Points' or app.displayButtonColor == 'Points':
        drawSmallBox(app, 105, 250,0)
    if app.displayButton == 'Rebounds' or app.displayButtonColor == 'Rebounds':
        drawSmallBox(app, 165, 230,0)
    if app.displayButton == 'Assists' or app.displayButtonColor == 'Assists':
        drawSmallBox(app, 245, 238,0)

    #drawing the words in the buttons 
    if app.displayButtonColor == 'Season Stats':
        drawLabel('Season Stats', 67, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) , font  = 'Arial', size = 14, fill = 'blue')
    else:
        drawLabel('Season Stats', 67, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2) , font  = 'Arial', size = 14)
    if app.displayButtonColor == 'Points':
        drawLabel('Points', 150, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2), font  = 'Arial', size = 14, fill = 'blue')
    else:
        drawLabel('Points', 150, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2), font  = 'Arial', size = 14)
    if app.displayButtonColor == 'Rebounds':
        drawLabel('Rebounds', 220, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2), font  = 'Arial', size = 14, fill = 'blue')
    else:
        drawLabel('Rebounds', 220, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2), font  = 'Arial', size = 14)
    if app.displayButtonColor == 'Assists':
        drawLabel('Assists', 295, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2), font  = 'Arial', size = 14, fill = 'blue')
    else:
        drawLabel('Assists', 295, app.yCoordinateBox + app.shiftDown + (app.inputBoxHeight / 2), font  = 'Arial', size = 14)

def drawBoxHomePage(app, stretch, offsetY, stretchY, offsetX):
    #bottom, then top
    drawLine(app.xCoordinateBox+app.inputBoxRadius + offsetX, app.yCoordinateBox + app.inputBoxHeight + offsetY + stretchY, app.inputBoxWidth-app.inputBoxRadius + stretch + offsetX, app.yCoordinateBox + app.inputBoxHeight + offsetY + stretchY, lineWidth = app.borderWidth, fill = 'black')
    drawLine(app.xCoordinateBox+app.inputBoxRadius + offsetX, app.yCoordinateBox + offsetY, app.inputBoxWidth-app.inputBoxRadius + stretch + offsetX, app.yCoordinateBox + offsetY, lineWidth = app.borderWidth )
    
    #vertical lines 
    drawLine(app.xCoordinateBox + offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.xCoordinateBox +offsetX, app.yCoordinateBox+app.inputBoxHeight-app.inputBoxRadius + offsetY + stretchY, lineWidth = app.borderWidth )
    drawLine(app.inputBoxWidth + stretch + offsetX,  app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxWidth + stretch+offsetX, app.yCoordinateBox+app.inputBoxHeight-app.inputBoxRadius + offsetY + stretchY, lineWidth = app.borderWidth )
    
    #top Left
    drawArc(app.xCoordinateBox+app.inputBoxRadius +offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxRadius*2+2, app.inputBoxRadius*2+2, 90, 90, fill = None, border = 'grey', borderWidth = 2)
    drawArc(app.xCoordinateBox+app.inputBoxRadius+offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxRadius*2-2, app.inputBoxRadius*2-2, 90, 90, fill = 'white')
    
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch+offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxRadius*2+2, app.inputBoxRadius*2+2, 0, 90, fill = None, border = 'grey', borderWidth = 2)
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch +offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxRadius*2-2, app.inputBoxRadius*2-2, 0, 90, fill = 'white')
    
    #bottom right
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch+offsetX, app.inputBoxHeight+app.yCoordinateBox-app.inputBoxRadius + stretchY + offsetY, app.inputBoxRadius*2+2, app.inputBoxRadius*2+2, 270, 90, fill = None, border = 'grey', borderWidth = 2)
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch+offsetX, app.inputBoxHeight+app.yCoordinateBox-app.inputBoxRadius + stretchY + offsetY, app.inputBoxRadius*2-2, app.inputBoxRadius*2-2, 270, 90, fill = 'white')

    #bottom left
    drawArc(app.xCoordinateBox+app.inputBoxRadius+offsetX, app.inputBoxHeight+app.yCoordinateBox-app.inputBoxRadius + offsetY + stretchY, app.inputBoxRadius*2+2, app.inputBoxRadius*2+2, 180, 90, fill = None, border = 'grey', borderWidth = 2)
    drawArc(app.xCoordinateBox+app.inputBoxRadius+offsetX, app.inputBoxHeight+app.yCoordinateBox-app.inputBoxRadius + offsetY + stretchY, app.inputBoxRadius*2-2, app.inputBoxRadius*2-2, 180, 90, fill = 'white')

def drawBoxHomePageHover(app, stretch, offsetY, stretchY, offsetX):
    drawLine(app.xCoordinateBox+app.inputBoxRadius + offsetX, app.yCoordinateBox + app.inputBoxHeight + offsetY + stretchY, app.inputBoxWidth-app.inputBoxRadius + stretch + offsetX, app.yCoordinateBox + app.inputBoxHeight + offsetY + stretchY, lineWidth = 2, fill = 'black')
    drawLine(app.xCoordinateBox+app.inputBoxRadius + offsetX, app.yCoordinateBox + offsetY, app.inputBoxWidth-app.inputBoxRadius + stretch + offsetX, app.yCoordinateBox + offsetY, lineWidth = 2 )
    
    #vertical lines 
    drawLine(app.xCoordinateBox + offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.xCoordinateBox +offsetX, app.yCoordinateBox+app.inputBoxHeight-app.inputBoxRadius + offsetY + stretchY, lineWidth = 2, fill = 'black')
    drawLine(app.inputBoxWidth + stretch + offsetX,  app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxWidth + stretch+offsetX, app.yCoordinateBox+app.inputBoxHeight-app.inputBoxRadius + offsetY + stretchY, lineWidth = 2, fill = 'black')
    
    #top Left
    drawArc(app.xCoordinateBox+app.inputBoxRadius +offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxRadius*2+2, app.inputBoxRadius*2+2, 90, 90, fill = None, border = 'black', borderWidth = 2)
    drawArc(app.xCoordinateBox+app.inputBoxRadius+offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxRadius*2-2, app.inputBoxRadius*2-2, 90, 90, fill = 'white')
    
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch+offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxRadius*2+2, app.inputBoxRadius*2+2, 0, 90, fill = None, border = 'black', borderWidth = 2)
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch +offsetX, app.yCoordinateBox+app.inputBoxRadius + offsetY, app.inputBoxRadius*2-2, app.inputBoxRadius*2-2, 0, 90, fill = 'white')
    
    #bottom right
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch+offsetX, app.inputBoxHeight+app.yCoordinateBox-app.inputBoxRadius + stretchY + offsetY, app.inputBoxRadius*2+2, app.inputBoxRadius*2+2, 270, 90, fill = None, border = 'black', borderWidth = 2)
    drawArc(app.inputBoxWidth-app.inputBoxRadius + stretch+offsetX, app.inputBoxHeight+app.yCoordinateBox-app.inputBoxRadius + stretchY + offsetY, app.inputBoxRadius*2-2, app.inputBoxRadius*2-2, 270, 90, fill = 'white')

    #bottom left
    drawArc(app.xCoordinateBox+app.inputBoxRadius+offsetX, app.inputBoxHeight+app.yCoordinateBox-app.inputBoxRadius + offsetY + stretchY, app.inputBoxRadius*2+2, app.inputBoxRadius*2+2, 180, 90, fill = None, border = 'black', borderWidth = 2)
    drawArc(app.xCoordinateBox+app.inputBoxRadius+offsetX, app.inputBoxHeight+app.yCoordinateBox-app.inputBoxRadius + offsetY + stretchY, app.inputBoxRadius*2-2, app.inputBoxRadius*2-2, 180, 90, fill = 'white')

def drawHomePage(app):
    font = ImageFont.truetype("Arial", 15)
    width = font.getlength(app.input)
    drawBoxHomePage(app, 0, 0, 0,0 ) #drawing input box
    drawLabel(app.input, app.xCoordinateBox+app.inputBoxRadius+width/2, app.yCoordinateBox+app.inputBoxHeight/2, align = 'center', size = 15) #align center seems to work smoother than align left
    drawExitButton(app)
    if app.cursor and app.cursorInBox:
        drawLine(app.xCoordinateBox+width+app.inputBoxRadius+2, app.yCoordinateBox+app.inputBoxRadius, app.xCoordinateBox+width+app.inputBoxRadius+2, app.yCoordinateBox+app.inputBoxHeight-app.inputBoxRadius, lineWidth = 1, fill = 'black')
    if app.search and not app.noName:
        #drawing the box showing the player 
        if len(app.firstName + app.lastName) > 15:
            sizeName = 17
        else:
            sizeName = 25
        drawImage(app.url, app.xCoordinateBox, app.yCoordinateBox + 50, width = 100*26/19, height = 100)
        drawLabel(f'{app.firstName} {app.lastName}', app.inputBoxWidth/2 + 70, app.yCoordinateBox + 80, size = sizeName)
        drawLabel(f'{app.position}  - {app.team}', app.inputBoxWidth/2 + 70, app.yCoordinateBox + 105)
        if app.hoverOverPlayer:
            pass 
            drawBoxHomePageHover(app, 10, 50, 70,0)
        else:
            drawBoxHomePage(app, 10, 50, 70,0)
    elif app.search and app.noName:
        drawLabel('There are no players with the name you entered', 20, 80, size = 17, align = 'left')

def onKeyPress (app, key):
    app.cursor = True 
    if app.cursorInBox and not app.introductionPage:
        if key == 'enter':
            app.noName = False 
            app.search = True 
            app.team, app.position, app.url, app.firstName, app.lastName = getInformation(app.input)
            if app.team == None:
                app.noName = True 
        elif key == 'space':
            app.input += ' '
        elif key == 'backspace':
            app.input = app.input[:-1]
        elif key.isalpha():
            app.input += key

def onMousePress(app, mouseX, mouseY):  
    if app.introductionPage: #for introduction page; most of this code is just navigating between pages 
        if app.hoverOverStart:
            app.introductionPage = False 
        if app.hoverOverGuide:
            app.guidePage = True 
            app.introductionPage = False 
    elif app.guidePage:
        if app.hoverOverExitButtonGuide:
            app.guidePage = False 
            app.introductionPage = True 
            app.hoverOverExitButtonGuide = False 
            app.hoverOverGuide = False 
    elif not app.pressPlayerBox: #split into two pages: this is for the homepage
        if app.hoverOverExitButtonHome:  #if pressing exit Button
            app.introductionPage = True
            app.hoverOverStart = False 
            app.hoverOverExitButtonHome = False 
        elif app.xCoordinateBox+app.inputBoxRadius<=mouseX<=app.xCoordinateBox-app.inputBoxRadius+app.inputBoxWidth and \
                app.yCoordinateBox+app.inputBoxRadius<=mouseY<=app.yCoordinateBox-app.inputBoxRadius+app.inputBoxHeight:
            app.cursorInBox = True 
        else:
            app.cursorInBox = False 

        #if pressing in the player box 
        if (app.xCoordinateBox<=mouseX<=app.inputBoxWidth+app.xCoordinateBox and app.yCoordinateBox + 50<=mouseY<=app.yCoordinateBox + 50 + app.inputBoxHeight*3) and app.search and not app.noName:
            app.pressPlayerBox = True 
            if app.playerData == None:
                app.playerData, app.gameDates = getData(f'{app.firstName} {app.lastName}')
                app.playerBoxScore =  { #a minidataFrame
                    'Minutes':[],
                    'Points':[],
                    'Rebounds':[],
                    'Assists':[],
                }
                for row in app.playerData['Points']: 
                    app.playerBoxScore ['Points'].append(row)
                for row in app.playerData['Rebounds']:
                    app.playerBoxScore ['Rebounds'].append(row)
                for row in app.playerData['Assists']:
                    app.playerBoxScore ['Assists'].append(row)
                for row in app.playerData['Minutes']:
                    app.playerBoxScore ['Minutes'].append(row)
    else: #this is for the player page 
        #if pressing one of the stat buttons 
        if app.displayButton == 'Season Stats':
            app.displayButtonColor = 'Season Stats'
        elif app.displayButton == 'Points':
            app.noGames = False 
            app.displayButtonColor = 'Points'
            if app.dataFramePoints is None: #works like this so that the forest won't run every time the user switches between tabs
                try:
                    app.dataFramePoints, app.oddsForPlayerPoints = getDataFrame(f'{app.firstName} {app.lastName}', 'Points', app.playerData) 
                    randomForest = RandomForest (app.nTrees, app.dataFramePoints, 'Over')
                    randomForest.train()
                    app.playerPointsOdds.append(randomForest.predict())
                    randomForest = RandomForest (app.nTrees, app.dataFramePoints, 'Under')
                    randomForest.train() 
                    app.playerPointsOdds.append(randomForest.predict())
                except:
                    app.noGames = True #if fails, means there are no data in the last two columns (no odds for the night)
        elif app.displayButton == 'Rebounds':
            app.displayButtonColor = 'Rebounds'
            app.noGames = False 
            if app.dataFrameRebounds is None:
                try:
                    app.dataFrameRebounds, app.oddsForPlayerRebounds = getDataFrame(f'{app.firstName} {app.lastName}', 'Rebounds', app.playerData) 
                    randomForest = RandomForest (app.nTrees, app.dataFrameRebounds, 'Over')
                    randomForest.train()
                    app.playerReboundsOdds.append(randomForest.predict())
                    randomForest = RandomForest (app.nTrees, app.dataFrameRebounds, 'Under')
                    randomForest.train()
                    app.playerReboundsOdds.append(randomForest.predict())
                except:
                    app.noGames = True 
        elif app.displayButton == 'Assists':
            app.displayButtonColor = 'Assists'
            app.noGames = False 
            if app.dataFrameAssists is None:
                try:
                    app.dataFrameAssists, app.oddsForPlayerAssists = getDataFrame(f'{app.firstName} {app.lastName}', 'Assists', app.playerData) 
                    randomForest = RandomForest (app.nTrees, app.dataFrameAssists, 'Over')
                    randomForest.train()
                    app.playerAssistsOdds.append(randomForest.predict())
                    randomForest = RandomForest (app.nTrees, app.dataFrameAssists, 'Under')
                    randomForest.train()
                    app.playerAssistsOdds.append(randomForest.predict())
                except:
                    app.noGames =  True 
        #if pressing the exit button 
        if app.hoverOverExitButton:
            app.pressPlayerBox = False #returns to homePage
            app.dataFramePoints = None #reset everything 
            app.dataFrameRebounds = None 
            app.dataFrameAsists = None
            app.playerPointsOdds = []
            app.playerReboundsOdds = []
            app.playerAssistsOdds = []
            app.playerData = None
            app.displayButtonColor = 'Season Stats'
            app.hoverOverExitButtonHome = False 
            app.hoverOverExitButton = False
            app.scrollY = 0 #resetting scroll for the boxscores  
            app.hoverOverPlayer = False 


def onMouseMove(app, mouseX, mouseY): 
    if app.introductionPage:
        app.hoverOverStart = False 
        app.hoverOverGuide = False 
        if  75 <= mouseX <= 330 and 170 <= mouseY <= 221:
            app.hoverOverStart = True
        if  75 <= mouseX <= 330 and 250 <= mouseY <= 300:
            app.hoverOverGuide = True 
    elif app.guidePage:
        app.hoverOverExitButtonGuide = False 
        if 350 <= mouseX <= 380 and 15 <= mouseY <= 45:
                app.hoverOverExitButtonGuide = True #toggles to True
    elif not app.introductionPage and not app.pressPlayerBox: #in the homepage 
        app.hoverOverExitButtonHome = False
        app.hoverOverPlayer = False 
        if 350 <= mouseX <= 380 and 15 <= mouseY <= 45:
            app.hoverOverExitButtonHome = True #toggles to True  
        elif (app.xCoordinateBox<=mouseX<=app.inputBoxWidth+app.xCoordinateBox and app.yCoordinateBox + 50<=mouseY<=app.yCoordinateBox + 50 + app.inputBoxHeight*3) and app.search:
            app.hoverOverPlayer = True 
    elif app.pressPlayerBox: #in the playerPage 
        app.hoverOverExitButton = False 
        #some hard coding but kind of hard to avoid due to how the box is created (I am scaling everything down by a factor)
        if 17 <= mouseX <= 118 and 133<=mouseY <= 156:
            app.displayButton = 'Season Stats' 
        elif 112 <= mouseX <= 178 and 133<=mouseY <= 156:
            app.displayButton = 'Points'  
        elif 182 <= mouseX <= 258 and 133<=mouseY <= 156:
            app.displayButton = 'Rebounds' 
        elif 262 <= mouseX <= 330 and 133<=mouseY <= 156: 
            app.displayButton = 'Assists'  
        elif 350 <= mouseX <= 380 and 15 <= mouseY <= 45:
            app.hoverOverExitButton = True #toggles to True 
        else:
            app.displayButton = None 

def onStep(app):
    app.cursor = not app.cursor #toggles 
    
def main():
    runApp()

main()

