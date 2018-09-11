from scipy.io import wavfile
import numpy as np
from psychopy import visual, prefs, event, core
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound
import datetime
from tkinter import filedialog
from tkinter import Tk,Button,mainloop
import csv

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
        
class SoundWrap():
    # class contains sound, sound info, and information required for performing iterative operations on them
    def __init__(self,name,data,operation,ops):
        self.name = name # file name of wav
        self.data = data # wav data in numpy format
        self.operation = operation # operation to perform on data
        self.ops = ops # which arguments to pass to the operation
    def operate(self,side_idx,**kwargs):
        self.data[:,side_idx] = self.operation(self.data[:,side_idx],**kwargs)
    
def audio_load(sound_name):
    nptypes = {np.dtype("int16"):32768,np.dtype("int32"):2147483648}
    fs,data = wavfile.read(sound_name)
    aud_res = nptypes[data.dtype]
    if len(data.shape)==1:
        data = (np.tile(data,(2,1))/aud_res).T
    # 0 values to infinitesimal values for dB log calculations
    data[data==0]=0.00000001
    return data

def dec2dcb(dec):
    return 20*np.log10(np.abs(dec))

def dcb2dec(dcb):
    return 10**(dcb/20)

def incr_dcb(data,dcb_delta=0,direction=-1):
    # if direction is 1, increase by requested decibels, if -1 decrease by same amount
    dcb = dec2dcb(np.abs(data))
    if direction==1:
        newdcb = dcb + dcb_delta
    elif direction==-1:
        newdcb = dcb - dcb_delta
    newdcb[newdcb<-160]=-160
    return dcb2dec(newdcb)*np.sign(data)
    

def col_anim(beg,end,steps):
    col_list = []
    for col_idx in range(3):
        col_list.append(list(np.linspace(beg[col_idx],end[col_idx],steps)))
    return list(zip(*col_list))
    
def pos_anim(beg,end,steps):
    pos_list = []
    for pos_idx in range(2):
        pos_list.append(list(np.linspace(beg[pos_idx],end[pos_idx],steps)))
    return list(zip(*pos_list))
            
