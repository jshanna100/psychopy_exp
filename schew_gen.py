import numpy as np
from numpy.random import randint
import pickle

def reihe_gen(time,n_schw_rang,min_dist,max_dist,other_set=0):
    onsets = [0]
    while onsets[0] == 0:
        for i_idx in range(randint(*n_schw_rang)):
            onsets.append(randint(time))
        onsets.append(time)
        onsets.sort()
        time_comp = np.zeros(len(onsets)-1,dtype=bool)
        for o_idx,o in enumerate(range(1,len(onsets))):
            if onsets[o]-onsets[o-1]>min_dist and onsets[o]-onsets[o-1]<max_dist:
                time_comp[o_idx] = 1
            if other_set is not 0:
                if np.any(abs(other_set-onsets[o])<min_dist):
                    time_comp[o_idx] = 0

        if np.all(time_comp):
            onsets.remove(0)
            onsets.remove(time)
        else:
            onsets = [0]
    return onsets

sound_name_list = ["4000Hz.wav","4000_cheby.wav","4000_fftf.wav","6000Hz.wav",
                   "6500Hz.wav","7000Hz.wav","7500Hz.wav"]

schwank = {}
for s in sound_name_list:
    schwank[s] = np.array(reihe_gen(70000,(10,11),2500,8500,other_set=0))
    print(s)
    #schwank[s] = np.empty(0)

with open("audprac","wb") as f:
    pickle.dump(schwank,f)
