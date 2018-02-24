#!/usr/bin/env python3

from style_codec import *
from pprint import pprint

'''
testPad = MultiPad(rp='0000', cm='4567')

testPadEvents = []
for idx in range(0, 128):
    testPadEvents.append({"time": idx * 200, "command": "on", "note": idx, "velocity": idx})
    testPadEvents.append({"time": idx * 200 + 180, "command": "off", "note": idx, "velocity": 0})
testPad.setEvents(1, testPadEvents)
testPad.setEvents(2, testPadEvents)
testPad.setEvents(3, testPadEvents)
testPad.setEvents(4, testPadEvents)

testPad.saveAsYml('./test.yml')
testPad.saveAsPad('f:/test.pad')
'''

guitarPad = MultiPad.fromPad('../styles/GuitarPads/Steel8BtStrum1.S096.pad')

guitarStyle = Style.fromSty('../styles/K_UnpluggedAcoustic/Accoustic/SoftGuitarBeat.S929.sty')
tablaStyle = Style.fromSty('../styles/YAMAHA Indian Styles fro S970/Bhajan08.T409.prs')

harmonium3Right = {
    'enabled': True,
    'mixer': 100,
    'octave': -1,
    'channel': 0,
    'bankMsb': 51,
    'bankLsb': 0,
    'program': 16,
    'volume': 90
}

harmonium3Left = {
    'enabled': True,
    'mixer': 70,
    'octave': 2,
    'channel': 0,
    'bankMsb': 51,
    'bankLsb': 0,
    'program': 16,
    'volume': 90
}



style = Style(name='Bhadzany01', tempo=100)

style.createTrackSection('Intro A', 4)

style.importChannels(guitarStyle,
     channels=[(0, 0), (2, 1), 11, (3, 2), (7, 3), 12],
     trackSections=['SInt', 'Main A', ('Main A', 'Main B')]
)

style.importChannels(tablaStyle,
     channels=[8],
     trackSections=['SInt', 'Main A', ('Main A', 'Main B'), ('Main A', 'Main C')]
)

style.importChannels(guitarStyle,
     channels=[10],
     trackSections=['SInt', 'Main A', ('Main A', 'Main B')]
)

style.setEvents(trackSections=['Main A'], channel=10, noOfBeats=4, events=[
       {"time": 0, "command": "on", "note": 86, "velocity": 0},
       {"time": beats - 20, "command": "off", "note": 86, "velocity": 0},
])

style.casm['Main C'][12] = getCtb2('StlStr', autostart=True, sourceChannel=12, destChannel=12, ntr='guitar', ntt='stroke', rtr='pitch-shift', chordKey='c', chordType='Maj7', noteLowLimit=0, noteHighLimit=127)
events = guitarPad.getEvents(2, translateMode6=False)
style.setEvents(trackSections=['Main C'], channel=12, noOfBeats=8, events=events)

style.setupChannel(9, 'Cymbals', autostart=True, bankMsb=126, bankLsb=1, program=107, ntt='bypass')
style.setEvents(trackSections=['Main A', 'Main B'], channel=9, noOfBeats=4, events=[
       {"time": 0, "command": "on", "note": 86, "velocity": 100},
       {"time": beats - 20, "command": "off", "note": 86, "velocity": 0},
])

style.setEvents(trackSections=['Intro A'], channel=9, noOfBeats=1, events=[
       {"time": 0, "command": "on", "note": 89, "velocity": 50},
       {"time": beats - 20, "command": "off", "note": 89, "velocity": 0},
])

style.createEnding('Main A', 'Ending A', channels=[8])


style.addOTS(right1=harmonium3Right, left=harmonium3Left)
style.addOTS(right1=harmonium3Right, left=harmonium3Left)


style.saveAsYml('../styles/My Styles/Bhadzany01.yml')
style.saveAsSty('../styles/My Styles/Bhadzany01.sty')
style.saveAsSty('f:/Bhadzany01.sty')

