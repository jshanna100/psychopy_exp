import numpy as np
from psychopy import visual, prefs, event
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound
from ratingbar import RatingBar,RBarVerkehr
from hearingtest import HearTest,HTestVerkehr
import pickle

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

class Block():
    def __init__(self,sounds,audschwank,visschwank,keys,beachten,play_len,
                 monitor_idx,beamer_idx):
        self.sounds = sounds
        self.audschwank = audschwank
        self.visschwank = visschwank
        self.keys = keys
        self.play_len = play_len 
        self.monitor_idx = monitor_idx
        self.beamer_idx = beamer_idx
        self.beachten = beachten
    def go(self):
        # get the schwank
        with open(self.audschwank,"rb") as f:
            audschwank = pickle.load(f)
        with open(self.visschwank,"rb") as f:
            visschwank = pickle.load(f)
        
        # set up the monitors
        back_color = (0.5,0.5,0.5)
        monitor = visual.Window(size=(700,700),color=back_color,
                                screen=self.monitor_idx,winType="pyglet")
        monitor_fps = np.round(1/monitor.monitorFramePeriod).astype(int)
        beamer = visual.Window(color=back_color,screen=self.beamer_idx,
                                   fullscr=True,winType="pyglet")
        beamer_fps = np.round(1/beamer.monitorFramePeriod).astype(int)
             
        fixation = VisObj(visual.TextStim(win=beamer,text="X",height=0.6,color=(0,0,0)))
        
        # randomly cycle through sounds
        keys = list(sounds.keys())
        reihenfolge = np.array(range(len(keys)))
        np.random.shuffle(reihenfolge)
        for abs_idx,sound_idx in enumerate(np.nditer(reihenfolge)):
            snd = sounds[keys[sound_idx]]
            aschw = np.round(audschwank[keys[sound_idx]]*beamer_fps*1e-3).astype(int)
            vschw = np.round(visschwank[keys[sound_idx]]*beamer_fps*1e-3).astype(int)
            
            aud_check_keys = 0
            vid_check_keys = 0
            snd.play(loops=5)
            for f in range(self.play_len*beamer_fps):
                if f in aschw:
                    fixation.color = col_anim((0,0,0),(0.25,0.25,0.25),beamer_fps//4) + \
                      col_anim((0.25,0.25,0.25),(0,0,0),beamer_fps//4)
                fixation.draw()
                beamer.flip()
            snd.stop()

sound_name_list = ["4000Hz.wav","4000_cheby.wav","4000_fftf.wav","7500Hz.wav"]
key_presses = ["3","4"] # these correspond to hitting "left" and "right"
ops = [60,30,15,7.5,3.25]
practice_ops = [15,0,0]
quorum = 2 # must have this many correct/incorrect to reduce/increase volume
play_duration = 2
jitter_range = (0.8,2)

ht = HearTest(sound_name_list,key_presses,ops,quorum,
             monitor_idx=0,beamer_idx=2,
             practice=0)
pt = HearTest(sound_name_list,key_presses,practice_ops,quorum,
             monitor_idx=0,beamer_idx=2,
             practice=1)

htv = HTestVerkehr(ht,pt,over_thresh=55)
sounds = htv.go()

a = Block(sounds,"audschwank","visschwank",["3","4"],0,50,0,2)     
a.go()            

            
            
            
        
        