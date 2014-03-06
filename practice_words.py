import sys
import sqlite3
import numpy as np
import itertools as it
import math
import pygame

# parse arguments
if len(sys.argv) > 1:
  maxlevel = int(sys.argv[1])
else:
  maxlevel = 0

# word database
db_fname = 'words.db'
con = sqlite3.connect(db_fname)
cur = con.cursor()
(n_words,) = cur.execute('select count(*) from words').fetchone()

def new_word():
  cmd = 'select * from words where rowid=? and level<=?'
  ret = None
  while ret is None:
    ret = cur.execute(cmd,(np.random.randint(n_words),maxlevel)).fetchone()
  (id,level,pos,korean,english,score,seen,last) = ret
  try:
    english = english.decode('ascii','ignore')
  except:
    pass
  return (korean,english,level)

# guess evaluator
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

# other tools
advancers = [pygame.K_RETURN,pygame.K_RIGHT]

def is_alphanum(k):
  return ((k>=pygame.K_a) and (k<=pygame.K_z)) or ((k>=pygame.K_0) and (k<=pygame.K_9)) or (k==pygame.K_SPACE)

# game state class
class PracticeCards:
  def __init__(self):
    # screen config
    self.screen_size = (500,200)
    self.korean_pos = (10,10)
    self.english_pos = (20,160)
    self.prompt_pos = (20,130)
    self.prompt_text = 'English: '

    # font config
    self.font_name_ko = 'undotum'
    self.font_bg = (0,0,0)
    self.font_fg = (230,230,230)
    self.font_size_large = 80
    self.font_size_small = 20
    self.font_aa = True

    # intialize
    self.init_pygame()
    self.init_fonts()
    self.init_state()
    self.prompt_clear()

  def init_pygame(self):
    pygame.init()
    self.screen = pygame.display.set_mode(self.screen_size)

  def init_fonts(self):
    self.font_ko = pygame.font.Font(pygame.font.match_font(self.font_name_ko),self.font_size_large)
    self.font_en = pygame.font.Font(pygame.font.get_default_font(),self.font_size_small)

    # state tracking
  def init_state(self):
    self.card = 0
    self.state = 0 # 0 -> korean, 1 -> prompt, 2 -> answered
    self.hist = [new_word()]
    self.sizes = []
    self.input = ''

  def is_lastcard(self):
    return self.card == len(self.hist)-1

  def current_card(self):
    return self.hist[self.card]

  # display tools
  def draw_text(self,text,font,pos):
    ren = font.render(text,self.font_aa,self.font_fg,self.font_bg)
    self.screen.blit(ren,pos)
    pygame.display.flip()

  # prompt tools
  def prompt_clear(self):
    self.input = ''
    (self.cursor_x,self.cursor_y) = self.prompt_pos
    self.cursor_x += self.font_en.size(self.prompt_text)[0]
    self.sizes = []

  def prompt_addchar(self,k):
    if is_alphanum(k):
      char = chr(k)
      self.draw_text(char,self.font_en,(self.cursor_x,self.cursor_y))
      char_size = self.font_en.size(char)
      self.cursor_x += char_size[0]
      self.sizes.append(char_size)
      self.input += char
    elif (k == pygame.K_BACKSPACE) and (len(self.sizes) > 0):
      char_size = self.sizes.pop()
      back_rect = pygame.Rect(self.cursor_x-char_size[0],self.cursor_y,self.cursor_x,self.cursor_y+char_size[1])
      self.screen.fill(self.font_bg,rect=back_rect)
      pygame.display.flip()
      self.cursor_x -= char_size[0]
      self.input = self.input[:-1]

  def prompt_answer(self):
    (korean,english,level) = self.current_card()

    if guess_distance(self.input,english) <= 0.2:
      result = 'Correct: ' + english
    else:
      result = 'Answer: ' + english
    self.draw_text(result,self.font_en,self.english_pos)
    self.prompt_clear()

  # display control
  def display_state(self):
    (korean,english,level) = self.current_card()

    # draw text
    self.screen.fill(self.font_bg)
    self.draw_text(korean +' ('+str(level)+')',self.font_ko,self.korean_pos)
    if self.is_lastcard():
      self.draw_text(self.prompt_text+self.input,self.font_en,self.prompt_pos)
    elif self.state == 1:
      self.draw_text(self.prompt_text+english,self.font_en,self.prompt_pos)
    pygame.display.flip()

  # run program
  def run(self):
    self.display_state()
    while True:
      event = pygame.event.wait()
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          sys.exit()
        elif not event.key in advancers:
          if self.is_lastcard() and self.state == 0:
            self.prompt_addchar(event.key)
      if event.type == pygame.KEYUP:
        if event.key in advancers:
          if self.is_lastcard():
            if self.state == 0:
              self.prompt_answer()
              self.state = 1
            elif self.state == 1:
              self.state = 0
              self.card += 1
              self.hist.append(new_word())
              self.display_state()
          else:
            if self.state == 0:
              self.state = 1
            elif self.state == 1:
              self.state = 0
              self.card += 1
            self.display_state()
        elif event.key == pygame.K_LEFT:
          if self.state == 0 and self.card > 0:
            self.card -= 1
            self.state = 1
          elif self.state == 1:
            self.state = 0
          self.display_state()

# run it
pc = PracticeCards()
pc.run()
