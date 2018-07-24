from ratingbar import *
from psychopy import visual

win = visual.Window(size=(700,700),color=(0.5,0.5,0.5))
RatingBar(win,[],[],[],midline_length=3,midline_pos=0,orient="horizontal")
