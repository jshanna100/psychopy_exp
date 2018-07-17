from scipy.io import wavfile
import numpy as np
from psychopy import core, visual, prefs, event
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound

class SoundWrap():
    def __init__(self,name,data,operation,op_num,aud_res):
        self.name = name # file name of wav
        self.data = data # wav data in numpy format
        self.operation = operation # operation to perform on data
        self.op_num = op_num # 1x2 tuple, how many operations to perform before quitting, per ear
        self.aud_res = aud_res # resolution of wav file
        self.op_idx = [0,0] # which operation are we currently on, per ear
    def operate(self,side_idx,**kwargs):
        self.data[:,side_idx] = self.operation(self.data[:,side_idx],**kwargs)
        self.op_idx[side_idx] += 1

def dec2dcb(dec):
    return 20*np.log10(np.abs(dec))

def dcb2dec(dcb):
    return 10**(dcb/20)

def dcbexp2(data,direction=None):
    print(direction)
    dcb = dec2dcb(np.abs(data))
    if direction==1:
        newdcb = dcb / 2
    elif direction==-1:
        newdcb = (-70-dcb)/2
    print("new decibel: "+str(np.max(newdcb)))
    return dcb2dec(newdcb)*np.sign(data)
    

sound_name_list = ["4000_cheby.wav"]
key_presses = ["4","3"] # these correspond to hitting "right" or "left"
runde = np.array([0,0,1,1])
op_num = [5,5]

# for every file name,convert to stereo, 
# and normalise to [-1,1] range, build the SoundWrap objects
sound_list = []
for sound_name in sound_name_list:
    nptypes = {np.dtype("int16"):32768,np.dtype("int32"):2147483648}
    fs,sig = wavfile.read(sound_name_list[0])
    aud_res = nptypes[sig.dtype]
    data = (np.tile(sig,(2,1))/aud_res).T
    # 0 values to infinitesimal values for dB calculations
    #data[data==0]=0.000001
    sound_list.append(SoundWrap(sound_name,data,dcbexp2,op_num,aud_res))
    
# randomise order of sounds
reihenfolge = np.array(range(len(sound_name_list)))
np.random.shuffle(reihenfolge)
# here we go
monitor = visual.Window(size=(400,400))
monitor_fps = monitor.getActualFrameRate()
for sound_idx in np.nditer(reihenfolge):
    swr = sound_list[sound_idx]
    swr.operate(0,direction=-1),swr.operate(1,direction=-1) # already reduce by half before we do anything
    while not (swr.op_idx[0]>=swr.op_num[0] and swr.op_idx[1]>=swr.op_num[1]):
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
            for f_idx in range(int(monitor_fps*2)):
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
                swr.operate(r_idx,direction=-1)
            elif not accs[r_idx,].any(): # all false, increase
                swr.operate(r_idx,direction=1)
                
                

        
            
        
core.quit()