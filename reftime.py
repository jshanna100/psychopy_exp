from psychopy import visual
import time
import numpy as np

def col_anim(beg,end,steps):
    # make color animations, put in start and finish RGB values and how many frames
    col_list = []
    for col_idx in range(3):
        col_list.append(list(np.linspace(beg[col_idx],end[col_idx],steps)))
    return list(zip(*col_list))

class VisObj():
    # class contains a visual object and queues of operations to apply to it
    def __init__(self,visobj,width=[],height=[],pos=[],fillColor=[],lineColor=[],
      color=[],opacity=[]):
        self.visobj = visobj
        self.width = width
        self.height = height
        self.pos = pos
        self.fillColor = fillColor
        self.lineColor = lineColor
        self.color = color
        self.opacity = opacity
    def draw(self):
        if self.fillColor:
            self.visobj.fillColor = self.fillColor.pop(0)
        if self.lineColor:
            self.visobj.lineColor = self.lineColor.pop(0)
        if self.pos:
            self.visobj.pos = self.pos.pop(0)
        if self.color:
            self.visobj.color = self.color.pop(0)
        self.visobj.draw()

def refresh_timer(monitors,test_length):

    screens = []
    visobjs = []
    for mon in monitors:
        screens.append(visual.Window(size=mon["res"],screen=mon["idx"],winType="pyglet"))
        screens[-1].waitBlanking = False
        visobjs.append(VisObj(visual.Circle(screens[-1])))
        
    refresh_rates = []
    for scr_idx, scr in enumerate(screens):
        t_start = time.perf_counter()
        visobjs[scr_idx].fillColor = col_anim((.5,.5,.5),(1,0,0),int(test_length/3)) + \
        col_anim((1,0,0),(0,1,0),int(test_length/3)) + \
        col_anim((0,1,0),(0,0,1),int(test_length/3))
        for f_idx in range(test_length):
            visobjs[scr_idx].draw()
            scr.flip()
        t_end = time.perf_counter()
        refresh_rates.append(t_end-t_start)
        visobjs[scr_idx].fillColor = col_anim((.5,.5,.5),(1,0,0),int(test_length/3)) + \
        col_anim((1,0,0),(0,1,0),int(test_length/3)) + \
        col_anim((0,1,0),(0,0,1),int(test_length/3))
    t_start = time.perf_counter()
    for f_idx in range(test_length):
        for x_idx,x in enumerate(screens):
            visobjs[x_idx].draw()
            x.flip()
    t_end = time.perf_counter()
    refresh_rates.append(t_end-t_start)
    
    [x.close() for x in screens]
    return [int(round(test_length/x)) for x in refresh_rates]
