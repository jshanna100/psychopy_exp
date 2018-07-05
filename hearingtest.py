from scipy.io import wavfile
import numpy as np
from psychopy import core, visual, prefs
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound

sound_name_list = ["4000_cheby.wav","4000_fftf.wav",
"4000Hz.wav","7500Hz.wav"]
vol_steps = [[0.5,0.25,0.125,0.0625,0.03125,0.015625],
[0.5,0.25,0.125,0.0625,0.03125,0.015625]]
vol = [vol_steps[0][0],vol_steps[1][0]]

# for every file name,convert to stereo, 
# and normalise to [-1,1] range. Store as list of
# numpy arrays to be played later
sound_list = []
for sound_name in sound_name_list:
    nptypes = {np.dtype("int16"):32768,np.dtype("int32"):2147483648}
    fs,sig = wavfile.read(sound_name_list[0])
    negmax = nptypes[sig.dtype]
    sound_list.append((np.tile(sig,(2,1))/negmax).T)
    
#randomise order of sounds
reihenfolge = np.array(range(len(sound_name_list)))
np.random.shuffle(reihenfolge)

# here we go
for stim_idx in np.nditer(reihenfolge):
    while not (vol[0]==vol_steps[0][-1] and vol[1]==vol_steps[1][-1]):
        



core.quit()