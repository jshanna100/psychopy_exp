import numpy as np
from psychopy import visual, prefs, event, core, parallel
prefs.general["audioLib"] = ["pygame"]
from psychopy import sound
from ratingbar import RatingBar,RBarVerkehr
from hearingtest import HearTest,HTestVerkehr
import pickle
from pyglet.window import key
import time
import datetime
from tkinter import filedialog
import argparse
from reftime import refresh_timer
import sys

def tile_audio(snd,length):
    tile_remain, tile_iters = np.modf(length/(len(snd)//44100))
    remain_idx = int(tile_remain*len(snd))
    new_snd = np.tile(snd,(int(tile_iters),1))
    if remain_idx:
        new_snd = np.concatenate((new_snd,snd[:remain_idx,:]))
    return new_snd

def add_schwank(snd,audschwank,length):
    for schw in np.nditer(audschwank):
        start_idx = int(np.round(schw*44.1))
        idx_length = length*44100
        end_idx = int(start_idx+idx_length)
        if end_idx < len(snd):
            for samp_count,samp_idx in enumerate(range(start_idx,end_idx)):
                snd[samp_idx,:] = snd[samp_idx,:]*0.5 + \
                  snd[samp_idx,:]*0.5 * (1-np.sin((np.pi*samp_count)/idx_length))
    return snd

def add_tone(snd,audschwank,length,add_snds):
    rand_idx = (0, 2, 1, 1, 0, 0, 1, 2, 2, 1, 2, 0, 1, 1, 2, 2, 0, 0)
    for schw_idx,schw in enumerate(np.nditer(audschwank)):
        start_idx = int(np.round(schw*44.1))
        idx_length = length*44100
        end_idx = int(start_idx+idx_length)
        if end_idx < len(snd):
            for samp_count,samp_idx in enumerate(range(start_idx,end_idx)):
                snd[samp_idx,:] = snd[samp_idx,:]*0.15 + \
                  snd[samp_idx,:]*0.85 * (1-np.sin((np.pi*samp_count)/(idx_length)))
                snd[samp_idx,:] += add_snds[rand_idx[schw_idx]][samp_count,:] * \
                  (np.sin((np.pi*samp_count)/(idx_length)))
    return snd

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

class TriggerSet():
    def __init__(self,port):
        self.port = port
    def set_val(self,value):
        if port==-1:
            return
        else:
            port.setData(value)
    def reset(self):
        if port==-1:
            return
        else:
            port.setData(0)
    def read_val(self):
        return port.readData()
        
class RestingState():
    
    def __init__(self,monitor_idx,beamer_idx,monitor_fps=0,beamer_fps=0,
                 start_trig=255,length=180,back_color=(0,0,0),
                 text_color=(-1,-1,-1),port=-1):
        
        self.monitor_idx = monitor_idx
        self.beamer_idx = beamer_idx
        self.start_trig = start_trig
        self.length = length
        self.back_color = back_color
        self.text_color = text_color
        self.port = TriggerSet(port)
        
    def draw_visobjs(self,visobjs):
        vis_list = list(visobjs.values())
        for vis in vis_list:
            vis.draw()
        
    def go(self):            

        monitor = visual.Window(size=(700,700),color=self.back_color,
                                screen=self.monitor_idx,winType="pyglet",
                                useFBO=False,waitBlanking=False)       
        beamer = visual.Window(color=self.back_color,screen=self.beamer_idx,
                                       fullscr=False,size=(1280,1024),
                                       winType="pyglet",useFBO=False,
                                       waitBlanking=False)
        

        panel_disp = {}
        panel_disp["title"] = visual.TextStim(win=monitor,text="Resting State",
                  pos=(-0.8,0.8),height=0.07,color=self.text_color,alignHoriz="left")
        panel_disp["progress"] = visual.TextStim(win=monitor,text="Press p to start resting state",
          pos=(-0.8,0.65),height=0.09,color=self.text_color,alignHoriz="left")
        
        while "p" not in event.getKeys(["p"]):
            self.draw_visobjs(panel_disp)
            monitor.flip()
        
        beam_disp = {}
        beam_disp["fixation"] = visual.TextStim(win=beamer,text="+",color=(1,1,1))
        
        self.port.set_val(self.start_trig)
            
        beg_time = time.perf_counter()
        sec_counter = 0
        now = time.perf_counter()
        while now < beg_time+self.length:
            if np.round(now)>sec_counter:
                sec_counter = np.round(now-beg_time).astype(int)
                panel_disp["progress"].text = "Remaining: "+ str(
                        self.length-sec_counter)    
                self.draw_visobjs(beam_disp)
                self.draw_visobjs(panel_disp)   
                beamer.flip()
                monitor.flip()
            now = time.perf_counter()
        core.wait(0.5)
        self.port.reset()
        
        panel_disp["progress"] = visual.TextStim(win=monitor,text="Press p to proceed.",
          pos=(-0.8,0.65),height=0.09,color=self.text_color,alignHoriz="left")
        while "p" not in event.getKeys(["p"]):
            self.draw_visobjs(panel_disp)
            monitor.flip()
        
        monitor.close()
        beamer.close()

class Block():
    
    def draw_visobjs(self,visobjs):
        vis_list = list(visobjs.values())
        for vis in vis_list:
            vis.draw()
    
    def exp_quit(self):
        self.monitor.close()
        self.beamer.close()
        core.quit()
    
    def __init__(self,sounddata,audschwank,visschwank,torespond,keys,play_len,
                 monitor_idx,beamer_idx,name="Experiment",monitor_fps=60,beamer_fps=60,
                 instruct="Instructions",aud_schw_len=0.5,vis_schw_len=0.5,
                 aud_trig=100,vis_trig=200,port=-1,schw_or_add="schwank",id_trig=1,
                 practice=0,stim_start_trig=50,resp_len=1.5,back_color=(0,0,0),
                 text_color=(-1,-1,-1),time_events=1,right_trig=225,wrong_trig=250,
                 combined_fps=60):
        with open(audschwank,"rb") as f:
            self.audschwank = pickle.load(f)
        with open(visschwank,"rb") as f:
            self.visschwank = pickle.load(f)
        with open(torespond,"rb") as f:
            self.torespond = pickle.load(f)
        self.sounddata = sounddata[0]
        self.keys = keys
        self.play_len = play_len 
        self.monitor_idx = monitor_idx
        self.beamer_idx = beamer_idx
        self.name = name
        self.monitor_fps = monitor_fps
        self.beamer_fps = beamer_fps
        self.instruct = instruct
        self.aud_trig = aud_trig
        self.vis_trig = vis_trig
        self.aud_schw_len = aud_schw_len
        self.vis_schw_len = vis_schw_len
        self.port = TriggerSet(port)
        self.schw_or_add = schw_or_add
        self.id_trig = id_trig
        self.practice = practice
        self.stim_start_trig = stim_start_trig
        self.resp_len = resp_len
        self.back_color = back_color
        self.text_color = text_color
        self.time_events = time_events
        self.right_trig=right_trig
        self.wrong_trig=wrong_trig
        self.combined_fps = combined_fps
        print("Building stimuli...")
        kurz_sounds = {}
        for s in list(self.sounddata.keys()):
            temp_sound = tile_audio(self.sounddata[s],aud_schw_len)
            kurz_sounds[s] = temp_sound
        self.kurz_sounds = kurz_sounds
        sounds = {}
        for s in list(self.sounddata.keys()):
            temp_sound = tile_audio(self.sounddata[s],play_len)
            if len(self.audschwank[s]):
                if schw_or_add == "schwank":
                    temp_sound = add_schwank(temp_sound,self.audschwank[s],aud_schw_len)
                elif schw_or_add == "add":
                    add_snds = kurz_sounds.copy()
                    del add_snds[s]
                    add_snds = list(add_snds.values())
                    temp_sound = add_tone(temp_sound,self.audschwank[s],aud_schw_len,add_snds)
            sounds[s] = sound.Sound(temp_sound)
        self.sounds = sounds
        print("Done.")
        
    def go(self):
        ratings = []
        # set up the monitors
        monitor = visual.Window(size=(800,600),color=self.back_color,
                                screen=self.monitor_idx,winType="pyglet",
                                useFBO=False,waitBlanking=False)       
        beamer = visual.Window(color=self.back_color,screen=self.beamer_idx,
                                       fullscr=False,size=(1280,1024),winType="pyglet",
                                       useFBO=False,waitBlanking=False)
        
        print("Monitor fps: " + str(self.monitor_fps))
        print("Beamer fps: " + str(self.beamer_fps))
        print("Combined fps: " + str(self.combined_fps))
             
        # build the display objects
        
        instruct_disp = {}
        instruct_disp["instruct"] = visual.TextStim(win=beamer,text=self.instruct,
                     color=self.text_color,pos=(0,0),height=0.07,wrapWidth=1.5)
  
        panel_disp = {}
        panel_disp["title"] = visual.TextStim(win=monitor,text=self.name,
                  pos=(-0.8,0.8),height=0.07,color=self.text_color,alignHoriz="left")
        panel_disp["progress"] = visual.TextStim(win=monitor,text="Trial: ",
          pos=(-0.8,0.65),height=0.09,color=self.text_color,alignHoriz="left")
        panel_disp["status"] = visual.TextStim(win=monitor,
                  text="",color=self.text_color,
                  pos=(0,0),height=0.1)
        panel_disp["feedback"] = VisObj(visual.TextStim(win=monitor,
                  text="",color=self.text_color,
                  pos=(0,-.3),height=0.1))        
        
        pause_disp = {}
        pause_disp["panel_flash"] = visual.TextStim(win=monitor,
                  text="Block finished. Press p to continue.",color=(1,-1,-1),
                  pos=(0,-0.5),height=0.1)
        pause_disp["beamer_smile"] = visual.ImageStim(win=beamer,image="ausruhen1.png")
        
        beam_disp = {}
        beam_disp["fixation"] = VisObj(visual.TextStim(win=beamer,text="+",color=self.text_color))
        beam_disp["feedback"] = VisObj(visual.TextStim(win=beamer,text="",
                 color=self.text_color, pos=(0,0.3),height=0.15))
        
        # set up rating bars
        down_butts = [key._8]
        up_butts = [key._9]
        conf_ud_butts = [key._6]
        left_butts = [key._2]
        right_butts = [key._3]
        conf_lr_butts = [key._5]
        
        extra_vis_vol = []
        extra_vis_ang = []
        
        volume = RatingBar(beamer,(-0.5,0),0.1,0.75,0.01,down_butts,up_butts,conf_ud_butts,
                           richtung=1,midline_length=1.5,midline_pos=-1,overcolor=(-1,-1,1))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="leise",pos=(-0.5,-0.5),height=0.07,color=self.text_color,bold=True))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="laut",pos=(-0.5,0.5),height=0.07,color=self.text_color,bold=True))
        extra_vis_vol.append(visual.TextStim(win=beamer,text="Wie laut empfandest Du den Ton eben?",pos=(-0.5,0.75),height=0.07,color=self.text_color))
        
        angenehm = RatingBar(beamer,(0.5,0),0.75,0.15,0.01,left_butts,right_butts,conf_lr_butts,
                           richtung=0,midline_length=1.5,midline_pos=0,overcolor=(-1,0.5,-0.8),undercolor=(1,-1,-1))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="unangenehm",pos=(0.1,-0.2),height=0.07,color=self.text_color,bold=True))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="angenehm",pos=(0.8,-0.2),height=0.07,color=self.text_color,bold=True))
        extra_vis_ang.append(visual.TextStim(win=beamer,text="Wie un/angenehm empfandest Du den Ton eben?",pos=(0.5,0.75),height=0.07,color=self.text_color))
        
        rbv = RBarVerkehr([volume,angenehm],beamer,extra_vis=extra_vis_vol+extra_vis_ang,fps=self.beamer_fps)
        
        # preprocess color animations
        col_anims = {}
        col_anims["visschw"] = col_anim((-1,-1,-1),(0,0,0),
                 np.round(self.combined_fps*self.vis_schw_len/2).astype(int)) + \
                 col_anim((0,0,0),(-1,-1,-1),
                 np.round(self.combined_fps*self.vis_schw_len/2).astype(int))
        col_anims["correct"] = col_anim((-1,1,-1),self.back_color,self.combined_fps)
        col_anims["incorrect"] = col_anim((1,-1,-1),self.back_color,self.combined_fps)
        if self.practice:
            col_anims["treffer"] = col_anim(self.back_color,(-1,1,-1),self.combined_fps//2) + \
                              col_anim((-1,1,-1),self.back_color,self.combined_fps)
            col_anims["falsch"] = col_anim(self.back_color,(1,-1,-1),self.combined_fps//2) + \
                                      col_anim((1,-1,-1),self.back_color,self.combined_fps)                
        
        # instructions
        event.clearEvents()
        panel_disp["status"].text = "Subject reading instructions..."
        while not event.getKeys(["0","1","2","3","4","5","6","7","8","9"]):
            self.draw_visobjs({**panel_disp,**instruct_disp})
            monitor.flip()
            beamer.flip()
        panel_disp["status"].text = ""
        
        # send id trigger, to confirm what block we're in
        self.port.set_val(self.id_trig)
        
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

            aschw = list(self.audschwank[keys[sound_idx]])
            vschw = list(self.visschwank[keys[sound_idx]])
            toresp = list(self.torespond[keys[sound_idx]] )         
            # send trigger and play sound
            self.port.set_val(sound_idx+1)
            snd.play()
            
            # run modulations
            resp_check = 0
            event.clearEvents()
            a_next = aschw.pop(0) if aschw else np.inf
            v_next = vschw.pop(0) if vschw else np.inf
            t_next = toresp.pop(0) if toresp else np.inf
            aud_schw_time = np.nan
            vis_schw_time = np.nan
            beg_time = time.perf_counter()
            while (time.perf_counter()-beg_time) < self.play_len:
                now = (time.perf_counter()-beg_time)*1000
                if now >= a_next:
                    a_next = aschw.pop(0) if aschw else np.inf
                    aud_schw_time = now+self.aud_schw_len*1000
                    panel_disp["status"].text = "AUDITORY MODULATION"
                    panel_disp["status"].color = (1,-1,-1)
                    self.port.set_val(self.aud_trig)
                if now >= v_next:
                    v_next = vschw.pop(0) if vschw else np.inf
                    vis_schw_time = now+self.vis_schw_len*1000
                    beam_disp["fixation"].color = col_anims["visschw"].copy()
                    beamer.callOnFlip(self.port.set_val,self.vis_trig)
                    panel_disp["status"].text = "VISUAL MODULATION"
                    panel_disp["status"].color = (1,-1,-1)
                if now >= t_next:
                    t_next = toresp.pop(0) if toresp else np.inf
                    resp_check = now + self.resp_len*1000
                    event.clearEvents()                        
                if event.getKeys(["0","1","2","3","4","5","6","7","8","9"]):
                    if now < resp_check:
                        panel_disp["feedback"].visobj.text = "Subject responded correctly."
                        panel_disp["feedback"].color = col_anims["correct"].copy()
                        self.port.set_val(self.right_trig)
                        if self.practice:
                            beam_disp["feedback"].visobj.text = "Treffer!"
                            beam_disp["feedback"].color = col_anims["treffer"].copy()
                        event.clearEvents()
                    else:
                        panel_disp["feedback"].visobj.text = "Subject responded incorrectly."
                        panel_disp["feedback"].color = col_anims["incorrect"].copy()
                        self.port.set_val(self.wrong_trig)
                        if self.practice:
                            beam_disp["feedback"].visobj.text = "Falsch!"
                            beam_disp["feedback"].color = col_anims["falsch"].copy()                        
                        event.clearEvents()  
                
                if not all(np.isnan((aud_schw_time,vis_schw_time))):
                    if now > aud_schw_time:
                        aud_schw_time = np.nan    
                    if now > vis_schw_time:
                        vis_schw_time = np.nan
                    if all(np.isnan((aud_schw_time,vis_schw_time))):
                        if self.port:
                            self.port.set_val(sound_idx+1)
                        panel_disp["status"].text = "Subject is receiving stimuli..."
                        panel_disp["status"].color = self.text_color
                    
                self.draw_visobjs(beam_disp)
                self.draw_visobjs(panel_disp)
                beamer.flip()           
                monitor.flip()               
                
            self.port.reset()
            if self.time_events:
                print("Stimulus duration: "+str(time.perf_counter()-beg_time))
            beam_disp["feedback"].visobj.text = ""
            panel_disp["feedback"].visobj.text = ""
            snd.stop()
            
            beamer.winHandle.activate()
            panel_disp["status"].text = "Subject is rating stimuli..."
            panel_disp["status"].color = self.text_color
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
sound_name_list = ["4000Hz.wav","4000_cheby.wav","4000_fftf.wav","7000Hz.wav"]
#sound_name_list = ["6000Hz.wav","6500Hz.wav","7000Hz.wav","7500Hz.wav"]
hear_keys = ["9","2"] # these correspond to hitting "left" and "right"
ops = [40,20,10,5,2.5]
practice_ops = [15,0,0]
quorum = 2 # must have this many correct/incorrect to reduce/increase volume
jitter_range = (0.8,2)
use_parport = 1
keys = ["2","9"]

play_len = 100
monitor_idx = 0
beamer_idx = 1
aud_schw_len = 0.5
screen_defs = {"monitor":(monitor_idx,(800,600)),"beamer":(beamer_idx,(1280,1024))}

# detemine joint fps
fps = refresh_timer(screen_defs,15,cycles=5)
print(fps)
monitor_fps,beamer_fps,combined_fps=fps[0],fps[1],fps[2]

print("Monitor fps: "+str(monitor_fps))
print("Beamer fps:  "+str(beamer_fps))
print("Combined fps: "+str(combined_fps))

instructA = "Aufmerksamkeit:\nAchte genau auf die Töne (die Augen bleiben auf dem Kreuz).\n\nAufgabe:\nBemerke Schwankungen in der Lautstärke und drücke die Zeigefinger-Taste.\n\n\n\n\nDrücke eine beliebige Taste um fortzufahren."
instructB = "Aufmerksamkeit:\nAchte genau auf das Kreuz, NICHT auf die Töne.\n\nAufgabe:\nBemerke Schwankungen in der Helligkeit und drücke die Zeigefinger-Taste.\n\n\n\nDrücke eine beliebige Taste um fortzufahren."
instructC = "Aufmerksamkeit:\nAchte auf das Kreuz.\n\nAufgabe:\nBemerke Schwankungen in der Helligkeit und drücke die Zeigefinger-Taste.\n\n\n\nDrücke eine beliebige Taste um fortzufahren."
instructD = "Aufmerksamkeit:\nKeine besondere Aufmerksamkeit (nur die Augen bleiben mittig).\n\nAufgabe:\nZähle innerlich rückwärts von 700 (also 699 - 698 - 697 usw.) am Ende sagst Du uns, bei welcher Zahl Du gelandet bist.\n\n\n\nDrücke eine beliebige Taste um fortzufahren."

if use_parport:
    port = parallel.ParallelPort(address="/dev/parport0")
else:
    port = -1

ht = HearTest(sound_name_list,hear_keys,ops,quorum,
             monitor_idx=monitor_idx, beamer_idx=beamer_idx,beamer_fps=beamer_fps,
             monitor_fps=monitor_fps,practice=0)
pt = HearTest(sound_name_list,hear_keys,practice_ops,quorum,
             monitor_idx=monitor_idx, beamer_idx=beamer_idx,monitor_fps=monitor_fps,
             beamer_fps=beamer_fps,practice=1)

htv = HTestVerkehr(ht,pt,over_thresh=55)
sounddata = htv.go()
if sounddata == -1:
    sys.exit()
sounddata = [sounddata] # make it a list so it can be put in other lists without making multiple copies 
params = {}
params["a"]= {"sounddata":sounddata,"audschwank":"audschwank","visschwank":"empty",
               "torespond":"audschwank","keys":keys,"play_len":play_len,"monitor_idx":monitor_idx,
               "beamer_idx":beamer_idx,"name":"Audio modulations only","port":port,
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":10,
                "instruct":instructA,"monitor_fps":monitor_fps,"combined_fps":combined_fps}
params["b"]= {"sounddata":sounddata,"audschwank":"audadd","visschwank":"visselten",
               "keys":keys,"play_len":play_len,"monitor_idx":monitor_idx,"port":port,
               "torespond":"visselten","beamer_idx":beamer_idx,"name":"Infrequent visual modulations, ignore audio",
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":20,
               "schw_or_add":"add","instruct":instructB,"monitor_fps":monitor_fps,
               "combined_fps":combined_fps}
params["c"]= {"sounddata":sounddata,"audschwank":"empty","visschwank":"visschwank",
               "torespond":"visschwank","keys":keys,"play_len":play_len,"monitor_idx":monitor_idx,
               "beamer_idx":beamer_idx,"name":"Visual modulations only","port":port,
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":30,
                "instruct":instructC,"monitor_fps":monitor_fps,"combined_fps":combined_fps}
params["d"]= {"sounddata":sounddata,"audschwank":"empty","visschwank":"empty",
               "torespond":"empty","keys":keys,"play_len":play_len,"monitor_idx":monitor_idx,"port":port,
               "beamer_idx":beamer_idx,"name":"No modulations, count backward.",
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":40,
                "instruct":instructD,"monitor_fps":monitor_fps,"combined_fps":combined_fps}
params["i"]= {"sounddata":sounddata,"audschwank":"audprac","visschwank":"empty",
               "torespond":"audprac","keys":keys,"play_len":15,"monitor_idx":monitor_idx,
               "beamer_idx":beamer_idx,"name":"Practice round: audio","port":port,
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":50,
               "practice":1,"instruct":instructA,"monitor_fps":monitor_fps,
               "combined_fps":combined_fps}
params["j"]= {"sounddata":sounddata,"audschwank":"empty","visschwank":"visprac",
               "torespond":"visprac","keys":keys,"play_len":15,"monitor_idx":monitor_idx,
               "beamer_idx":beamer_idx,"name":"Practice round: visual","port":port,
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":60,
               "practice":1,"instruct":instructC,"monitor_fps":monitor_fps,
               "combined_fps":combined_fps}
          
# handle command line arguments
parser = argparse.ArgumentParser(monitor_idx,beamer_idx,monitor_fps,beamer_fps)
parser.add_argument("--order",type=str,default="abcd")
parser.add_argument("--prac",type=str,default="")
parser.add_argument("--rest", action="store_true")
opt = parser.parse_args()
block_order = list(opt.order)
prac_order = list(opt.prac)
if not all([x in ["a","b","c","d"] for x in block_order]):
    raise ValueError("All blocks must be a,b,c, or d - lowercase.")
if not all([x in ["i","j"] for x in prac_order]):
    raise ValueError("All practice blocks must be i or j - lowercase.")
for p in prac_order:
    blo = Block(**params[p])
    blo.go()
    del blo
if opt.rest:
    blo = RestingState(monitor_idx,beamer_idx,monitor_fps=monitor_fps,
                       beamer_fps=beamer_fps,port=port,length=180)
    blo.go()
results = []
for b in block_order:
    blo = Block(**params[b])
    results += blo.go()
    now = datetime.datetime.now()
    temp_filename = "tempfiles/temp_{d}.{m}.{y}_{block}.txt".format(
            d=now.day,m=now.month,y=now.year,block=b)
    with open(temp_filename,"w") as file:
        file.write("Subject {sub}, recorded on {d}.{m}.{y}, {h}:{mi}\n".format(
          sub=temp_filename[:-4],d=now.day,m=now.month,y=now.year,h=now.hour,mi=now.minute))
        file.write("Index\tBlock\tWavfile\tLaut\tAngenehm\n")
        for res in results:
           file.write("{idx}\t{block}\t{name}\t{laut}\t{angenehm}\n".format(
             idx=res[0],block=res[1],name=res[2],laut=res[3][0],angenehm=res[3][1]))       
    del blo

now = datetime.datetime.now()
filename = filedialog.asksaveasfilename(filetypes=(("Text file","*.txt"),("All files","*.*")))

if filename:
    with open(filename,"w") as file:
        file.write("Subject {sub}, recorded on {d}.{m}.{y}, {h}:{mi}\n".format(
          sub=filename[:-4],d=now.day,m=now.month,y=now.year,h=now.hour,mi=now.minute))
        file.write("Index\tBlock\tWavfile\tLaut\tAngenehm\n")
        for res in results:
           file.write("{idx}\t{block}\t{name}\t{laut}\t{angenehm}\n".format(
             idx=res[0],block=res[1],name=res[2],laut=res[3][0],angenehm=res[3][1]))       
            