class HearTest():    

    def __init__(self,sound_name_list,key_presses,ops,quorum,
      play_duration=2, jitter_range=(0.5,2), practice=0,
      monitor_idx=0,beamer_idx=np.nan,monitor_fps=None,beamer_fps=None,
      back_color=(0.5,0.5,0.5),beamsize=(1280,1024),monsize=(700,700)):
        
        self.sound_name_list = sound_name_list
        self.key_presses = key_presses
        self.ops = ops
        self.quorum = quorum
        self.play_duration = play_duration
        self.jitter_range = jitter_range
        self.practice = practice
        self.monitor_idx = monitor_idx
        self.beamer_idx = beamer_idx
        self.monitor_fps = monitor_fps
        self.beamer_fps = beamer_fps
        self.back_color = back_color
        self.monsize = monsize
        self.beamsize = beamsize
    
    def draw_visobjs(self,visobjs):
        vis_list = list(visobjs.values())
        for vis in vis_list:
            vis.draw()
    
    def go(self):
        
        sound_name_list= self.sound_name_list
        key_presses= self.key_presses
        ops = self.ops
        quorum = self.quorum
        play_duration = self.play_duration
        jitter_range = self.jitter_range
        practice = self.practice
        monitor_idx = self.monitor_idx
        beamer_idx = self.beamer_idx
        monitor_fps = self.monitor_fps
        beamer_fps = self.beamer_fps
        back_color = self.back_color
             
        thresh_results = []
        abort = 0
        
        # set up the monitors
        beamer = None
        monitor = visual.Window(size=self.monsize,color=back_color,
                                screen=monitor_idx,winType="pyglet")
        if not monitor_fps:
            monitor_fps = 1/monitor.monitorFramePeriod
        if not np.isnan(beamer_idx):    
            beamer = visual.Window(size=self.beamsize,color=back_color,screen=beamer_idx,
                                   winType="pyglet")
            if not beamer_fps:
                beamer_fps = 1/beamer.monitorFramePeriod
        
        visobjs = {}
        beamobjs = {}
        # set up the complex of visual objects
    
        # text
        visobjs["tonepress_label"] = visual.TextStim(win=monitor,text="Sound/Press",pos=(-0.9,0.9),height=0.07,color=(0,0,0),alignHoriz="left")
        visobjs["tonepress_l"] = visual.TextStim(win=monitor,text="L",pos=(-0.8,0.8),height=0.1,color=(0,0,0))
        visobjs["tonepress_r"] = visual.TextStim(win=monitor,text="R",pos=(-0.7,0.8),height=0.1,color=(0,0,0))
        visobjs["tonelabel"] = visual.TextStim(win=monitor,text="S",pos=(-0.9,0.7),height=0.1,color=(0,0,0))
        visobjs["presslabel"] = visual.TextStim(win=monitor,text="P",pos=(-0.9,0.6),height=0.1,color=(0,0,0))
        visobjs["acclabel"] = visual.TextStim(win=monitor,text="Accuracy",pos=(-0.9,0.4),height=0.07,color=(0,0,0),alignHoriz="left")
        visobjs["acclabel_l"] = visual.TextStim(win=monitor,text="L",pos=(-0.9,0.3),height=0.1,color=(0,0,0))
        visobjs["acclabel_r"] = visual.TextStim(win=monitor,text="R",pos=(-0.9,0.15),height=0.1,color=(0,0,0))
        visobjs["filename"] = visual.TextStim(win=monitor,text="",pos=(-0.95,-0.1),height=0.06,color=(0,0,0),alignHoriz="left")
        visobjs["progress"] = visual.TextStim(win=monitor,text="",pos=(-0.95,-0.2),height=0.06,color=(0,0,0),alignHoriz="left")
        visobjs["mode"] = visual.TextStim(win=monitor,text="Normal Mode",pos=(-0.95,-0.5),height=0.08,color=(0,0,0),alignHoriz="left")
        visobjs["status"] = visual.TextStim(win=monitor,text="Running",pos=(0.05,-0.5),height=0.08,color=(0,0,0),alignHoriz="left")
        visobjs["message"] = visual.TextStim(win=monitor,text="press p to pause, a to abort",pos=(-0.95,-0.8),height=0.06,color=(0,0,0),alignHoriz="left")
    
        if practice:
            visobjs["mode"].text = "Practice"
            visobjs["mode"].color = (1,0,0)
        
        if beamer is not None:
            beamobjs["befehl"] = visual.TextStim(win=beamer,
                   text="Drücke sofort RECHTS bei einem Ton im rechten Ohr.\n\n\nDrücke sofort LINKS bei einem Ton im linken Ohr.",
                   pos=(0,0),height=0.07,color=(0,0,0))
            beamobjs["bericht"] = VisObj(visual.TextStim(win=beamer,text="",pos=(0,0),
                    height=0.1,color=back_color))
            self.draw_visobjs(beamobjs)
            beamer.flip()
        
        # tone/press squares
        visobjs["lefttone"] = VisObj(visual.Rect(
          win=monitor,units="norm",width=0.1,height=0.1,pos=(-0.8,0.7),lineColor=[0,0,0]))
        visobjs["righttone"] = VisObj(visual.Rect(
          win=monitor,units="norm",width=0.1,height=0.1,pos=(-0.7,0.7),lineColor=[0,0,0]))
        visobjs["leftpress"] = VisObj(visual.Rect(
          win=monitor,units="norm",width=0.1,height=0.1,pos=(-0.8,0.6),lineColor=[0,0,0]))
        visobjs["rightpress"] = VisObj(visual.Rect(
          win=monitor,units="norm",width=0.1,height=0.1,pos=(-0.7,0.6),lineColor=[0,0,0]))
    
        # accuracy squares
        acc_pane_names = [[],[]]
        for s_idx,s in enumerate(zip(["left","right"],[0.3,0.15])):
            for p_idx in range(quorum):
                acc_pane_names[s_idx].append(s[0]+"acc"+str(p_idx))
                visobjs[acc_pane_names[s_idx][-1]]=VisObj(visual.Rect(
                  win=monitor,units="norm",width=0.1,height=0.1,pos=(-0.8+(p_idx*0.1),s[1]),
                  lineColor=(0,0,0),fillColor=back_color))
    
        # threshold chart
        thresh_height_cent = 0.25
        thresh_width_cent = 0.3
        thresh_height = 1
        thresh_width = 0.7
        thresh_height_min = thresh_height_cent-thresh_height/2
        visobjs["thresh_back"] = VisObj(visual.Rect(
          win=monitor,units="norm",width=thresh_width,height=thresh_height,pos=(thresh_width_cent,thresh_height_cent),
          lineColor=[0,0,0],fillColor=(1,1,1)))
        visobjs["thresh_left"] = VisObj(visual.Rect(
          win=monitor,units="norm",width=thresh_width/4,height=0.08,pos=(thresh_width_cent-thresh_width/4,thresh_height_cent),
          lineColor=[0,0,0],fillColor=(0,0,1)))
        visobjs["thresh_right"] = VisObj(visual.Rect(
          win=monitor,units="norm",width=thresh_width/4,height=0.08,pos=(thresh_width_cent+thresh_width/4,thresh_height_cent),
          lineColor=[0,0,0],fillColor=(0,0,1)))
    
        visobjs["thresh_label"] = visual.TextStim(win=monitor,text="Hearing Threshold",pos=(0.3,0.9),height=0.07,color=(0,0,0))
        visobjs["thresh_label_l"] = visual.TextStim(win=monitor,text="L",pos=(thresh_width_cent-thresh_width/4,0.8),height=0.1,color=(0,0,0))
        visobjs["thresh_label_r"] = visual.TextStim(win=monitor,text="R",pos=(thresh_width_cent+thresh_width/4,0.8),height=0.1,color=(0,0,0))
        visobjs["thresh_label_dB"] = visual.TextStim(win=monitor,text="dB",pos=(thresh_width_cent-thresh_width/2-0.13,thresh_height_cent),height=0.1,color=(0,0,0))
        visobjs["thresh_label_max"] = visual.TextStim(win=monitor,text="0",pos=(thresh_width_cent-thresh_width/2-0.13,thresh_height_cent+thresh_height/2),height=0.1,color=(0,0,0))
        visobjs["thresh_label_min"] = visual.TextStim(win=monitor,text="-160",pos=(thresh_width_cent-thresh_width/2-0.13,thresh_height_cent-thresh_height/2),height=0.1,color=(0,0,0))
        
        # for every file name,convert to stereo, 
        # and normalise to [-1,1] range, build the SoundWrap objects
        sound_list = []
        for sound_name in sound_name_list:
            snd = audio_load(sound_name)
            sound_list.append(SoundWrap(sound_name,snd,incr_dcb,[ops.copy(),ops.copy()]))
    
        # randomise order of sounds
        reihenfolge = np.array(range(len(sound_name_list)))
        np.random.shuffle(reihenfolge)
        runde = np.concatenate((np.zeros(quorum),np.ones(quorum))).astype(np.int)
        # cycle through sounds randomly
        for abs_idx,sound_idx in enumerate(np.nditer(reihenfolge)):
            swr = sound_list[sound_idx]
            visobjs["filename"].text=sound_name_list[sound_idx]
            visobjs["progress"].text = "File: "+str(abs_idx+1)+" of "+str(len(sound_name_list))
            # already do a reduction before we begin
            swr.operate(0,dcb_delta=swr.ops[0].pop(0),direction=-1)
            swr.operate(1,dcb_delta=swr.ops[1].pop(0),direction=-1)
            ear_thresh = dec2dcb((np.max(swr.data[:,0]),np.max(swr.data[:,1])))
            visobjs["thresh_left"].pos = pos_anim(visobjs["thresh_left"].visobj.pos,(visobjs["thresh_left"].visobj.pos[0],
              thresh_height_min+thresh_height*(-160-ear_thresh[0])/-160),int(monitor_fps*0.5))
            visobjs["thresh_right"].pos = pos_anim(visobjs["thresh_right"].visobj.pos,(visobjs["thresh_right"].visobj.pos[0],
              thresh_height_min+thresh_height*(-160-ear_thresh[1])/-160),int(monitor_fps*0.5))
            # do until ops are exhausted in both ears
            while swr.ops[0] or swr.ops[1]:
                # make versions with sound only in left or right
                sounds = []
                for s_idx in range(quorum):
                    d = swr.data.copy()
                    d[:,1-s_idx] = 0
                    sounds.append(sound.Sound(d))
                # present to each ear twice in random order, record accuracy
                np.random.shuffle(runde)
                accs = [[],[]]
                for r_idx,r in enumerate(np.nditer(runde)):
                    # play sound and update tone squares
                    sounds[r].play()
                    if r:
                        visobjs["righttone"].visobj.fillColor=(0,1,0)
                    else:
                        visobjs["lefttone"].visobj.fillColor=(0,1,0)
                    
                    for f_idx in range(int(monitor_fps*play_duration)):
                        response = event.getKeys(key_presses)
                        # update press squares
                        self.draw_visobjs(visobjs)
                        monitor.flip()
                        if response:
                            break
                            
                    # turn off sound and update tone squares
                    sounds[r].stop()
                    anim_pattern = col_anim((0,1,0),(0,1,0),int(monitor_fps*0.15)) + \
                      col_anim((0,1,0),back_color,int(monitor_fps*0.3))
                    if r:
                        visobjs["righttone"].fillColor= anim_pattern.copy()
                    else:
                        visobjs["lefttone"].fillColor= anim_pattern.copy()
                    
                    # mark accuracy, update press squares
                    if key_presses[r] in response and key_presses[1-r] not in response:
                        accs[r].append(1)
                        anim_pattern = col_anim(back_color,(0,1,0),int(monitor_fps*0.15)) + \
                          col_anim((0,1,0),back_color,int(monitor_fps*0.3))
                        if r:
                            visobjs["rightpress"].fillColor=anim_pattern.copy()
                        else:
                            visobjs["leftpress"].fillColor=anim_pattern.copy()
                        if practice and not np.isnan(beamer_idx):
                            beamobjs["bericht"].visobj.text="Richtig!"
                            beamobjs["bericht"].color = col_anim(back_color,(0,1,0),beamer_fps*0.35) + \
                              col_anim((0,1,0),back_color,beamer_fps*0.35)
                            
                    elif key_presses[1-r] in response:
                        accs[r].append(0)
                        anim_pattern = col_anim(back_color,(1,0,0),int(monitor_fps*0.15)) + \
                          col_anim((1,0,0),back_color,int(monitor_fps*0.3))
                        if r:
                            visobjs["leftpress"].fillColor=anim_pattern.copy()
                        else:
                            visobjs["rightpress"].fillColor=anim_pattern.copy()
                        if practice and not np.isnan(beamer_idx):
                            beamobjs["bericht"].visobj.text="Falsch!"
                            beamobjs["bericht"].color = col_anim(back_color,(1,0,0),beamer_fps*0.35) + \
                              col_anim((1,0,0),back_color,beamer_fps*0.35)
                    else:
                        accs[r].append(0)
                        if practice and not np.isnan(beamer_idx):
                            beamobjs["bericht"].visobj.text="Verpasst!"
                            beamobjs["bericht"].color = col_anim(back_color,(1,0,0),beamer_fps*0.35) + \
                              col_anim((1,0,0),back_color,beamer_fps*0.35)
                    
                    # update acc squares
                    if accs[r][-1]:
                        anim_pattern = col_anim(back_color,(0,1,0),monitor_fps*0.2)
                    else:
                        anim_pattern = col_anim(back_color,(1,0,0),monitor_fps*0.2)
                    visobjs[acc_pane_names[r][len(accs[r])-1]].fillColor=anim_pattern.copy()
                                        
                    # ISI
                    jitter = jitter_range[0]+np.random.rand()*(jitter_range[1]-jitter_range[0])
                    for f_idx in range(int(monitor_fps*jitter)):
                        self.draw_visobjs(visobjs)
                        if not np.isnan(beamer_idx):
                            self.draw_visobjs(beamobjs)
                            beamer.flip()
                        monitor.flip()
                    if "p" in event.getKeys(["p"]):
                        visobjs["status"].text = "Paused"
                        visobjs["status"].color = (1,0,0)
                        visobjs["message"].text = "press p again to resume"
                        self.draw_visobjs(visobjs)
                        monitor.flip()
                        event.waitKeys(keyList=["p"])
                        visobjs["status"].text = "Running"
                        visobjs["status"].color = (0,0,0)
                        visobjs["message"].text = "press p to pause, a to abort"
                        self.draw_visobjs(visobjs)
                        monitor.flip
                    if "a" in event.getKeys(["a"]):
                        abort += 1
                        if abort == 1:
                            visobjs["message"].text = "press a again to abort, n to cancel"
                            visobjs["message"].color = (1,0,0)
                        if abort == 2:
                            monitor.close()
                            return ([],0)
                    if abort == 1 and "n" in event.getKeys(["n"]):
                        abort = 0
                        visobjs["message"].text = "press p to pause, a to abort"
                        visobjs["message"].color = (0,0,0)
                    event.clearEvents()
                
                # assess accuracy and act accordingly
                accs = np.array(accs)
                for r_idx in range(accs.shape[0]):
                    line_flash = col_anim((0,0,0),(1,1,1),monitor_fps*0.2) + col_anim((1,1,1),(0,0,0),monitor_fps*0.4)
                    green_flash = col_anim((0,1,0),(1,1,1),monitor_fps*0.2) + col_anim((1,1,1),back_color,monitor_fps*0.4)
                    red_flash = col_anim((1,0,0),(1,1,1),monitor_fps*0.2) + col_anim((1,1,1),back_color,monitor_fps*0.4)
                    if accs[r_idx,].all() and swr.ops[r_idx]: # all correct, decrease volume, flash squares
                        swr.operate(r_idx,dcb_delta=swr.ops[r_idx].pop(0),direction=-1)
                        for accp in acc_pane_names[r_idx]:
                            visobjs[accp].fillColor = green_flash
                            visobjs[accp].lineColor = line_flash
                    elif not accs[r_idx,].any() and swr.ops[r_idx]: # all false, increase
                        swr.operate(r_idx,dcb_delta=swr.ops[r_idx].pop(0),direction=1)
                        for accp in acc_pane_names[r_idx]:
                            visobjs[accp].fillColor = red_flash
                            visobjs[accp].lineColor = line_flash
                    else: # ambiguous result, just clear acc squares
                        for accp in acc_pane_names[r_idx]:
                            visobjs[accp].fillColor = col_anim(
                            visobjs[accp].visobj.fillColor,back_color,monitor_fps*0.4) 
                    # update threshold chart
                    ear_thresh = dec2dcb((np.max(swr.data[:,0]),np.max(swr.data[:,1])))
                    visobjs["thresh_left"].pos = pos_anim(visobjs["thresh_left"].visobj.pos,(visobjs["thresh_left"].visobj.pos[0],
                      thresh_height_min+thresh_height*(-160-ear_thresh[0])/-160),int(monitor_fps*0.5))
                    visobjs["thresh_right"].pos = pos_anim(visobjs["thresh_right"].visobj.pos,(visobjs["thresh_right"].visobj.pos[0],
                      thresh_height_min+thresh_height*(-160-ear_thresh[1])/-160),int(monitor_fps*0.5))
            # store threshold for item
            thresh_results.append([sound_idx,swr.name,ear_thresh[0],ear_thresh[1]])
            for f_idx in range(int(monitor_fps*0.35)):
                self.draw_visobjs(visobjs)
                monitor.flip()
            
        # write to file
        if not practice:
            now = datetime.datetime.now()
            Tk().withdraw()
            filename = filedialog.asksaveasfilename(filetypes=(("Hearing test files","*.hrt"),("All files","*.*")))
                
            if filename:
                with open(filename,"w") as file:
                    file.write("Subject {sub}, recorded on {d}.{m}.{y}, {h}:{mi}\n".format(
                      sub="test",d=now.day,m=now.month,y=now.year,h=now.hour,mi=now.minute))
                    file.write("Index\tWavfile\tLeftEar\tRightEar\n")
                    for thrsh in thresh_results:
                        file.write("{idx}\t{name}\t{right}\t{left}\n".format(
                          idx=thrsh[0],name=thrsh[1],right=thrsh[2],left=thrsh[3]))       

        monitor.close()
        if not np.isnan(beamer_idx):
            beamer.close()
        return thresh_results

