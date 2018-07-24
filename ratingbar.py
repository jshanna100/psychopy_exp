from psychopy import visual
import numpy as np

class CoordFlipper():
    def __init__(self,richtung=0):
        self.richtung = richtung
    def __call__(self,coord):
        if len(coord) is not 2:
            raise ValueError("Coord flipping: only length of 2 accepted.")
        if self.richtung:
            coord=coord[::-1]
        return coord

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
        
def draw_visobjs(visobjs):
    vis_list = list(visobjs.values())
    for vis in vis_list:
        vis.draw()


def RatingBar(win,dir0_butts,dir1_butts,confirm_butts,pos=(0,0),lng_sht=(1,0.2),orient="horizontal",
  midline_length=1,midline_pos=0):
    richtung = 1 if orient=="vertical" else 0
    xyf = CoordFlipper(richtung=richtung)
    visobjs={}
    visobjs["frame"]=VisObj(visual.Rect(win,units="norm",pos=xyf(pos),width=xyf(lng_sht)[0],height=xyf(lng_sht)[1],
      lineColor=(0,0,0)))
    visobjs["midline"]=VisObj(visual.Line(win,xyf((pos[0]+midline_pos*lng_sht[0]/2,pos[1]-midline_length*lng_sht[1]/2)),
      xyf((pos[0]+midline_pos*lng_sht[0]/2,pos[1]+midline_length*lng_sht[1]/2)),
    lineColor=(0,0,0)))

    for f in range(500):
        draw_visobjs(visobjs)
        win.flip()