from psychopy import visual
import time
import numpy as np
from scipy.stats import mode

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

def refresh_timer(monitors,test_length,cycles=5):

    screens = []
    mon_names = list(monitors.keys())
    visobjs = [[] for m in mon_names]
    for mon_idx,mon in enumerate(list(monitors.values())):
        screens.append(visual.Window(size=mon[1],screen=mon[0],winType="pyglet",
                                     useFBO=False,waitBlanking=False))
        visobjs[mon_idx].append(VisObj(visual.TextStim(win=screens[-1],text="+",color=(1,1,1))))
        visobjs[mon_idx].append(VisObj(visual.TextStim(win=screens[-1],text=mon_names[mon_idx],color=(1,1,1),pos=(0,-0.5))))
        
    refresh_rates = [[] for x in range(cycles)]
    for cyc in range(cycles):
        for scr_idx, scr in enumerate(screens):
            t_start = time.perf_counter()
            visobjs[scr_idx][0].color = col_anim((.5,.5,.5),(1,0,0),int(test_length/3)) + \
            col_anim((1,0,0),(0,1,0),int(test_length/3)) + \
            col_anim((0,1,0),(0,0,1),int(test_length/3))
            for f_idx in range(test_length):
                for v in visobjs[scr_idx]:
                    v.draw()
                scr.flip()
            t_end = time.perf_counter()
            refresh_rates[cyc].append(t_end-t_start)
            visobjs[scr_idx][0].color = col_anim((.5,.5,.5),(1,0,0),int(test_length/3)) + \
            col_anim((1,0,0),(0,1,0),int(test_length/3)) + \
            col_anim((0,1,0),(0,0,1),int(test_length/3))
        t_start = time.perf_counter()
        for f_idx in range(test_length):
            for x_idx,x in enumerate(screens):
                for v in visobjs[x_idx]:
                    v.draw()
                x.flip()
        t_end = time.perf_counter()
        refresh_rates[cyc].append(t_end-t_start)
    
    [x.close() for x in screens]
    refresh_rates = np.array(refresh_rates)
    refresh_rates = np.round(test_length/refresh_rates).astype(int)
    refresh_rates = mode(refresh_rates)[0][0]
    return refresh_rates
