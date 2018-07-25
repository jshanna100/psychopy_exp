from ratingbar import *
from psychopy import visual
import numpy as np

win = visual.Window(size=(700,700),color=(0.5,0.5,0.5))
rb1 = RatingBar(win,(0.2,-0.3),(1.5,0.3),0.05,["3"],["4"],["0"],
  midline_length=3,midline_pos=0,rval=0,orient="vertical")
for f in np.nditer(np.linspace(-1,1,num=500)):
    rb1.set_val(f)
    win.flip()
