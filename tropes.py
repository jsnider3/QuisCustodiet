#!/usr/bin/env python3
'''
  @author: Josh Snider
'''

import requests
import sqlite3

class Tropes(object):

  DB = "tropes.db"
  TABLE = "pagecache"

  def __init__(self):
    self.sql = sqlite3.connect(self.DB)
    self.c = self.sql.cursor()

  def __enter__(self):
    return self

  def __exit__(self, typ, value, trace):
    self.sql.close()

  def add_page(self, url, page):
    self.c.execute("INSERT INTO pagecache VALUES (?, ?)", (url, page))
    self.sql.commit()

  def cache_pages(self, url_file):
    with open(url_file) as src:
      urls = src.readlines()
      cached = set(self.list_pages())
      urls = [url.strip() for url in urls]
      urls = [url for url in urls if url not in cached]
      for url in urls:
        try:
          page = requests.get(url).text
          self.add_page(url, page)
        except:
          pass

  def get_page(self, url):
    '''Look up the url in the database.
       Fetch and cache it if it's not present.'''
    self.c.execute('SELECT contents FROM pagecache WHERE url = ?', (url,))
    results = self.c.fetchall()
    assert(len(results) < 2)
    page = ""
    if len(results):
      page = results[0]
    else:
      try:
        page = requests.get(url).text
        self.add_page(url, page)
      except:
        print('FATAL ERROR: Could not get page %s.' % url, file=sys.stderr)
    return page

  def list_contents(self):
    self.c.execute('SELECT * FROM pagecache')
    print(self.c.fetchall())

  def list_pages(self):
    self.c.execute('SELECT url FROM pagecache')
    return [url for (url,) in self.c.fetchall()]

  def list_tables(self):
    self.c.execute("SELECT * FROM sqlite_master WHERE type='table';")
    print(self.c.fetchall())

  def make_db(self):
    self.c.execute('''CREATE TABLE pagecache (url VARCHAR(20),
      contents VARCHAR(30))''')
    self.sql.commit()

if __name__ == '__main__':
  #make_db()
  #cache_pages('filteredworks.txt')
  with Tropes() as tropes:
    tropes.get_page(
      'http://tvtropes.org/pmwiki/pmwiki.php/Film/ThePhantomMenace')
  #print("DONE"t)
