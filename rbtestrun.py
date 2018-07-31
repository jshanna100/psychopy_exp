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

extra_vis = []

win = visual.Window(size=(700,700),color=(0.5,0.5,0.5))
volume = RatingBar(win,(-0.5,0),0.3,0.75,0.02,decr_butts1,incr_butts1,conf_butts1,
                   richtung=1,midline_length=1.5,midline_pos=-1,overcolor=(0,0,1))
extra_vis.append(visual.TextStim(win=win,text="Lautstärke",pos=(-0.5,-0.5),height=0.07,color=(0,0,0)))
rating = RatingBar(win,(0.5,0),0.75,0.3,0.02,decr_butts2,incr_butts2,conf_butts2,
                   richtung=0,midline_length=1.5,midline_pos=0,overcolor=(0,1,0))
extra_vis.append(visual.TextStim(win=win,text="Angenehm",pos=(0.5,-0.3),height=0.07,
                                 color=(0,0,0)))

rbv = RBarVerkehr([volume,rating],win,extra_vis=extra_vis)
print(rbv.go())
win.close()
