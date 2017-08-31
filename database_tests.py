from game_database import *
import sqlite3

def new_games(conn):
    c = conn.cursor()
    create_database(conn, 2, "test_new")
    maintain_database(conn, 3, "test_new")
    c.execute("SELECT * FROM test_new")
    if len(c.fetchall()) == 75:
        return True
    else:
        return False
    conn.commit()

def old_games(conn):
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS test_old(id TEXT, title TEXT, tags TEXT)")
    for shit in range(0, 10):
        c.execute("INSERT INTO test_old VALUES(?, ?, ?)", ("12" + str(shit), "game" + str(shit), "fun,and,interactive" + str(shit)))
    conn.commit()
    maintain_database(conn, 1, "test_old")
    conn.commit()
    try:
        for shit in range(0, 10):
            c.execute("SELECT * FROM test_old WHERE id=?", "12" + shit)
        return False
    except:
        return True

def duplicate_insert(c):
    for shit in range(0, 10):
        c.execute("INSERT INTO test_duplicate VALUES(?, ?, ?)", ("12" + str(shit), "game" + str(shit), "fun,and,interactive" + str(shit)))

def duplicates(conn):
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS test_duplicate(id TEXT, title TEXT, tags TEXT)")
    duplicate_insert(c)
    duplicate_insert(c)
    duplicate_insert(c)
    conn.commit()
    maintain_database(conn, 1, "test_duplicate")
    try:
        for shit in range(0, 10):
            c.execute("SELECT * FROM test_old WHERE id=?", "12" + shit)
        return False
    except:
        return True

def tests():
    conn = sqlite3.connect("tags_database.db")
    c = conn.cursor()
    print(duplicates(conn))
    
    
    
    conn.commit()
    c.close()

tests()