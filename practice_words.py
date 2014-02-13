import sys
import sqlite3
import numpy as np
import itertools as it
import math
import pygame

if len(sys.argv) > 1:
  maxlevel = int(sys.argv[1])
else:
  maxlevel = 0

db_fname = 'words.db'
con = sqlite3.connect(db_fname)
cur = con.cursor()
(n_words,) = cur.execute('select count(*) from words').fetchone()

drop_list = ['a','the','to','be','(honorific)','an']
def strip_down(s):
  return ' '.join(filter(lambda w: not w in drop_list,s.split()))

def cosine_distance(p1,p2):
  if len(p1) == 0 or len(p2) == 0:
    return 1.0

  d1 = {}
  for w in p1.split():
    d1[w] = d1.get(w,0) + 1
  d2 = {}
  for w in p2.split():
    d2[w] = d2.get(w,0) + 1

  both = sum([d1.get(w,0)*d2.get(w,0) for w in d1.keys()])
  sum1 = sum(d1.values())
  sum2 = sum(d2.values())
  return 1.0-float(both)/math.sqrt(float(sum1*sum2))

def guess_distance(guess,answer):
  guess_base = strip_down(guess.lower())
  answer_list = map(strip_down,answer.lower().split(','))
  answer_list = list(it.chain(*map(lambda s: s.split(' or '),answer_list)))
  scores = [cosine_distance(guess_base,p) for p in answer_list]
  return min(scores)

# init pygame
screen_size = (500,200)
font_name_ko = 'undotum'
font_bg = (0,0,0)
font_fg = (230,230,230)
font_size = 80
font_aa = 0

pygame.init()
screen = pygame.display.set_mode(screen_size)
font_ko = pygame.font.Font(pygame.font.match_font(font_name_ko),font_size)
font_en = pygame.font.get_default_font()

def draw_text(text,font,pos):
  ren = font.render(text,font_aa,font_fg,font_bg)
  screen.blit(ren,pos)
  pygame.display.flip()

while True:
  cmd = 'select * from words where rowid=? and level<=?'
  ret = None
  while ret is None:
    ret = cur.execute(cmd,(np.random.randint(n_words),maxlevel)).fetchone()
  (id,level,pos,korean,english,score,seen,last) = ret
  try:
    english = english.decode('ascii','ignore')
  except:
    pass

  print korean + ' (' + str(level) + ')'

  screen.fill(font_bg)
  draw_text(korean,font_ko,(10,10))

  guess = unicode(raw_input('English: '))
  if guess_distance(guess,english) <= 0.2:
    print 'Correct: ' + english
  else:
    print 'Answer: ' + english
  print '='*80
  print 
  print 
