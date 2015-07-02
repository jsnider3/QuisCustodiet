#!/usr/bin/env python3
'''
  @author: Josh Snider
'''

from bs4 import BeautifulSoup
import filters
import requests
import sqlite3
import sys

def add_schema(url):
  if not url.startswith('http'):
    url = "http://" + url
  return url

class Tropes(object):

  top_url = "tvtropes.org"
  base_url = top_url + "/pmwiki/pmwiki.php/"

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
    '''Read a list of urls from a file and cache them.'''
    with open(url_file) as src:
      urls = src.readlines()
      cached = set(self.list_pages())
      urls = [url.strip() for url in urls]
      urls = [url for url in urls if url not in cached]
      for url in urls:
        try:
          page = requests.get(add_schema(url)).text
          self.add_page(url, page)
        except:
          print('FATAL ERROR: Could not get page %s.' % url, file=sys.stderr)

  def get_page(self, url):
    '''Look up the url in the database.
       Fetch and cache it if it's not present.'''
    self.c.execute('SELECT contents FROM pagecache WHERE url = ?', (url,))
    results = self.c.fetchall()
    assert(len(results) < 2)
    page = ""
    if len(results):
      page = results[0][0]
    else:
      try:
        page = requests.get(add_schema(url)).text
        self.add_page(url, page)
      except:
        print('FATAL ERROR: Could not get page %s.' % url, file=sys.stderr)
    return page

  def get_shoutouts(self, url):
    if self.get_shoutout_page(url):
      page = self.get_shoutout_page(url)
      soup = BeautifulSoup(page)
      soup = soup.find("div", {"id": "wikitext"})
    elif self.has_multitropes(url):
      pass
    else:
      pass
    links = [link.get('href') for link in soup.find_all('a')]
    links = [link for link in links if link and self.is_trope(link)]
    print(links)
    #TODO Beautiful soup.

  def get_shoutout_page(self, url):
    '''Returns if this has a specific shout out page.'''
    page = self.get_page(url)
    soup = BeautifulSoup(page)
    links = [link.get('href') for link in soup.find_all('a')]
    links = [link for link in links if link]
    shoutoutpage = "/ShoutOut/" + url.split('/')[-1]
    links = [link for link in links if shoutoutpage in link]
    if len(links):
      return self.get_page(add_schema(self.top_url + links[0]))
    else:
      return ""

  def is_trope(self, url):
    return  self.base_url in url

  def list_contents(self):
    self.c.execute('SELECT * FROM pagecache')
    return self.c.fetchall()

  def list_pages(self):
    '''List the pages in the database.'''
    self.c.execute('SELECT url FROM pagecache')
    return [url for (url,) in self.c.fetchall()]

  def list_tables(self):
    '''List the tables in the database.'''
    self.c.execute("SELECT * FROM sqlite_master WHERE type='table';")
    return self.c.fetchall()

  def make_db(self):
    self.c.execute('''CREATE TABLE IF NOT EXISTS pagecache (url VARCHAR(20),
      contents VARCHAR(30))''')
    self.sql.commit()

if __name__ == '__main__':
  with Tropes() as tropes:
    tropes.get_shoutouts(
      'http://tvtropes.org/pmwiki/pmwiki.php/TabletopGame/Warhammer40000')
    print("DONE")
