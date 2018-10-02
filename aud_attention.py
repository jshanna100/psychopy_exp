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
    rand_idx = (2,0,1,1,0,2,2,1,0)
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
        
class RestingState():
    
    def __init__(self,monitor_idx,beamer_idx,monitor_fps=0,beamer_fps=0,
                 start_trig=255,length=180,back_color=(0.5,0.5,0.5),
                 text_color=(0,0,0)):
        
        self.monitor_idx = monitor_idx
        self.beamer_idx = beamer_idx
        self.monitor_fps = monitor_fps
        self.beamer_fps = beamer_fps
        self.start_trig = start_trig
        self.length = length
        self.back_color = back_color
        self.text_color = text_color
        
    def draw_visobjs(self,visobjs):
        vis_list = list(visobjs.values())
        for vis in vis_list:
            vis.draw()
        
    def go(self):            

        monitor = visual.Window(size=(700,700),color=self.back_color,
                                screen=self.monitor_idx,winType="pyglet")
        
        self.monitor = monitor
        monitor.waitBlanking = False
        beamer = visual.Window(color=self.back_color,screen=self.beamer_idx,
                                       fullscr=False,size=(1280,1024),winType="pyglet")
        self.beamer = beamer
        beamer.waitBlanking = False
        
        if not self.monitor_fps:
            self.monitor_fps = np.round(1/monitor.monitorFramePeriod).astype(int)
        if not self.beamer_fps:  
            self.beamer_fps = np.round(1/beamer.monitorFramePeriod).astype(int)
            
        panel_disp = {}
        panel_disp["title"] = visual.TextStim(win=monitor,text="Resting State",
                  pos=(-0.8,0.8),height=0.07,color=(0,0,0),alignHoriz="left")
        panel_disp["progress"] = visual.TextStim(win=monitor,text="Remaining: ",
          pos=(-0.8,0.65),height=0.09,color=(0,0,0),alignHoriz="left")
        
        beam_disp = {}
        beam_disp["fixation"] = VisObj(visual.TextStim(win=beamer,text="X",
                 height=0.15,color=(0,0,0)))
        
        for s_idx in range(self.length):
            panel_disp["progress"].text = "Remaining: "+ str(self.length-s_idx)
            for f_idx in range(self.beamer_fps):
                self.draw_visobjs(panel_disp)
                self.draw_visobjs(beam_disp)
                monitor.flip()
                beamer.flip()


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
                 monitor_idx,beamer_idx,name="Experiment",monitor_fps=0,beamer_fps=0,
                 instruct="Instructions",aud_schw_len=0.5,vis_schw_len=0.5,
                 aud_trig=100,vis_trig=200,port=0,schw_or_add="schwank",id_trig=1,
                 practice=0,stim_start_trig=50,resp_len=1,back_color=(0.5,0.5,0.5)):
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
        monitor = visual.Window(size=(700,700),color=self.back_color,
                                screen=self.monitor_idx,winType="pyglet")
        
        self.monitor = monitor
        monitor.waitBlanking = False
        beamer = visual.Window(color=self.back_color,screen=self.beamer_idx,
                                       fullscr=False,size=(1280,1024),winType="pyglet")
        self.beamer = beamer
        beamer.waitBlanking = False
            
        if not self.monitor_fps:
            self.monitor_fps = np.round(1/monitor.monitorFramePeriod).astype(int)
        if not self.beamer_fps:  
            self.beamer_fps = np.round(1/beamer.monitorFramePeriod).astype(int)
        
        print("Monitor fps: " + str(self.monitor_fps))
        print("Beamer fps: " + str(self.beamer_fps))
             
        # build the display objects
        
        instruct_disp = {}
        instruct_disp["instruct"] = visual.TextStim(win=beamer,text=self.instruct,color=(0,0,0),
                  pos=(0,0),height=0.1,wrapWidth=1.8)
  
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
        
        beam_disp = {}
        beam_disp["fixation"] = VisObj(visual.TextStim(win=beamer,text="X",
                 height=0.15,color=(0,0,0)))
        beam_disp["feedback"] = VisObj(visual.TextStim(win=beamer, text="",color=(0,0,0),
                 pos=(0,0.3),height=0.15))  
        
        # set up rating bars
        down_butts = [key._2]
        up_butts = [key._3]
        conf_ud_butts = [key._5]
        left_butts = [key._8]
        right_butts = [key._9]
        conf_lr_butts = [key._6]
        
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
            # load Schwankungen
            aschw = np.round(self.audschwank[keys[sound_idx]]*self.beamer_fps*1e-3).astype(int)
            vschw = np.round(self.visschwank[keys[sound_idx]]*self.beamer_fps*1e-3).astype(int)
            toresp = np.round(self.torespond[keys[sound_idx]]*self.beamer_fps*1e-3).astype(int)
            
            # send trigger, offset of which indicates start of sound
            self.port.set_val(sound_idx+1)
            snd.play()
            
            # run modulations
            vis_check = 0
            aud_check = 0
            resp_check = 0
            ans_timer = 0
            event.clearEvents()
            for f in range(self.play_len*self.beamer_fps):
                if f in aschw:
                    aud_check = int(self.beamer_fps*self.aud_schw_len)
                    panel_disp["status"].text = "AUDITORY MODULATION"
                    panel_disp["status"].color = (1,0,0)
                    beamer.callOnFlip(self.port.set_val,self.aud_trig)
                if f in vschw:
                    beam_disp["fixation"].color = col_anim((0,0,0),(0.25,0.25,0.25),self.beamer_fps//4) + \
                      col_anim((0.25,0.25,0.25),(0,0,0),self.beamer_fps//4)
                    vis_check = int(self.beamer_fps*self.vis_schw_len)
                    beamer.callOnFlip(self.port.set_val,self.vis_trig)
                    panel_disp["status"].text = "VISUAL MODULATION"
                    panel_disp["status"].color = (1,0,0)
                if f in toresp :
                    resp_check = int(self.beamer_fps*self.resp_len)
                    event.clearEvents()
                        
                if vis_check:
                    vis_check -= 1
                if aud_check:
                    aud_check -= 1
                if resp_check:
                    if event.getKeys(["0","1","2","3","4","5","6","7","8","9"]):
                        panel_disp["status"].text = "Subject responded correctly."
                        panel_disp["status"].color = [0,1,0]
                        ans_timer = self.beamer_fps*2
                        if self.practice:
                            beam_disp["feedback"].visobj.text = "Treffer!"
                            beam_disp["feedback"].color = col_anim(self.back_color,(0,1,0),self.beamer_fps) + \
                              col_anim((0,1,0),self.back_color,self.beamer_fps)
                    resp_check -= 1
                else:
                    if event.getKeys(["0","1","2","3","4","5","6","7","8","9"]):
                        panel_disp["status"].text = "Subject responded falsely."
                        panel_disp["status"].color = [1,0,0]
                        ans_timer = self.beamer_fps*2
                        if self.practice:
                                beam_disp["feedback"].visobj.text = "Falsch!"
                                beam_disp["feedback"].color = col_anim(self.back_color,(1,0,0),self.beamer_fps) + \
                                      col_anim((1,0,0),self.back_color,self.beamer_fps)
                if ans_timer:
                    ans_timer -=1
                               
                if not vis_check and not aud_check and not ans_timer:
                    if self.port:
                        self.port.reset()
                    panel_disp["status"].text = "Subject is receiving stimuli..."
                    panel_disp["status"].color = (0,0,0)
                    
                self.draw_visobjs(beam_disp)
                self.beamer.flip()
                self.draw_visobjs(panel_disp)           
                self.monitor.flip()

            self.port.reset()
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
hear_keys = ["9","2"] # these correspond to hitting "left" and "right"
ops = [40,20,10,5,2.5]
practice_ops = [15,0,0]
quorum = 2 # must have this many correct/incorrect to reduce/increase volume
jitter_range = (0.8,2)
use_parport = 0
keys = ["2","9"]
beamer_fps = 60
monitor_fps = 60
play_len = 50
monitor_idx = 1
beamer_idx = 0
aud_schw_len = 0.5


instructA = "Aufmerksamkeit: achte genau auf die Töne (die Augen bleiben auf dem Kreuz).\n\nAufgabe: bemerke Schwankungen in der Lautstärke und drücke die Zeigefinger-Taste."
instructB = "Aufmerksamkeit: achte genau auf das Kreuz, NICHT auf die Töne.\n\nAufgabe: bemerke Schwankungen in der Helligkeit und drücke die Zeigefinger-Taste."
instructC = "Aufmerksamkeit: achte auf das Kreuz.\n\nAufgabe: bemerke Schwankungen in der Helligkeit und drücke die Zeigefinger-Taste."
instructD = "Aufmerksamkeit: keine besondere Aufmerksamkeit (nur die Augen bleiben mittig).\n\nAufgabe: zähle innerlich rückwärts von 700 (also 699 - 698 - 697 usw.) am Ende sagst Du uns, bei welcher Zahl Du gelandet bist."

if use_parport:
    port = parallel.ParallelPort(address="/dev/parport0")
else:
    port = -1

ht = HearTest(sound_name_list,hear_keys,ops,quorum,
             monitor_idx=1, beamer_idx=0,practice=0)
pt = HearTest(sound_name_list,hear_keys,practice_ops,quorum,
             monitor_idx=1, beamer_idx=0,practice=1)

htv = HTestVerkehr(ht,pt,over_thresh=40)
sounddata = [htv.go()] # make it a list so it can be put in other lists without making multiple copies 
params = {}
params["a"]= {"sounddata":sounddata,"audschwank":"audschwank","visschwank":"empty",
               "torespond":"audschwank","keys":keys,"play_len":play_len,"monitor_idx":monitor_idx,
               "beamer_idx":beamer_idx,"name":"Audio modulations only","port":port,
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":10,
                "instruct":instructA}
params["b"]= {"sounddata":sounddata,"audschwank":"audadd","visschwank":"visselten",
               "keys":keys,"play_len":play_len,"monitor_idx":monitor_idx,"port":port,
               "torespond":"visselten","beamer_idx":beamer_idx,"name":"Infrequent visual modulations, ignore audio",
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":20,
               "schw_or_add":"add","instruct":instructB}
params["c"]= {"sounddata":sounddata,"audschwank":"empty","visschwank":"visschwank",
               "torespond":"visschwank","keys":keys,"play_len":play_len,"monitor_idx":monitor_idx,
               "beamer_idx":beamer_idx,"name":"Visual modulations only","port":port,
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":30,
                "instruct":instructC}
params["d"]= {"sounddata":sounddata,"audschwank":"empty","visschwank":"empty",
               "torespond":"empty","keys":keys,"play_len":play_len,"monitor_idx":monitor_idx,"port":port,
               "beamer_idx":beamer_idx,"name":"No modulations, count backward.",
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":40,
                "instruct":instructD}
params["i"]= {"sounddata":sounddata,"audschwank":"audprac","visschwank":"empty",
               "torespond":"audprac","keys":keys,"play_len":15,"monitor_idx":monitor_idx,
               "beamer_idx":beamer_idx,"name":"Practice round: audio","port":port,
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":50,
               "practice":1,"instruct":instructA}
params["j"]= {"sounddata":sounddata,"audschwank":"empty","visschwank":"visprac",
               "torespond":"visprac","keys":keys,"play_len":15,"monitor_idx":monitor_idx,
               "beamer_idx":beamer_idx,"name":"Practice round: visual","port":port,
               "beamer_fps":beamer_fps,"aud_schw_len":aud_schw_len,"id_trig":60,
               "practice":1,"instruct":instructC}
          
# handle command line arguments
parser = argparse.ArgumentParser(monitor_idx,beamer_idx,monitor_fps,beamer_fps,
                                 )
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
if opt.rest:
    blo = RestingState(monitor_idx,beamer_idx,monitor_fps=monitor_fps,
                       beamer_fps=beamer_fps)
    blo.go()
for p in prac_order:
    blo = Block(**params[p])
    blo.go()
    del blo
results = []
for b in block_order:
    blo = Block(**params[b])
    results += blo.go()
    del blo

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
            
            
            
        
        
