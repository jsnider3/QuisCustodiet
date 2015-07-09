#!/usr/bin/env python3
'''
  @author: Josh Snider
'''

from bs4 import BeautifulSoup
import filters
import json
import networkx as nx
import pdb
import re
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

  TABLE = "pagecache"

  def __init__(self, purge, DB="tropes.db"):
    self.sql = sqlite3.connect(DB)
    self.c = self.sql.cursor()
    self.purge = purge

  def __enter__(self):
    return self

  def __exit__(self, typ, value, trace):
    self.sql.close()

  def add_page(self, url, page):
    #TODO Purge won't work
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

  def count_references(self, url):
    self.c.execute('SELECT count(page_to) FROM edges where page_from=?', (url,))
    [(cnt,)] = self.c.fetchall()
    return cnt

  def count_referrers(self, url):
    self.c.execute('SELECT count(page_from) FROM edges where page_to=?', (url,))
    [(cnt,)] = self.c.fetchall()
    return cnt

  def delete_page(self, url):
    self.c.execute("DELETE FROM pagecache WHERE url=?", (url,))
    self.sql.commit()

  def duplicate(self, dest):
    '''Copy this database to a new location,
       used if constraints were changed.'''
    with Tropes(False, dest) as tropes:
      tropes.make_db()
      print("made db")
      stuff = self.list_contents()
      print("loaded stuff")
      for (url, contents) in stuff:
        try:
          tropes.add_page(url, contents)
        except:
          pass

  def edges_as_json(self, edges):
    edges = [(k,v) for (k,v) in edges if '?' not in k and '?' not in v]
    jsonified = [{'page_from': edge[0], 'page_to': edge[1]} for edge in edges]
    return json.dumps(jsonified)

  def get_multitropes(self, url):
    #DragonBallZ is an example.
    page = self.get_page(url)
    soup = BeautifulSoup(page)
    links = [link.get('href') for link in soup.find_all('a')]
    links = [link for link in links if link]
    pattern = re.compile('.*/Tropes[A-Z]To[A-Z].*')
    links = [str(link) for link in links if pattern.match(str(link))]
    pattern = re.compile('Tropes([A-Z])To([A-Z])')
    for link in links:
      mat = pattern.search(link)
      if mat.group(1) <= 'S' and 'S' <= mat.group(2):
        return self.get_page(link)
    return ""

  def get_page(self, url):
    '''Look up the url in the database.
       Fetch and cache it if it's not present.'''
    if self.top_url not in url:
      url = self.top_url + url
    url = add_schema(url)
    self.c.execute('SELECT contents FROM pagecache WHERE url = ?', (url,))
    results = self.c.fetchall()
    assert(len(results) < 2)
    page = ""
    if len(results) and not self.purge:
      page = results[0][0]
    else:
      try:
        page = requests.get(url).text
        self.add_page(url, page)
      except:
        print('FATAL ERROR: Could not get page %s.' % url, file=sys.stderr)
    return page

  def get_shoutouts(self, url):
    '''Get a list of pages that the given work has "shoutouts" to.'''
    if self.get_shoutout_page(url):
      #An example is Warhammer40000.
      page = self.get_shoutout_page(url)
      soup = BeautifulSoup(page)
      soup = soup.find("div", {"id": "wikitext"})
      if soup == None:
        print("INVALID PAGE:" + url, file=sys.stderr)
        print(page)
        shoutouturl = add_schema(self.base_url + "ShoutOut/"
          + url.split('/')[-1])
        print("delete " + shoutouturl)
        self.delete_page(shoutouturl)
        return self.get_shoutouts(url)
    else:
      page = self.get_multitropes(url)
      if not page:
        #An example is MontyPythonsFlyingCircus.
        page = self.get_page(url)
      soup = BeautifulSoup(page)
      items = [item for item in soup.findAll('li') if
        '/Main/ShoutOut' in str(item)]
      try:
        soup = min(items, key=lambda x: str(x).index('/Main/ShoutOut'))
      except ValueError:
        soup = BeautifulSoup("")
    links = [link.get('href') for link in soup.find_all('a')]
    links = [link for link in links if link and self.is_trope(link)
      and filters.is_work(link)]
    return links

  def get_shoutout_page(self, url):
    '''Returns if this has a specific shout out page.'''
    page = self.get_page(url)
    soup = BeautifulSoup(page)
    links = [link.get('href') for link in soup.find_all('a')]
    links = [link for link in links if link]
    shoutoutpage = "/ShoutOut/" + url.split('/')[-1]
    links = [link for link in links if shoutoutpage in link]
    if len(links):
      return self.get_page(self.base_url + shoutoutpage)
    else:
      return ""

  def is_trope(self, url):
    return self.base_url in url

  def list_contents(self):
    self.c.execute('SELECT * FROM pagecache')
    return self.c.fetchall()

  def list_edges(self):
    self.c.execute('SELECT * FROM edges')
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
    self.c.execute('''CREATE TABLE IF NOT EXISTS pagecache (url VARCHAR(20) PRIMARY KEY,
      contents VARCHAR(30))''')
    self.c.execute('''CREATE TABLE IF NOT EXISTS edges (page_from VARCHAR(20),
      page_to VARCHAR(30))''')
    self.sql.commit()

  def pagerank(self, edges):
    '''Take the edges as generated by list_edges,
       and calculate the pagerank of the nodes.'''
    return nx.pagerank(nx.from_edgelist(edges))

  def print_results(self, ranked):
    ind = 1
    print("[")
    for (k, v) in ranked:
      urlsplit = v.split('/')
      if "?" not in urlsplit[-1] and "?" not in urlsplit[-2]:
        if (k,v) != ranked[-1]:
          print("{ ind:", ind, ", pr:", k,
            ", cat: '" + urlsplit[-2] + "', name: '" + urlsplit[-1] + "'},")
        else:
          print("{ ind:", ind, ", pr:", k,
            ", cat: '" + urlsplit[-2] + "', name: '" + urlsplit[-1] + "'}")
        ind += 1
    print("]")

  def replicate(self):
    '''The steps to fully replicate my work.'''
    #Run scrapy runspider crawler.py
    #Filter out pages that aren't works or that redirect.
    self.make_db()
    self.cache_pages('filteredworks.txt')
    works = self.list_pages()
    for work in works:
      if filters.is_work(work):
        shoutouts = tropes.get_shoutouts(work)
        tropes.save_shoutouts(work, shoutouts)
    rankdict = tropes.pagerank(tropes.list_edges())
    ranked = [(rankdict[k], k) for k in rankdict]
    ranked.sort()
    ranked = [(k, v) for (k, v) in ranked if (self.count_referrers(k) * 2 > 
      self.count_references(k))]
    ranked = list(reversed(ranked))
    self.print_results(ranked)

  def list_references(self, url):
    self.c.execute('SELECT page_to FROM edges where page_from=?', (url,))
    return self.c.fetchall()

  def list_referrers(self, url):
    self.c.execute('SELECT page_from FROM edges where page_to=?', (url,))
    return self.c.fetchall()

  def save_shoutouts(self, work, shoutouts):
    for ref in shoutouts:
      print(work, "->", ref)
      self.c.execute("INSERT INTO edges VALUES (?, ?)", (work, ref))
      self.sql.commit()

if __name__ == '__main__':
  with Tropes(False) as tropes:
    print(tropes.edges_as_json(tropes.list_edges()))

