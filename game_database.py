"""
Author: Zach Morgan
Description: Creates a database of games and their tags
"""

import steamapi
import requests
from bs4 import BeautifulSoup
import time
import math
import sqlite3


def find_total_pages(filter):
    
    """
    Parameters: String filter - indicating which filter to be used for the search page, Example: Games only = 'category1=998'
    Purpose: Retrieve the total amount of pages of games from the search page
    Returns: Integer page count
    """
    
    first_page = requests.get("http://store.steampowered.com/search/?" + filter)
    html = BeautifulSoup(first_page.content, "html.parser")
    div = html.find("div", class_ = "search_pagination_left")
    split = div.contents[0].split()
    total_pages = math.ceil(int(split[5]) / 25)
    return total_pages


def get_tags(page):
    
    """
    Parameters: Request object page
    Purpose: Aquire a tuple of the title and a list of the tags
    Returns: Tuple (String, List)
    """

    html = BeautifulSoup(page.content, "html.parser")
    title_raw = html.find("title").contents
    trim = title_raw[0].split()
    on_steam = False
    save = False
    title = ""
    if " ".join(trim[-2:]) == "on Steam":
        on_steam = True
    if "%" in trim[1]:
        save = True
    if on_steam and not save:
        title = " ".join(trim[0:-2])
    if save and not on_steam:
        title = " ".join(trim[2:])
    if save and on_steam:
        title = " ".join(trim[3:-2])
    if not save and not on_steam:
        title = title_raw        
    tags_raw = html.find_all("a", class_="app_tag")
    tags_list = []
    for tags in tags_raw:
        tag = tags.contents[0].strip()
        #If i want tags to be "-" seperated
        """
        try:
            tag_split = tag.split()
            tag = "-".join(tag_split[:])
        except:
            pass  
        """
        tags_list.append(tag)
    formatted_tags = ",".join(tags_list[:])
    return title, formatted_tags               
    

def create_database_list(c, tablename):
    
    """
    Parameters: Sqlite3 object c - connection to database, String tablename - name of table to create list from
    Purpose: Creates a list of all the ID's in the table
    Returns: List
    """

    c.execute("SELECT * FROM " + tablename)
    all_games = c.fetchall()
    game_lst =[]
    for game in all_games:
        game_lst.append(game[0])
    return game_lst


def find_duplicates(game_lst):
    """
    Purpose: Create a list of duplicates in the database
    Doesn't really work 100%, website still functions without it, if working would save a little bit of space in the db file but thats about it
    """
    seen = set()
    duplicates = set()
    for game in game_lst:
        if game not in seen:
            seen.add(game)
        else:
            duplicates.add(game)
    return duplicates


def maintain_database(conn, total_pages, tablename, filter):
    
    """
    Parameters: conn - database connection 
    Integer total_pages - total page number aquired from the find_total_pages function
    String tablename - name of the table to perform maintainance on
    String filter - indicating which filter to be used for the search page, Example: Games only = 'category1=998'

    Purpose: Performs maintaince on an existing table, or creates one
    
    Returns: NONE
    """

    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS " + tablename + "(id TEXT, title TEXT, tags TEXT)")
    page_count = 0
    games_on_steam = {}
    maintain = True
    #Checks whether a table exists already, if it does it leaves the maintain value True
    try:
        c.execute("SELECT * FROM " + tablename)
    except:
        maintain = False
    #Pages in the steam store start at 1, not 0
    for page_number in range(1, total_pages + 1):
        page_count += 1
        try:
            if page_number == 1:
                page = requests.get("http://store.steampowered.com/search/" + filter)
            else:
                page = requests.get("http://store.steampowered.com/search/?" + filter  + "&page=" + str(page_number))
            html = BeautifulSoup(page.content, "html.parser")
            raw_links_lst = html.find_all("div", class_ = "col search_capsule")
            links_lst =[]
            #creates a list of the Store URLs on the current search page
            for index in range(0, len(raw_links_lst)):
                links_lst.append(raw_links_lst[index].parent["href"]) 
            #Cookies that by pass the age gate for age restricted games
            agecheck = {'birthtime': '568022401'}
            for link in links_lst:
                id_lst = link.split("/")
                id = id_lst[4]
                #check if game is new and not in database yet
                c.execute("SELECT title FROM " + tablename + " WHERE id=" + str(id))
                data = c.fetchone()
                if data is None:
                    page = requests.get(link, cookies = agecheck)
                    title, tags = get_tags(page)
                    c.execute("INSERT INTO " + tablename + " VALUES(?, ?, ?)", (id, title, tags))
                games_on_steam[id] = None    
            conn.commit()        
        except:
            print(page_count)
    #Supposed to delete old games no longer on steam, randomly deletes games that are on steam can't figure out why, the website still 
    #functions 100% with old games staying in the database, maybe I'll get around to fixing it
            """
    if maintain:
        game_lst = create_database_list(c, tablename)      
        #delete old games no longer on steam
        for game in game_lst:
            if game not in games_on_steam:
                c.execute("DELETE FROM " + tablename + " WHERE id=?", [game])
        """

def main():
    conn = sqlite3.connect("tags_database.db")
    c = conn.cursor()
    total_pages = find_total_pages("category1=998")
    maintain_database(conn, total_pages, "games_filter", "category1=998")
    conn.commit()
    c.close()


if __name__ == "__main__":
    main()

