#!/usr/bin/env python3
'''
  @author: Josh Snider
'''

import filters
import pdb
import tropes
import unittest

class TestTropes(unittest.TestCase):

  def test_sep_shoutouts(self):
    with tropes.Tropes(False) as datab:
      shoutouts = datab.get_shoutouts(
        'http://tvtropes.org/pmwiki/pmwiki.php/TabletopGame/Warhammer40000')
      assert(len(shoutouts) == 50)
      assert('http://tvtropes.org/pmwiki/pmwiki.php/Film/ApocalypseNow'
        in shoutouts)
      assert('http://tvtropes.org/pmwiki/pmwiki.php/Literature/TheLordOfTheRings'
        in shoutouts)

  def test_multitrope_shoutouts(self):
    with tropes.Tropes(False) as datab:
      pdb.set_trace()
      shoutouts = datab.get_shoutouts(
        'http://tvtropes.org/pmwiki/pmwiki.php/Anime/DragonBallZ')
      assert(len(shoutouts) == 0)

  def test_single_shoutouts(self):
    with tropes.Tropes(False) as datab:
      shoutouts = datab.get_shoutouts(
        'http://tvtropes.org/pmwiki/pmwiki.php/Series/MontyPythonsFlyingCircus')
      assert(len(shoutouts) == 3)
      assert('http://tvtropes.org/pmwiki/pmwiki.php/Series/ThePrisoner'
        in shoutouts)
      assert('http://tvtropes.org/pmwiki/pmwiki.php/Series/TheSaint'
        in shoutouts)

if __name__ == '__main__':
  unittest.main()
