from hearingtest import HearTest

sound_name_list = ["4000Hz.wav","4000_cheby.wav"]
key_presses = ["3","4"] # these correspond to hitting "left" and "right"
ops = [60,30,15,7.5,3.25]
practice_ops = [0,0,0]
quorum = 2 # must have this many correct/incorrect to reduce/increase volume
play_duration = 2
jitter_range = (0.8,2)

ht = HearTest(sound_name_list,key_presses,ops,quorum,
             monitor_idx=0,beamer_idx=2,
             practice=0)
a = ht.go()
