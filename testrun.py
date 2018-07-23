from hearingtest import heartest

sound_name_list = ["4000Hz.wav","4000_cheby.wav"]
key_presses = ["3","4"] # these correspond to hitting "left" and "right"
ops = [3.25,7.5,15,30,60]
quorum = 2 # must have this many correct/incorrect to reduce/increase volume
play_duration = 2
jitter_range = (0.8,2)

a = heartest(sound_name_list,key_presses,ops,quorum,play_duration,jitter_range)
print(a)