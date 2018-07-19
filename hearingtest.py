from scipy.io import wavfile
import numpy as np
from psychopy import core, visual, prefs, event
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound
import datetime
from tkinter import filedialog
from tkinter import Tk

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
        self.visobj.draw()
        

class SoundWrap():
    # class contains sound, sound info, and information required for performing iterative operations on them
    def __init__(self,name,data,operation,ops,aud_res):
        self.name = name # file name of wav
        self.data = data # wav data in numpy format
        self.operation = operation # operation to perform on data
        self.aud_res = aud_res # resolution of wav file
        self.ops = ops # which arguments to pass to the operation
    def operate(self,side_idx,**kwargs):
        self.data[:,side_idx] = self.operation(self.data[:,side_idx],**kwargs)

def draw_visobjs(visobjs):
    vis_list = list(visobjs.values())
    for vis in vis_list:
        vis.draw()

def dec2dcb(dec):
    return 20*np.log10(np.abs(dec))

def dcb2dec(dcb):
    return 10**(dcb/20)

def incr_dcb(data,dcb_delta=0,direction=-1):
    # if direction is 1, increase by requested decibels, if -1 decrease by same amount
    dcb = dec2dcb(np.abs(data))
    #print("Before: max: {} min: {}".format(np.max(dcb),np.min(dcb)))
    if direction==1:
        newdcb = dcb + dcb_delta
    elif direction==-1:
        newdcb = dcb - dcb_delta
    newdcb[newdcb<-160]=-160
    #print("After: max: {} min: {}".format(np.max(newdcb),np.min(newdcb)))
    return dcb2dec(newdcb)*np.sign(data)
    

def col_anim(beg,end,steps):
    col_list = []
    for col_idx in range(3):
        col_list.append(list(np.linspace(beg[col_idx],end[col_idx],steps)))
    return list(zip(*col_list))


# arbitrary parameters
sound_name_list = ["4000Hz.wav","4000_cheby.wav"]
thresh_results = []
key_presses = ["3","4"] # these correspond to hitting "left" and "right"
runde = np.array([0,0,1,1])
ops = [3.25,7.5,15,30,60]
monsize = (700,700)
back_color = (0.5,0.5,0.5)
quorum = 2 # must have this many correct to reduce volume

# set up the monitor
monitor = visual.Window(size=monsize,color=back_color)
monitor_fps = monitor.getActualFrameRate()

visobjs = {}

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


# for every file name,convert to stereo, 
# and normalise to [-1,1] range, build the SoundWrap objects
sound_list = []
for sound_name in sound_name_list:
    nptypes = {np.dtype("int16"):32768,np.dtype("int32"):2147483648}
    fs,sig = wavfile.read(sound_name)
    aud_res = nptypes[sig.dtype]
    data = (np.tile(sig,(2,1))/aud_res).T
    # 0 values to infinitesimal values for dB log calculations
    data[data==0]=0.00000001
    sound_list.append(SoundWrap(sound_name,data,incr_dcb,[ops.copy(),ops.copy()],aud_res))


# randomise order of sounds
reihenfolge = np.array(range(len(sound_name_list)))
np.random.shuffle(reihenfolge)
# cycle through random sounds
for sound_idx in np.nditer(reihenfolge):
    swr = sound_list[sound_idx]
    # already do a reduction before we begin
    swr.operate(0,dcb_delta=swr.ops[0].pop(),direction=-1)
    swr.operate(1,dcb_delta=swr.ops[1].pop(),direction=-1) 
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
            
            for f_idx in range(int(monitor_fps*3)):
                response = event.getKeys(key_presses)
                # update press squares
                draw_visobjs(visobjs)
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
            elif key_presses[1-r] in response:
                accs[r].append(0)
                anim_pattern = col_anim(back_color,(1,0,0),int(monitor_fps*0.15)) + \
                  col_anim((1,0,0),back_color,int(monitor_fps*0.3))
                if r:
                    visobjs["leftpress"].fillColor=anim_pattern.copy()
                else:
                    visobjs["rightpress"].fillColor=anim_pattern.copy()
            else:
                accs[r].append(0)
            
            # update acc squares
            if accs[r][-1]:
                anim_pattern = col_anim(back_color,(0,1,0),monitor_fps*0.2)
            else:
                anim_pattern = col_anim(back_color,(1,0,0),monitor_fps*0.2)
            visobjs[acc_pane_names[r][len(accs[r])-1]].fillColor=anim_pattern.copy()
                
                
            # ISI
            for f_idx in range(int(monitor_fps*0.5)):
                draw_visobjs(visobjs)
                monitor.flip()
            event.clearEvents()
        
        # assess accuracy and act accordingly
        accs = np.array(accs)
        for r_idx in range(accs.shape[0]):
            line_flash = col_anim((0,0,0),(1,1,1),monitor_fps*0.2) + col_anim((1,1,1),(0,0,0),monitor_fps*0.4)
            green_flash = col_anim((0,1,0),(1,1,1),monitor_fps*0.2) + col_anim((1,1,1),back_color,monitor_fps*0.4)
            red_flash = col_anim((1,0,0),(1,1,1),monitor_fps*0.2) + col_anim((1,1,1),back_color,monitor_fps*0.4)
            if accs[r_idx,].all() and swr.ops[r_idx]: # all correct, decrease volume, flash squares, update thresh chart
                swr.operate(r_idx,dcb_delta=swr.ops[r_idx].pop(),direction=-1)
                for accp in acc_pane_names[r_idx]:
                    visobjs[accp].fillColor = green_flash
                    visobjs[accp].lineColor = line_flash
            elif not accs[r_idx,].any() and swr.ops[r_idx]: # all false, increase
                swr.operate(r_idx,dcb_delta=swr.ops[r_idx].pop(),direction=1)
                for accp in acc_pane_names[r_idx]:
                    visobjs[accp].fillColor = green_flash
                    visobjs[accp].lineColor = line_flash
            else: # ambiguous result, just clear acc squares
                for accp in acc_pane_names[r_idx]:
                    visobjs[accp].fillColor = col_anim(
                    visobjs[accp].visobj.fillColor,back_color,monitor_fps*0.4)            
    # store threshold for item
    ear_thresh = dec2dcb((np.max(swr.data[:,0]),np.max(swr.data[:,1])))
    thresh_results.append([sound_idx,swr.name,ear_thresh])
    
# write to file
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
              idx=thrsh[0],name=thrsh[1],right=thrsh[2][0],left=thrsh[2][1]))
        
monitor.close()                    
core.quit()