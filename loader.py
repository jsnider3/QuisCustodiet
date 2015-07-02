#!/usr/bin/env python3
'''
  @author: Josh Snider
'''

import requests
import sqlite3

DB = "tropes.db"
TABLE = "pagecache"

def cache_pages(url_file):
  tropes = sqlite3.connect(DB)
  cursor = tropes.cursor()
  with open(url_file) as fl:
    urls = fl.readlines()
    cached = set(list_pages())
    urls = [url.strip() for url in urls]
    urls = [url for url in urls if url not in cached]
    for url in urls:
      try:
        page  = requests.get(url).text
        cursor.execute("INSERT INTO pagecache VALUES (?, ?)", (url, page))
        tropes.commit()
      except:
        pass
    tropes.close()

def list_contents():
  tropes = sqlite3.connect(DB)
  cursor = tropes.cursor()
  cursor.execute('SELECT * FROM pagecache')
  print(cursor.fetchall())

def list_pages():
  tropes = sqlite3.connect(DB)
  cursor = tropes.cursor()
  cursor.execute('SELECT url FROM pagecache')
  return [url for (url,) in cursor.fetchall()]

def list_tables():
  tropes = sqlite3.connect(DB)
  cursor = tropes.cursor()
  cursor.execute("SELECT * FROM sqlite_master WHERE type='table';")
  print(cursor.fetchall())

def make_db():
  tropesdb = sqlite3.connect(DB)
  cursor = tropesdb.cursor()
  cursor.execute('''CREATE TABLE pagecache (url VARCHAR(20),
    contents VARCHAR(30))''')
  tropesdb.commit()
  tropesdb.close()

if __name__ == '__main__':
  #make_db()
  cache_pages('filteredworks.txt')
  #print("DONE")
