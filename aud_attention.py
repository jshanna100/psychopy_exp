import numpy as np
from psychopy import visual, prefs, event, core, parallel
prefs.general["audioLib"] = ["pygame"]
from psychopy import sound
from ratingbar import RatingBar,RBarVerkehr
from hearingtest import HearTest,HTestVerkehr
import pickle
from pyglet.window import key
import _thread
import time
import datetime
from tkinter import filedialog

def tile_audio(snd,length):
    tile_remain, tile_iters = np.modf(length/(len(snd)//44100))
    remain_idx = int(tile_remain*len(snd))
    snd = np.tile(snd,(int(tile_iters),1))
    if remain_idx:
        snd = np.concatenate((snd,snd[:remain_idx,:]))
    return snd

def add_schwank(snd,audschwank,length):
    for schw in np.iditer(audschwank):
        start_idx = int(np.round(schw*44.1))
        idx_length = length*44100
        end_idx = int(start_idx+idx_length)      
        for samp_count,samp_idx in enumerate(range(start_idx,end_idx)):
            snd[samp_idx,:] = snd[samp_idx,:]*0.5 + \
              snd[samp_idx,:]*0.5 * (1-np.sin((np.pi*samp_count)/(2*idx_length)))
    return snd
        

def aud_schwank(snd,schw_length,schw_step,port,aud_trig):
    t = time.clock()
    t_end = t + schw_length
    t_next = t + schw_step
    if port:
        port.setData(aud_trig)
    while t<t_end:
        t = time.clock()
        if t > t_next:
            snd.setVolume((1-np.sin(np.pi*((t_end-t)/schw_length)))*0.5+0.5)
            t_next = t + schw_step
    if port:
        port.setData(0)

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
                  data[x_idx,e_idx]*(np.sin((np.pi*x_idx)/data.shape[0]))/1.5
            else:
                data[x_idx,e_idx] = data[x_idx,e_idx] + \
                  data[x_idx,e_idx]*(np.sin((np.pi*x_idx)/data.shape[0]))/1.5
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
    
    def draw_visobjs(self,visobjs):
        vis_list = list(visobjs.values())
        for vis in vis_list:
            vis.draw()
    
    def exp_quit(self):
        self.monitor.close()
        self.beamer.close()
        core.quit()
    
    def __init__(self,sounddata,audschwank,visschwank,keys,beachten,play_len,
                 monitor_idx,beamer_idx,name="Experiment",monitor_fps=0,beamer_fps=0,
                 instruct="Instructions",aud_schw_len=0.5,vis_schw_len=0.5,
                 aud_trig=100,vis_trig=200,port=0):
        with open(audschwank,"rb") as f:
            self.audschwank = pickle.load(f)
        with open(visschwank,"rb") as f:
            self.visschwank = pickle.load(f)
        self.keys = keys
        self.play_len = play_len 
        self.monitor_idx = monitor_idx
        self.beamer_idx = beamer_idx
        self.beachten = beachten
        self.name = name
        self.monitor_fps = monitor_fps
        self.beamer_fps = beamer_fps
        self.instruct = instruct
        self.aud_trig = aud_trig
        self.vis_trig = vis_trig
        self.aud_schw_len = aud_schw_len
        self.vis_schw_len = vis_schw_len
        self.port = port
        sounds = {}
        for s in list(sounddata.keys()):
            temp_sound = tile_audio(sounddata[s],50)
            temp_sound = add_schwank(temp_sound,audschwank[s],0.5)
            sounds[s] = sound.Sound(temp_sound)
        self.sounds = sounds
        
    def go(self):
        ratings = []
        # set up the monitors
        back_color = (0.5,0.5,0.5)
        monitor = visual.Window(size=(700,700),color=back_color,
                                screen=self.monitor_idx,winType="pyglet")
        
        self.monitor = monitor
        monitor.waitBlanking = False
        beamer = visual.Window(color=back_color,screen=self.beamer_idx,
                                       fullscr=False,size=(1280,1024),winType="pyglet")
        self.beamer = beamer
        beamer.waitBlanking = False
            
        if not self.monitor_fps:
            self.monitor_fps = np.round(1/monitor.monitorFramePeriod).astype(int)
        if not self.beamer_fps:  
            self.beamer_fps = np.round(1/beamer.monitorFramePeriod).astype(int)
        
        print("Monitor fps: " + str(self.monitor_fps))
        print("Beamer fps: " + str(self.beamer_fps))
             
        instruct_disp = {}
        instruct_disp["instruct"] = visual.TextStim(win=beamer,text=self.instruct,color=(0,0,0),
                  pos=(0,0),height=0.3)
  
        panel_disp = {}
        panel_disp["title"] = visual.TextStim(win=monitor,text=self.name,
                  pos=(-0.8,0.8),height=0.07,color=(0,0,0),alignHoriz="left")
        panel_disp["progress"] = visual.TextStim(win=monitor,text="Trial: ",
          pos=(-0.8,0.65),height=0.09,color=(0,0,0),alignHoriz="left")
        panel_disp["status"] = visual.TextStim(win=monitor,
                  text="",color=(0,0,0),
                  pos=(0,0),height=0.1)        
        
        pause_disp = {}
        pause_disp["panel_flash"] = visual.TextStim(win=monitor,
                  text="Block finished. Press p to continue.",color=(1,0,0),
                  pos=(0,-0.5),height=0.1)
        pause_disp["beamer_smile"] = visual.ImageStim(win=beamer,image="ausruhen1.png")
        
        fixation = VisObj(visual.TextStim(win=beamer,text="X",height=0.15,color=(0,0,0)))
        
        # set up rating bars
        down_butts = [key._3]
        up_butts = [key._4]
        conf_ud_butts = [key._1]
        left_butts = [key._7]
        right_butts = [key._8]
        conf_lr_butts = [key._0]
        
        extra_vis_vol = []
        extra_vis_ang = []
        
        volume = RatingBar(beamer,(-0.5,0),0.1,0.75,0.02,down_butts,up_butts,conf_ud_butts,
                           richtung=1,midline_length=1.5,midline_pos=-1,overcolor=(0,0,1))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="leise",pos=(-0.5,-0.5),height=0.07,color=(0,0,0),bold=True))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="laut",pos=(-0.5,0.5),height=0.07,color=(0,0,0),bold=True))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="Wie laut empfandest Du den Ton eben?",pos=(-0.5,0.75),height=0.07,color=(0,0,0)))
        
        angenehm = RatingBar(beamer,(0.5,0),0.75,0.15,0.02,left_butts,right_butts,conf_lr_butts,
                           richtung=0,midline_length=1.5,midline_pos=0,overcolor=(0,1,0),undercolor=(1,0,0))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="unangenehm",pos=(0.1,-0.2),height=0.07,color=(0,0,0),bold=True))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="angenehm",pos=(0.8,-0.2),height=0.07,color=(0,0,0),bold=True))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="Wie un/angenehm empfandest Du den Ton eben?",pos=(0.5,0.75),height=0.07,color=(0,0,0)))
        
        rbv = RBarVerkehr([volume,angenehm],beamer,extra_vis=extra_vis_vol+extra_vis_ang,fps=85)
        
        # instructions
        panel_disp["status"].text = "Subject reading instructions..."
        while not event.getKeys(["0","1","2","3","4","5","6","7","8","9"]):
            self.draw_visobjs({**panel_disp,**instruct_disp})
            monitor.flip()
            beamer.flip()
        panel_disp["status"].text = ""
        # randomly cycle through sounds
        keys = list(self.sounds.keys())
        reihenfolge = np.array(range(len(keys)))
        np.random.shuffle(reihenfolge)
        for abs_idx,sound_idx in enumerate(np.nditer(reihenfolge)):
            # update panel
            panel_disp["progress"].text="Trial: {} of {}".format(abs_idx+1,
                      len(reihenfolge))
            panel_disp["status"].text = "Subject is receiving stimuli..."
            # load sound, create sound Schwankung
            snd = self.sounds[keys[sound_idx]]
            # load Schwankungen
            aschw = np.round(self.audschwank[keys[sound_idx]]*self.beamer_fps*1e-3).astype(int)
            vschw = np.round(self.visschwank[keys[sound_idx]]*self.beamer_fps*1e-3).astype(int)
            
            event.clearEvents()
            snd.play()
            vis_check = 0
            aud_check = 0
            for f in range(self.play_len*self.beamer_fps):
                if f in aschw:
                    #_thread.start_new_thread(aud_schwank,(snd,self.aud_schw_len,0.001,self.port,self.aud_trig))
                    aud_check = int(self.beamer_fps*self.aud_schw_len)
                    panel_disp["status"].text = "AUDITORY MODULATION"
                    panel_disp["status"].color = (1,0,0)
                if f in vschw:
                    fixation.color = col_anim((0,0,0),(0.25,0.25,0.25),self.beamer_fps//4) + \
                      col_anim((0.25,0.25,0.25),(0,0,0),self.beamer_fps//4)
                    vis_check = int(self.beamer_fps*self.vis_schw_len)
                    if self.port:
                        self.port.setData(self.vis_trig)
                    panel_disp["status"].text = "VISUAL MODULATION"
                    panel_disp["status"].color = (1,0,0)  
                fixation.draw()
                self.beamer.flip()
                self.draw_visobjs(panel_disp)           
                self.monitor.flip()
                if vis_check:
                    vis_check -= 1
                if aud_check:
                    aud_check -= 1
                if not vis_check and not aud_check:
                    if self.port:
                        self.port.setData(0)
                    panel_disp["status"].text = "Subject is receiving stimuli..."
                    panel_disp["status"].color = (0,0,0)

            snd.stop()
            beamer.winHandle.activate()
            panel_disp["status"].text = "Subject is rating stimuli..."
            self.draw_visobjs(panel_disp)
            monitor.flip()
            ratings.append([abs_idx,self.name,keys[sound_idx],rbv.go()])
            if "q" in event.getKeys(["q"]):
                self.exp_quit()
        while "p" not in event.getKeys(["p"]):
            self.draw_visobjs({**panel_disp, **pause_disp})
            monitor.flip()
            beamer.flip()
        
        monitor.close()
        beamer.close()
        return ratings                
            

# define and run hearing test
sound_name_list = ["4000Hz.wav","4000_cheby.wav","4000_fftf.wav","7500Hz.wav"]
#sound_name_list = ["7500Hz.wav"]
key_presses = ["2","9"] # these correspond to hitting "left" and "right"
ops = [40,20,10,5,2.5]
practice_ops = [15,0,0]
quorum = 2 # must have this many correct/incorrect to reduce/increase volume
play_duration = 2
jitter_range = (0.8,2)
use_parport = 0

if use_parport:
    port = parallel.ParallelPort(address="/dev/parport0")

ht = HearTest(sound_name_list,key_presses,ops,quorum,
             monitor_idx=1, beamer_idx=0,practice=0)
pt = HearTest(sound_name_list,key_presses,practice_ops,quorum,
             monitor_idx=1, beamer_idx=0,practice=1)

htv = HTestVerkehr(ht,pt,over_thresh=40)
sounddata = htv.go()


a = Block(sounddata,"audschwank","empty",["3","4","7","8"],"audio",50,1,0,name="Audio modulations only", beamer_fps=85,aud_schw_len=0.5)
b = Block(sounddata,"audschwank","visschwank_selten",["3","4","7","8"],"audio",50,1,0,name="Infrequent visual modulations, attend audio modulations only", beamer_fps=85)
c = Block(sounddata,"empty","visschwank",["3","4","7","8"],"video",50,1,0,name="Visual modulations only", beamer_fps=85)
d = Block(sounddata,"empty","empty",["3","4","7","8"],"none",50,1,0,name="No modulations", beamer_fps=85)
           
results = []
#results += a.go()            
results += b.go()
#results += c.go()
#results += d.go()

now = datetime.datetime.now()
filename = filedialog.asksaveasfilename(filetypes=(("Text file","*.txt"),("All files","*.*")))

if filename:
    with open(filename,"w") as file:
        file.write("Subject {sub}, recorded on {d}.{m}.{y}, {h}:{mi}\n".format(
          sub="test",d=now.day,m=now.month,y=now.year,h=now.hour,mi=now.minute))
        file.write("Index\tBlock\tWavfile\tLaut\tAngenehm\n")
        for res in results:
           file.write("{idx}\t{block}\t{name}\t{laut}\t{angenehm}\n".format(
             idx=res[0],block=res[1],name=res[2],laut=res[3][0],angenehm=res[3][1]))       
            
            
            
        
        
