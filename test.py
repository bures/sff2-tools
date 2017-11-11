#!/usr/bin/env python3

from pprint import pprint


from style_codec import *

guitarStyle = Style.fromSty('sample/orig-styles/SoftGuitarBeat.S929.sty')
tablaStyle = Style.fromSty('sample/orig-styles/Bhajan08.T409.prs')

style = Style('TEST')

style.adoptChannel(guitarStyle, fromChannelNo=0, toChannelNo=0, trackSections=['SInt', 'Main A', 'Fill In BA'])
style.adoptChannel(guitarStyle, fromChannelNo=2, toChannelNo=1, trackSections=['SInt', 'Main A', 'Fill In BA'])
style.adoptChannel(guitarStyle, fromChannelNo=11, toChannelNo=11, trackSections=['SInt', 'Main A', 'Fill In BA'])
style.adoptChannel(guitarStyle, fromChannelNo=3, toChannelNo=2, trackSections=['SInt', 'Main A', 'Fill In BA'])
style.adoptChannel(guitarStyle, fromChannelNo=7, toChannelNo=3, trackSections=['SInt', 'Main A', 'Fill In BA'])
style.adoptChannel(guitarStyle, fromChannelNo=12, toChannelNo=12, trackSections=['SInt', 'Main A', 'Fill In BA'])

style.adoptChannel(tablaStyle, fromChannelNo=8, toChannelNo=8, trackSections=['SInt', 'Main A', 'Fill In BA'])
style.adoptChannel(tablaStyle, fromChannelNo=9, toChannelNo=9, trackSections=['SInt', 'Main A', 'Fill In BA'])

style.play(midiPort=1)

style.transposeChannel(channelNo=11, toChord='Maj7', toKey='c')

#style.deleteTrackSections(['Main B', 'Main C', 'Main D', 'Fill In AA', 'Fill In BB', 'Fill In CC', 'Fill In DD', 'Intro A', 'Intro B', 'Intro C', 'Ending A', 'Ending B', 'Ending C'])
#style.deleteChannels([8, 9, 13, 14, 15])

style.saveAsYml('sample/test-o.yml')
style.saveAsSty('sample/test-o.sty')

style.play(channelNos=channelNos, trackSections=[args.section], tempo=args.tempo, midiPort=args.midi_port, key=args.key, chord=args.chord)
