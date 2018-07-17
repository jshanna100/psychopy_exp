from scipy.io import wavfile
import numpy as np
from psychopy import core, visual, prefs, event
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound
import datetime
from tkinter import filedialog
from tkinter import Tk

class SoundWrap():
    def __init__(self,name,data,operation,ops,aud_res):
        self.name = name # file name of wav
        self.data = data # wav data in numpy format
        self.operation = operation # operation to perform on data
        self.aud_res = aud_res # resolution of wav file
        self.ops = ops # which arguments to pass to the operation
    def operate(self,side_idx,**kwargs):
        self.data[:,side_idx] = self.operation(self.data[:,side_idx],**kwargs)

def dec2dcb(dec):
    return 20*np.log10(np.abs(dec))

def dcb2dec(dcb):
    return 10**(dcb/20)

<<<<<<< HEAD
def incr_dcb(data,dcb_delta=0,direction=-1):
    # if direction is 1, increase by requested decibels, if -1 decrease by same amount
    dcb = dec2dcb(np.abs(data))
=======
def dcbexp2(data,direction=None):
    print(direction)
    dcb = dec2dcb(data)
>>>>>>> bb767889b17468147e6b3e78efa2ba21841224de
    if direction==1:
        newdcb = dcb + dcb_delta
    elif direction==-1:
<<<<<<< HEAD
        newdcb = dcb - dcb_delta
    newdcb[newdcb<-160]=-160
    print("max: {} min: {}".format(np.max(newdcb),np.min(newdcb)))
=======
        newdcb = dcb + (np.min(dcb)-dcb)/2
    print("new decibel: "+str(np.max(newdcb)))
>>>>>>> bb767889b17468147e6b3e78efa2ba21841224de
    return dcb2dec(newdcb)*np.sign(data)
    

sound_name_list = ["4000Hz.wav"]
thresh_results = []
key_presses = ["4","3"] # these correspond to hitting "right" or "left"
runde = np.array([0,0,1,1])
ops = [[3.25,7.5,15,30,60],[3.25,7.5,15,30,60]]

# for every file name,convert to stereo, 
# and normalise to [-1,1] range, build the SoundWrap objects
sound_list = []
for sound_name in sound_name_list:
    nptypes = {np.dtype("int16"):32768,np.dtype("int32"):2147483648}
    fs,sig = wavfile.read(sound_name_list[0])
    aud_res = nptypes[sig.dtype]
    data = (np.tile(sig,(2,1))/aud_res).T
    # 0 values to infinitesimal values for dB log calculations
    data[data==0]=0.00000001
    sound_list.append(SoundWrap(sound_name,data,incr_dcb,ops,aud_res))
    
# randomise order of sounds
reihenfolge = np.array(range(len(sound_name_list)))
np.random.shuffle(reihenfolge)
# here we go
monitor = visual.Window(size=(400,400))
monitor_fps = monitor.getActualFrameRate()
for sound_idx in np.nditer(reihenfolge):
    swr = sound_list[sound_idx]
    # already do a reduction before we begin
    swr.operate(0,dcb_delta=swr.ops[0].pop(),direction=-1)
    swr.operate(1,dcb_delta=swr.ops[1].pop(),direction=-1) 
    while swr.ops[0] and swr.ops[1]:
        # make versions with sound only in left or right
        sounds = []
        for s_idx in range(2):
            d = swr.data.copy()
            d[:,s_idx] = 0
            sounds.append(sound.Sound(d))
        # present each version, record accuracy
        np.random.shuffle(runde)
        accs = [[],[]]
        for r_idx,r in enumerate(np.nditer(runde)):
            sounds[r].play()
            for f_idx in range(int(monitor_fps*3)):
                monitor.flip()
                response = event.getKeys(key_presses)
                if response:
                    break
            sounds[r].stop()
            if key_presses[r] in response and key_presses[1-r] not in response:
                accs[r].append(1)
            else:
                accs[r].append(0)
            for f_idx in range(int(monitor_fps*0.5)):
                monitor.flip()
            event.clearEvents()
        # assess accuracy and act accordingly
        accs = np.array(accs)
        for r_idx in range(accs.shape[0]):
            if accs[r_idx,].all(): # all correct, decrease volume
                swr.operate(r_idx,dcb_delta=swr.ops[r_idx].pop(),direction=-1)
            elif not accs[r_idx,].any(): # all false, increase
                swr.operate(r_idx,dcb_delta=swr.ops[r_idx].pop(),direction=1)
                                
    # store threshold for item
    ear_thresh = dec2dcb((np.max(swr.data[:,0]),np.max(swr.data[:,1])))
    thresh_results.append([sound_idx,swr.name,ear_thresh])
    
    now = datetime.datetime.now()
    Tk().withdraw()
    filename = filedialog.asksaveasfilename(filetypes=(("Hearing test files","*.hrt"),("All files","*.*")))
    
    with open(filename,"w") as file:
        file.write("Subject {sub}, recorded on {d}.{m}.{y}, {h}:{mi}\n".format(
          sub="test",d=now.day,m=now.month,y=now.year,h=now.hour,mi=now.minute))
        file.write("Index\tWavfile\tRightEar\tLeftEar\n")
        for thrsh in thresh_results:
            file.write("{idx}\t{name}\t{right}\t{left}\n".format(
              idx=thrsh[0],name=thrsh[1],right=thrsh[2][0],left=thrsh[2][1]))
        
            
        
core.quit()