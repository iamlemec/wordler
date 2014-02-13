import numpy as np
import sqlite3

txt_fname = '6000_korean_words.txt'
db_fname = 'words.db'

con = sqlite3.connect(db_fname)
con.text_factory = str
cur = con.cursor()
try:
  cur.execute("create table words (id int, level text, pos text, korean text, english text, seen int, score int, last date)")
except:
  pass

dat = np.array([[s.strip() for s in line.split('\t')] for line in open(txt_fname)][1:],dtype=np.str)
cur.executemany("insert into words values (?,?,?,?,?,0,0,\'\')",dat)
cur.execute("update words set level=0 where level=\'A\'")
cur.execute("update words set level=1 where level=\'B\'")
cur.execute("update words set level=2 where level=\'C\'")
cur.execute("update words set level=3 where level=\'D\'")

con.commit()
cur.close()
con.close()
