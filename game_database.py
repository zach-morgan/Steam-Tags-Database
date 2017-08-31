import steamapi
import requests
from bs4 import BeautifulSoup
import time
import math
import sqlite3


def find_total_pages():
    first_page = requests.get("http://store.steampowered.com/search")
    html = BeautifulSoup(first_page.content, "html.parser")
    div = html.find("div", class_ = "search_pagination_left")
    split = div.contents[0].split()
    total_pages = math.ceil(int(split[5]) / 25)
    return total_pages

def get_tags(page):
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
    c.execute("SELECT * FROM " + tablename)
    all_games = c.fetchall()
    game_lst =[]
    for game in all_games:
        game_lst.append(game[0])
    return game_lst

def find_duplicates(game_lst):
    seen = set()
    duplicates = set()
    for game in game_lst:
        if game not in seen:
            seen.add(game)
        else:
            duplicates.add(game)
    return duplicates

def create_database(c, total_pages, tablename):
    c.execute("CREATE TABLE IF NOT EXISTS " + tablename + "(id TEXT, title TEXT, tags TEXT)")
    page_count = 0
    for page_number in range(1, total_pages+1):
        page_count += 1
        try:
            if page_number == 1:
                page = requests.get("http://store.steampowered.com/search")
            else:
                page = requests.get("http://store.steampowered.com/search?page=" + str(page_number))
            html = BeautifulSoup(page.content, "html.parser")
            raw_links_lst = html.find_all("div", class_ = "col search_capsule")
            links_lst =[]
            for index in range(0, len(raw_links_lst)):
                links_lst.append(raw_links_lst[index].parent["href"])
            agecheck = {'birthtime': '568022401'}
            for link in links_lst:
                id_lst = link.split("/")
                id = id_lst[4]
                page = requests.get(link, cookies = agecheck)
                title, tags = get_tags(page)
                c.execute("INSERT INTO " + tablename + " VALUES(?, ?, ?)", (id, title, tags))
        except:
            print(page_count)      

def maintain_database(conn, total_pages, tablename):
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS " + tablename + "(id TEXT, title TEXT, tags TEXT)")
    page_count = 0
    games_on_steam = {}
    maintain = True
    try:
        c.execute("SELECT * FROM " + tablename)
    except:
        maintain = False
    if page_count == 0:
        for page_number in range(1, total_pages + 1):
            page_count += 1
        #try:
            if page_number == 1:
                page = requests.get("http://store.steampowered.com/search")
            else:
                page = requests.get("http://store.steampowered.com/search?page=" + str(page_number))
            html = BeautifulSoup(page.content, "html.parser")
            raw_links_lst = html.find_all("div", class_ = "col search_capsule")
            links_lst =[]
            for index in range(0, len(raw_links_lst)):
                links_lst.append(raw_links_lst[index].parent["href"]) 
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
        #except:
            #print(page_count)
    conn.commit()
    if maintain:
        game_lst = create_database_list(c, tablename)      
        #delete old games no longer on steam
        for game in game_lst:
            if game not in games_on_steam:
                c.execute("DELETE FROM " + tablename + " WHERE id=?", [game])
        #take care of duplicates
        duplicates = find_duplicates(game_lst)
        if len(duplicates) != 0:
            for duplicate in duplicates:
                c.execute("SELECT title FROM " + tablename + " WHERE id=" + duplicate)
                game_info = c.fetchall()
                c.execute("DELETE FROM " + tablename + " WHERE id=?", (duplicate,))
                c.execute("INSERT INTO " + tablename + " VALUES(?, ?, ?)", (game_info[0], game_info[1], game_info[2]))

def main():
    conn = sqlite3.connect("tags_database.db")
    c = conn.cursor()
    total_pages = find_total_pages()
    #create_database(c, 2, "test")
    maintain_database(conn, 3, "test1")
    conn.commit()
    c.close()
if __name__ == "__main__":
    main()

