from scipy.io import wavfile
import numpy as np
from psychopy import core, visual, prefs, event
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound

class SoundWrap():
    def __init__(self,name,data,operation,op_num,negmax):
        self.name = name
        self.data = data
        self.operation = operation
        self.op_num = op_num
        self.negmax = negmax
        self.op_idx = [0,0]
    def operate(self,side_idx,**kwargs):
        self.data[:,side_idx] = self.operation(self.data[:,side_idx],**kwargs)
        self.op_idx[side_idx] += 1

def pow2plus(data,direction=1):
    return data + data * 1/2 * direction

sound_name_list = ["1000Hz.wav"]
key_presses = ["4","3"] # these correspond to hitting "right" or "left"
runde = np.array([0,0,1,1])

# for every file name,convert to stereo, 
# and normalise to [-1,1] range, build the SoundWrap objects
sound_list = []
for sound_name in sound_name_list:
    nptypes = {np.dtype("int16"):32768,np.dtype("int32"):2147483648}
    fs,sig = wavfile.read(sound_name_list[0])
    negmax = nptypes[sig.dtype]
    data = (np.tile(sig,(2,1))/negmax).T
    sound_list.append(SoundWrap(sound_name,data,pow2plus,(3,3),negmax))
    
# randomise order of sounds
reihenfolge = np.array(range(len(sound_name_list)))
np.random.shuffle(reihenfolge)
# here we go
monitor = visual.Window(size=(400,400))
for sound_idx in np.nditer(reihenfolge):
    swr = sound_list[sound_idx]
    swr.operate(0,direction=-1),swr.operate(1,direction=-1) # already reduce by half before we do anything
    while not (swr.op_idx[0]==swr.op_num[0] and swr.op_idx[1]==swr.op_num[1]):
        # make a versions with sound only in left or right
        sounds = []
        for s_idx in range(2):
            d = swr.data.copy()
            d[:,s_idx] = 0
            sounds.append(sound.Sound(d))
        # present each version, record accuracy
        np.random.shuffle(runde)
        accs = np.zeros((2,len(runde)//2))
        for r_idx,r in enumerate(np.nditer(runde)):
            sounds[r].play()
            for f_idx in range(400):
                monitor.flip()
                response = event.getKeys(key_presses)
                if response:
                    break
            sounds[r].stop()
            print(response)
            if key_presses[r] in response and key_presses[1-r] not in response:
                accs[r,r_idx] = 1 # FIX: 1x4 vector where 2x2 matrix required
                print(key_presses[r])
                print("hit")
            for f_idx in range(400):
                monitor.flip()
            event.clearEvents()
        # assess accuracy and act accordingly
        for r_idx in range(accs.shape[0]):
            if accs[r_idx,].all(): # all correct, decrease volume
                swr.operate(r_idx,direction=-1)
                print("all correct")
            elif not accs[r_idx,].any(): # all false, increase
                swr.operate(r_idx,direction=1)
                print("all false")
                
                

        
            
        
core.quit()