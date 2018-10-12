from psychopy import visual, event
import numpy as np
import pyglet
        
def col_anim(beg,end,steps):
    # make color animations, put in start and finish RGB values and how many frames
    col_list = []
    for col_idx in range(3):
        col_list.append(list(np.linspace(beg[col_idx],end[col_idx],steps)))
    return list(zip(*col_list))

class Rel2Abs():
    def __init__(self,abpos,width,height,midline_pos,richtung):
        # when given coords in relation to the bar, output absolute coordinates
        # abpos: tuple with xy coords of frame centre
        # width: absolute width
        # height: absolute height
        # richtung: orientation of bar, 0 is horizontal, 1 is vertical
        if len(abpos) is not 2:
            raise ValueError("Coord transposition: only length of 2 accepted.")
        self.abpos = abpos
        self.width = width
        self.height = height
        self.richtung = richtung
    def __call__(self,rel_xy):
        abpos = self.abpos
        width,height = self.width,self.height
        if self.richtung:
            rel_xy = rel_xy[::-1]
        output = (abpos[0]+rel_xy[0]*width/2,
                  abpos[1]+rel_xy[1]*height/2)
        return output
    def resize(self,rel_size):
        width,height = self.width,self.height
        if self.richtung:
            rel_size = rel_size[::-1]
        output = (rel_size[0]*width,rel_size[1]*height)
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
    def __init__(self,win,pos,width,height,incr,decr_butts,incr_butts,
                 conf_butts,richtung=0,midline_length=1,midline_pos=0,
                 overcolor=(0,0,1),undercolor=(1,0,0),visobjs_extras={}):
        rval = midline_pos
        r2a = Rel2Abs(pos,width,height,midline_pos,richtung)
        visobjs={}
        visobjs["frame"]=VisObj(visual.Rect(win,units="norm",pos=pos,
               width=width,height=height,lineColor=(-1,-1,-1)))
        visobjs["valrect"]=VisObj(visual.Rect(win,units="norm",pos=(0,0),
               width=0,height=0,lineColor=(-1,-1,-1),fillColor=(0,0,0)))
        visobjs["midline"]=VisObj(visual.Line(win,r2a((midline_pos,midline_length)),
          r2a((midline_pos,-midline_length)),lineColor=(-1,-1,-1)))
        
        self.visobjs = {**visobjs, **visobjs_extras}
        self.r2a = r2a
        self.rval = rval
        self.midline_pos = midline_pos
        self.incr = incr
        self.incr_butts = incr_butts
        self.decr_butts = decr_butts
        self.conf_butts = conf_butts
        self.overcolor = overcolor
        self.undercolor = undercolor
        
    def draw(self):
        vis_list = list(self.visobjs.values())
        for vis in vis_list:
            vis.draw()
          
    def set_val(self,new_val):
        if new_val=="incr":
            new_val = self.rval + self.incr
        elif new_val=="decr":
            new_val = self.rval - self.incr
        if new_val > 1 or new_val < -1:
            new_val = np.round(new_val)
        self.rval = new_val
        
        new_dim = self.r2a.resize((abs(new_val-self.midline_pos)/2,1))
        self.visobjs["valrect"].visobj.width = new_dim[0]
        self.visobjs["valrect"].visobj.height = new_dim[1]
        self.visobjs["valrect"].visobj.pos = self.r2a(((self.midline_pos+new_val)/2,0))
        if new_val < self.midline_pos:           
            self.visobjs["valrect"].visobj.fillColor = self.undercolor
        if new_val > self.midline_pos:
            self.visobjs["valrect"].visobj.fillColor = self.overcolor
        self.draw()
        
    def confirm(self):
        vo = self.visobjs["valrect"]
        flash = col_anim(vo.visobj.fillColor,(0.9,0.9,0.9),10)
        fossil = col_anim((0.9,0.9,0.9),(-.5,-.5,-.5),10)
        vo.fillColor = flash + fossil
        return self.rval
    def unconfirm(self):
        restore_color = self.undercolor if self.rval < 0 else self.overcolor
        vo = self.visobjs["valrect"]
        flash = col_anim((-.5,-.5,-.5),(0.9,0.9,0.9),10)
        entfossil = col_anim((0.9,0.9,0.9),restore_color,10)
        vo.fillColor = flash + entfossil
        return np.nan


                    
class RBarVerkehr():
    def __init__(self,RBarList,win,duration=-1,extra_vis=[],fps=60):
        self.RBarList = RBarList
        self.duration = duration
        self.extra_vis = extra_vis
        self.win = win
        self.fps = fps
    def go(self):
        key = pyglet.window.key
        keyboard = key.KeyStateHandler()
        self.win.winHandle.push_handlers(keyboard)
        # create list of relevant buttons for quick reference: list of lists; outer list corresponds to
        # Rating Bars in order, and inner lists are 0 for decrease buttons, 1 for increase, and 2 for confirm for that bar
        butt_lists = [[rb.decr_butts,rb.incr_butts,rb.conf_butts] for rb in self.RBarList]
        rates = np.ones(len(self.RBarList))*np.nan # ratings stored here
        # check for all possible button presses and react accordingly
        while any(np.isnan(rates)):
            for rb_idx,bl in enumerate(butt_lists):
                if any([keyboard[x] for x in bl[0]]) and self.RBarList[rb_idx].rval>-1 and np.isnan(rates[rb_idx]): # decrease
                    self.RBarList[rb_idx].set_val("decr")
                if any([keyboard[x] for x in bl[1]]) and self.RBarList[rb_idx].rval<1 and np.isnan(rates[rb_idx]): # increase
                    self.RBarList[rb_idx].set_val("incr")
                if any([keyboard[x] for x in bl[2]]): # confirm or unconfirm
                    if np.isnan(rates[rb_idx]):
                        rates[rb_idx] = self.RBarList[rb_idx].confirm()
                    else:
                        rates[rb_idx] = self.RBarList[rb_idx].unconfirm()
                    keyboard.clear()
            for rb in self.RBarList:
                rb.draw()
            for ev in self.extra_vis:
                ev.draw()
            self.win.flip()
        for f in range(int(self.fps*0.5)):
            for rb in self.RBarList:
                rb.draw()
            for ev in self.extra_vis:
                ev.draw()
            self.win.flip()
        for rb in self.RBarList:
            rb.visobjs["valrect"].visobj.width=0
            rb.visobjs["valrect"].visobj.height=0
            rb.rval = rb.midline_pos
        return rates
