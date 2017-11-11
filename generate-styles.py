#!/usr/bin/env python3

from style_codec import *

guitarStyle = Style.fromSty('../styles/K_UnpluggedAcoustic/Accoustic/SoftGuitarBeat.S929.sty')
tablaStyle = Style.fromSty('../styles/YAMAHA Indian Styles fro S970/Bhajan08.T409.prs')

style = Style(name='Bhadzany01', tempo=100)

style.createTrackSection('Intro A', 4)

style.importChannels(guitarStyle,
     channels=[(0,0), (2,1), 11, (3,2), (7,3), 12],
     trackSections=['SInt', 'Main A', ('Main A', 'Main B'), ('Main A', 'Ending A', 8), ('Main A', 'Ending B', 16)]
)

style.importChannels(tablaStyle,
     channels=[8],
     trackSections=['SInt', 'Main A', ('Main A', 'Main B')]
)

style.importChannels(guitarStyle,
     channels=[10],
     trackSections=['SInt', ('Main A', 'Main B')]
)

style.setupChannel(9, 'Cymbals', bankMsb=126, bankLsb=1, program=107, ntt='bypass')
style.setEvents(trackSections=['Main A', 'Main B'], channel=9, noOfBeats=4, events=[
       {"time": 0, "command": "on", "note": 86, "velocity": 100},
       {"time": beats - 20, "command": "off", "note": 86, "velocity": 0},
])

style.setEvents(trackSections=['Intro A'], channel=9, noOfBeats=1, events=[
       {"time": 0, "command": "on", "note": 89, "velocity": 50},
       {"time": beats - 20, "command": "off", "note": 89, "velocity": 0},
])

style.wrapUpChannels('Ending A', 100)
style.wrapUpChannels('Ending B', 100)

style.createEnding('Main A', 'Ending A', 100, channels=[8, 9])
style.createEnding('Main A', 'Ending B', 100, channels=[8, 9])


harmonium3 = {
    'enabled': True,
    'mixer': 100,
    'octave': -1,
    'channel': 0,
    'bankMsb': 51,
    'bankLsb': 0,
    'program': 16,
    'volume': 90
}

style.addOTS(right1=harmonium3)
style.addOTS(right1=harmonium3)


style.saveAsYml('../styles/My Styles/Bhadzany01.yml')
style.saveAsSty('f:/Bhadzany01.sty')

