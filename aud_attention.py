import numpy as np
from psychopy import visual, prefs, event
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound
from ratingbar import RatingBar,RBarVerkehr
from hearingtest import HearTest,HTestVerkehr
import pickle
from pyglet.window import key

def col_anim(beg,end,steps):
    # make color animations, put in start and finish RGB values and how many frames
    col_list = []
    for col_idx in range(3):
        col_list.append(list(np.linspace(beg[col_idx],end[col_idx],steps)))
    return list(zip(*col_list))

def amp_adjust(data,direction=-1):
    for e_idx in range(2):
        for x_idx in range(data.shape[0]):
            if direction == -1:
                data[x_idx,e_idx] = data[x_idx,e_idx] - \
                  data[x_idx,e_idx]*(np.sin((np.pi*x_idx)/data.shape[0]))/2
            else:
                data[x_idx,e_idx] = data[x_idx,e_idx] + \
                  data[x_idx,e_idx]*(np.sin((np.pi*x_idx)/data.shape[0]))/2
    return data

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
    def __init__(self,sounddata,audschwank,visschwank,keys,beachten,play_len,
                 monitor_idx,beamer_idx,direction=-1):
        self.sounddata = sounddata
        sounds = {}
        for s in list(sounddata.keys()):
            sounds[s] = sound.Sound(sounddata[s])
        self.sounds = sounds
        self.audschwank = audschwank
        self.visschwank = visschwank
        self.keys = keys
        self.play_len = play_len 
        self.monitor_idx = monitor_idx
        self.beamer_idx = beamer_idx
        self.beachten = beachten
        self.direction = direction
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
        monitor.waitBlanking = False
        beamer = visual.Window(color=back_color,screen=self.beamer_idx,
                                   fullscr=True,winType="pyglet")
        beamer.waitBlanking = False
        monitor_fps = np.round(1/monitor.monitorFramePeriod).astype(int)
        beamer_fps = np.round(1/beamer.monitorFramePeriod).astype(int)
             
        fixation = VisObj(visual.TextStim(win=beamer,text="X",height=0.6,color=(0,0,0)))
        
        # set up rating bars
        down_butts = [key._3]
        up_butts = [key._4]
        conf_ud_butts = [key._0]
        left_butts = [key._8]
        right_butts = [key._7]
        conf_lr_butts = [key._1]
        
        extra_vis_vol = []
        extra_vis_ang = []
        
        volume = RatingBar(beamer,(-0.5,0),0.1,0.75,0.02,down_butts,up_butts,conf_ud_butts,
                           richtung=1,midline_length=1.5,midline_pos=-1,overcolor=(0,0,1))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="leise",pos=(-0.5,-0.5),height=0.07,color=(0,0,0),bold=True))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="laut",pos=(-0.5,0.5),height=0.07,color=(0,0,0),bold=True))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="Wie laut empfandest Du den Ton eben?",pos=(-0.5,0.75),height=0.07,color=(0,0,0)))
        
        angenehm = RatingBar(beamer,(0.5,0),0.75,0.15,0.02,left_butts,right_butts,conf_lr_butts,
                           richtung=0,midline_length=1.5,midline_pos=0,overcolor=(0,1,0),undercolor=(1,0,0))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="unangenehm",pos=(0.15,-0.2),height=0.07,color=(0,0,0),bold=True))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="angenehm",pos=(0.85,-0.2),height=0.07,color=(0,0,0),bold=True))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="Wie un/angenehm empfandest Du den Ton eben?",pos=(0.5,0.75),height=0.07,color=(0,0,0)))
        
        rbv = RBarVerkehr([volume,angenehm],beamer,extra_vis=extra_vis_vol+extra_vis_ang)
        
        # randomly cycle through sounds
        keys = list(self.sounds.keys())
        reihenfolge = np.array(range(len(keys)))
        np.random.shuffle(reihenfolge)
        for abs_idx,sound_idx in enumerate(np.nditer(reihenfolge)):
            # load sound, create sound Schwankung
            snd = self.sounds[keys[sound_idx]]
            schw_snd = sound.Sound(amp_adjust(self.sounddata[keys[sound_idx]][:44100,],
                                   direction=self.direction))
            # load Schwankungen
            aschw = np.round(audschwank[keys[sound_idx]]*beamer_fps*1e-3).astype(int)
            vschw = np.round(visschwank[keys[sound_idx]]*beamer_fps*1e-3).astype(int)
            
            aud_check_keys = 0
            vid_check_keys = 0
            snd.play(loops=2)
            for f in range(self.play_len*beamer_fps):
                trigger = 20 if self.beachten else 10
                if f in aschw:
                    snd.stop()
                    schw_snd.play()
                    aud_check_keys = beamer_fps
                if f in vschw:
                    fixation.color = col_anim((0,0,0),(0.25,0.25,0.25),beamer_fps//4) + \
                      col_anim((0.25,0.25,0.25),(0,0,0),beamer_fps//4)
                    vid_check_keys = beamer_fps
                if aud_check_keys > 0:
                    if event.getKeys(self.keys) and not self.beachten:
                        trigger += 1
                        print("audio hit")
                    aud_check_keys -= 1
                    if not aud_check_keys:
                        schw_snd.stop()
                        snd.play()
                if vid_check_keys > 0:
                    if event.getKeys(self.keys) and self.beachten:
                        trigger += 1
                        print("video hit")
                    vid_check_keys -= 1
                
                fixation.draw()
                beamer.flip()                
                monitor.flip()
            
            snd.stop()
            beamer.winHandle.activate()
            rbv.go()
            

# define and run hearing test
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
sounddata = htv.go()

a = Block(sounddata,"audschwank","empty",["3","4"],0,50,0,2)
b = Block(sounddata,"audschwank","visschwank_selten",["3","4"],0,50,0,2,direction=1)
c = Block(sounddata,"empty","visschwank",["3","4"],1,50,0,2)
d = Block(sounddata,"empty","empty",["3","4"],1,50,0,2)
           
a.go()            
b.go()
c.go()
d.go()
            
            
            
        
        