from ratingbar import *
from psychopy import visual
import numpy as np
from pyglet.window import key

decr_butts1 = [key._1]
incr_butts1 = [key._2]
conf_butts1 = [key._3]
decr_butts2 = [key._9]
incr_butts2 = [key._0]
conf_butts2 = [key._8]

win = visual.Window(size=(700,700),color=(0.5,0.5,0.5))
volume = RatingBar(win,(-0.5,0),(0.75,0.3),0.03,incr_butts1,decr_butts1,conf_butts1,
  midline_length=2,midline_pos=0,rval=0,orient="vertical")
rating = RatingBar(win,(0.5,0),(0.75,0.3),0.03,incr_butts2,decr_butts2,conf_butts2,
  midline_length=3,midline_pos=-1,rval=0,orient="horizontal")
rbv = RBarVerkehr([volume,rating],win)
print(rbv.go())