class HTestVerkehr():    
    def __init__(self,HTest,PracTest,over_thresh=55):
        self.HTest = HTest
        self.PracTest = PracTest
        self.Threshs = [[s_idx, s, "0", "0"] for s_idx,s in enumerate(HTest.sound_name_list)]        
        self.over_thresh = over_thresh   
        self.quit = 0
    def HTest_callback(self):
        self.Threshs = self.HTest.go()
#        self.master.destroy()
#        self.master_init()
    def PTest_callback(self):
        self.PracTest.go()
    def LoadThresh_callback(self):
        filename = filedialog.askopenfilename(filetypes=(("Hearing test files","*.hrt"),("All files","*.*")))
        with open(filename,"r") as tsv:
            reader = csv.reader(tsv,delimiter="\t")
            thresh_results = [x for x in reader][2:]
        self.Threshs = thresh_results
    def Proceed_callback(self):
        self.quit = 1
    def master_init(self):
        self.master = Tk()
        ht_butt = Button(self.master,text="Hearing Test",command=self.HTest_callback,height=12, width=12)
        pt_butt = Button(self.master,text="Practice",command=self.PTest_callback,height=12, width=12)
        lt_butt = Button(self.master,text="Load thresholds",command=self.LoadThresh_callback,height=12, width=12)
        quit_butt = Button(self.master,text="Proceed",command=self.Proceed_callback,height=12, width=12)
        ht_butt.pack(side="left")
        pt_butt.pack(side="left")
        lt_butt.pack(side="left")
        quit_butt.pack(side="left")
        self.master.title("Hearing Test")
    
    def go(self):
        self.master_init()
        while not self.quit:
            self.master.update()
        self.master.destroy()
            
        sounds = {}
        for snd in self.Threshs:
            data = audio_load(snd[1])
            for i_idx in range(2):
                incr = 0 if float(snd[2+i_idx])+self.over_thresh > 0 else float(snd[2+i_idx])+self.over_thresh
                data[:,i_idx] = incr_dcb(data[:,i_idx],dcb_delta=incr,direction=1)
            sounds[snd[1]] = data.copy(order="C")
        return sounds
        
        
        
        
        
        
       
        