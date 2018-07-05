from psychopy import core, visual, prefs, parallel, event
prefs.general["audioLib"] = ["pyo"]
from psychopy import sound

port = parallel.ParallelPort(address="/dev/parport0")
event.clearEvents()
win = visual.Window(fullscr=True)

img_name_list = ["Animals_090_h.jpg","Animals_012_h.jpg",
"Animals_095_h.jpg","Animals_054_h.jpg",
"Animals_123_h.jpg","Animals_050_h.jpg"]

sound_name_list = ["4000_cheby.wav","4000_fftf.wav",
"4000Hz.wav","7500Hz.wav"]

def SoundAndTrig(snd,action,trig_val):
    if action:
        print("hi")
        snd.play()
    else:
        snd.stop()
    port.setData(trig_val)


imstims = []
for file_name in img_name_list:
    imstims.append(visual.ImageStim(win,image=file_name))

soundstims = []
for file_name in [*sound_name_list, *sound_name_list[:2]]:
    soundstims.append(sound.Sound(file_name))
    
while True:
    for img_idx,img in enumerate(imstims):
        port.setData(0)
        snd = soundstims[img_idx]
        win.callOnFlip(port.setData, 255)
        for f in range(100):
            img.draw()
            win.flip()
        port.setData(0)
        win.callOnFlip(SoundAndTrig, snd, 1, 128)
        img.draw()
        win.flip()
        for f in range(200):
            img.draw()
            win.flip()
        win.callOnFlip(SoundAndTrig, snd, 0, 0)
        img.draw()
        win.flip()
        for f in range(200):
            img.draw()
            win.flip()
        if len(event.getKeys())>0:
            win.close()
            core.quit()