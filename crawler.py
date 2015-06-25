from bs4 import BeautifulSoup
from sets import Set

import requests
import sys

tvtropes = "http://tvtropes.org"

ls = Set([])

def addLinks(links):
  new = Set([])
  for link in links:
    if link not in ls:
      ls.add(link)
      print(link)
      new.add(link)
  return new

def crawl(url):
  if url not in ls:
    links = getLinks(url)
    cont = addLinks(links)
    print(len(ls))
    for link in cont:
      crawl(cont)

def getLinks(url):
  r  = requests.get(tvtropes)
  data = r.text
  soup = BeautifulSoup(data)
  links = [link.get('href') for link in soup.find_all('a')]
  links = [link for link in links if 'mailto' not in link]
  links = [link for link in links if 'javascript' not in link]
  links = [link for link in links if '?action' not in link]
  links = [link for link in links if 'php' not in link or 'pmwiki.php' in link]
  links = [tvtropes + link if 'http' not in link else link for link in links]
  links = [link for link in links if tvtropes in link]
  return links

sys.setrecursionlimit(2000000)
crawl(tvtropes)
