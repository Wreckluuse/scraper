import pprint
import requests
import json
import re
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error

#Constant array of character names. This array is used throughout the scraper in things such as the url builder and the data
#that is sent to the database.
CHARACTERS = ["Blanka", "Cammy", "Chun-Li", "Dee_Jay", "Dhalsim", "E.Honda", "Guile", "Jamie", "JP", "Juri", "Ken", "Kimberly", "Lily", "Luke", "Manon", "Marisa", "Ryu", "Zangief"]

#This function initially returned an array of strings used to create tables, now just returns the one table in the database.
def generateTables():
    
    character_table = """CREATE TABLE IF NOT EXISTS Characters (
                    characterId int AUTO_INCREMENT NOT NULL PRIMARY KEY,
                    characterName varchar(255) NOT NULL,
                    characterMoves json NOT NULL
                    )"""

   ###########################################################################
   # Leaving this here for educational purposes. Attempted a properly        #
   # normalized database but ran into too many issues for how much time      #
   # I had. Ended up just using the table above and inserting my data as json#
   ########################################################################### 

    # characterName_table = """CREATE TABLE IF NOT EXISTS CharacterName (           
                        # CharacterID int AUTO_INCREMENT NOT NULL,
                        # CharacterName varchar(255) NOT NULL,
                        # PRIMARY KEY (CharacterID))"""
    # 
    # characterMoves_table = """CREATE TABLE IF NOT EXISTS CharacterMoves (
                # CharacterID int NOT NULL,
                # MoveID int NOT NULL,
                # Startup varchar(50),
                # Active varchar(50),
                # Recovery varchar(50),
                # Cancel varchar(50),
                # Damage varchar(50),
                # Guard varchar(50),
                # OnHit varchar(50),
                # OnBlock varchar(50),
                # PRIMARY KEY (CharacterID, MoveID),
                # FOREIGN KEY (CharacterID) REFERENCES CharacterName(CharacterID),
                # FOREIGN KEY (MoveID) REFERENCES Moves(MoveID))"""
    # 
    # moves_table = """CREATE TABLE IF NOT EXISTS Moves(
                # MoveID int AUTO_INCREMENT NOT NULL PRIMARY KEY,
                # MoveCategoryID int NOT NULL,
                # FOREIGN KEY (MoveCategoryID) REFERENCES MoveCategory(MoveCategoryID))"""
    # 
    # moveCategory_table = """CREATE TABLE IF NOT EXISTS MoveCategory (
                        # MoveCategoryID int AUTO_INCREMENT NOT NULL PRIMARY KEY,
                        # MoveCategoryName varchar(255) NOT NULL
                        # )"""
# 
    # moveType_table = """CREATE TABLE IF NOT EXISTS MoveType (
                    #  MoveTypeID int AUTO_INCREMENT NOT NULL PRIMARY KEY,
                    #  MoveName varchar(255) NOT NULL,
                    #  Input varchar(55) NOT NULL)
                    #  """
    # return [moveType_table, moveCategory_table, characterName_table, moves_table, characterMoves_table]
    return character_table


#This function is a part of the scraping process. It is responsible for pulling out data related to moves and building
#a move object to be nested into the character table.
def extractFrames(move_type):    
    section_moves = []
    for move in move_type:
        move_name = move.find('div', 'movedata-flex-image-container').div.div.text
        move_input = move.find('div', 'movedata-flex-framedata-name-item-middle').div.text
        table = move.table.tbody.find_all('tr')
        move_labels = table[0].text.split('\n')
        move_framevalues = table[1].text.split('\n')
        url = move.find('img', 'movedatacargoimage-img')['src']
        move_data = {
            "name": move_name,
            "input": move_input,
            "img_url": url,
            "frame_data" : []
        }
        for i in range(0, len(move_labels)):
            if move_labels[i] != "" and move_framevalues[i] != "":
                move_data['frame_data'].append({move_labels[i]:move_framevalues[i]})
        section_moves.append(move_data)
    return section_moves

#This function starts the scraping process by pulling out the main 'sections'
#or type of move, and then loops through these sections and performs the extractFrames() function.
def scrapeData(page):
    soup = BeautifulSoup(page.content, "html.parser")
    sections = soup.find_all('section', {"id":re.compile("section-collapsible-*")})
    section_headers = soup.find_all('h2', 'section-heading')
    data = []
    sections.pop(0)
    for i in range(0, len(sections)):
         section_name = section_headers[i].span.next_sibling.text
         current_section = sections[i].find_all('div', 'movedata-container')
         if (section_name != "SF6 Navigation"):
            data.append({"section":section_name,"data":extractFrames(current_section)})
    return data 
#Connection script found at https://pynative.com/python-mysql-database-connection/
def initDB():

    try:
        connection = mysql.connector.connect(host='localhost',
                                             database='street fighter 6 framedata test',
                                             user='root',
                                             password='')
        if connection.is_connected():
            db_Info = connection.get_server_info()
            print("Connected to MySQL Server version ", db_Info)
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print("You're connected to database: ", record)
            
            table_queries = generateTables()

            cursor.execute('CREATE TABLE IF NOT EXISTS Characters(characterId int AUTO_INCREMENT NOT NULL PRIMARY KEY, characterName varchar(255) NOT NULL, moves json NOT NULL)')
            for character in CHARACTERS:
                URL = "https://wiki.supercombo.gg/w/Street_Fighter_6/" + character 
                PAGE = requests.get(URL)
                data = scrapeData(PAGE)
                move_json = json.dumps(data)
                cursor.execute("INSERT INTO Characters (characterName, moves) VALUES (%s, %s)", (character, move_json))
                connection.commit()

    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    initDB()