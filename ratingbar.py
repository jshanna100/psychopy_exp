from psychopy import visual, event
import numpy as np
import pyglet

''' TODO TODO TODO coordinate translation system is completely screwed up '''

class CoordFlipper():
    def __init__(self,richtung=0):
        self.richtung = richtung
    def __call__(self,coord):
        if len(coord) is not 2:
            raise ValueError("Coord flipping: only length of 2 accepted.")
        if self.richtung:
            coord=coord[::-1]
        return coord
        
class Rel2Abs():
    def __init__(self,abpos,lng_sht):
        # when given coords in relation to the bar, output absolute coordinates
        # abpos: tuple with xy coords of frame centre
        # lng_sht: tuple with length and width of frame
        if len(abpos) is not 2 or len(lng_sht) is not 2:
            raise ValueError("Coord transposition: only length of 2 accepted.")
        self.abpos = abpos
        self.lng_sht = lng_sht
    def __call__(self,rel_xy):
        abpos = self.abpos
        lng_sht = self.lng_sht
        output = (abpos[0]+rel_xy[0]*lng_sht[0]/4,abpos[1]+rel_xy[1]*lng_sht[1]/4)
        return output
    def resize(self,rel_size):
        lng_sht = self.lng_sht
        output = (rel_size[0]*lng_sht[0]/2,rel_size[1]*lng_sht[1]/2)
        return output


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
        self.visobj.draw()
        


class RatingBar():
    def __init__(self,win,pos,lng_sht,incr,decr_butts,incr_butts,conf_butts,orient="horizontal",midline_length=1,midline_pos=0,rval=0):
        richtung = 1 if orient=="vertical" else 0
        xyf = CoordFlipper(richtung=richtung)
        r2a = Rel2Abs(pos,xyf(lng_sht))
        visobjs={}
        visobjs["frame"]=VisObj(visual.Rect(win,units="norm",pos=pos,width=xyf(lng_sht)[0],height=xyf(lng_sht)[1],
          lineColor=(0,0,0)))
        visobjs["valrect"]=VisObj(visual.Rect(win,units="norm",pos=(0,0),width=0,height=0,lineColor=(0,0,0)))
        visobjs["midline"]=VisObj(visual.Line(win,r2a((midline_pos,midline_length)),
          r2a((midline_pos,-midline_length)),lineColor=(0,0,0)))
      
        self.visobjs = visobjs
        self.xyf = xyf
        self.r2a = r2a
        self.rval = rval
        self.midline_pos = midline_pos
        self.incr = incr
        self.incr_butts = incr_butts
        self.decr_butts = decr_butts
        self.conf_butts = conf_butts
      
    def draw(self):
        vis_list = list(self.visobjs.values())
        for vis in vis_list:
            vis.draw()
          
    def set_val(self,new_val):
        xyf = self.xyf
        r2a = self.r2a
        if new_val=="incr":
            new_val = self.rval + self.incr
        elif new_val=="decr":
            new_val = self.rval - self.incr
        self.rval = new_val
        new_dim = xyf(r2a.resize((abs(new_val),2)))
        self.visobjs["valrect"].visobj.width = new_dim[0]
        self.visobjs["valrect"].visobj.height = new_dim[1]
        self.visobjs["valrect"].visobj.pos = xyf(r2a((new_val,0)))
        if new_val < self.midline_pos:
            self.visobjs["valrect"].visobj.fillColor = (1,0,0)
        if new_val > self.midline_pos:
            self.visobjs["valrect"].visobj.fillColor = (0,0,1)
        self.draw()
        
    def confirm(self):
        return self.rval
            
        
class RBarVerkehr():
    def __init__(self,RBarList,win,duration=-1,extra_vis=[]):
        self.RBarList = RBarList
        self.duration = duration
        self.extra_vis = extra_vis
        self.win = win
    def go(self):
        key = pyglet.window.key
        keyboard = key.KeyStateHandler()
        self.win.winHandle.push_handlers(keyboard)
        # create list of relevant buttons for quick reference: list of lists; outer list corresponds to
        # Rating Bars in order, and inner lists are 0 for decrease buttons, 1 for increase, and 2 for confirm for that bar
        butt_lists = [[rb.decr_butts,rb.incr_butts,rb.conf_butts] for rb in self.RBarList]
        rates = np.ones(len(self.RBarList))*np.nan # ratings stored here
        # check for all possible button presses and react accordingly
        while np.any(np.isnan(rates)):
            for rb_idx,bl in enumerate(butt_lists):
                if any([keyboard[x] for x in bl[0]]) and self.RBarList[rb_idx].rval>-1: # decrease
                    self.RBarList[rb_idx].set_val("decr")
                if any([keyboard[x] for x in bl[1]]) and self.RBarList[rb_idx].rval<1: # increase
                    self.RBarList[rb_idx].set_val("incr")
                if any([keyboard[x] for x in bl[2]]): # confirm
                    rates[rb_idx] = self.RBarList[rb_idx].confirm()
            for rb in self.RBarList:
                rb.draw()
            for ev in self.extra_vis:
                ev.draw()
            self.win.flip()
        return rates