#!/usr/bin/env python3

from style_codec import *
import argparse

parser = argparse.ArgumentParser(description='YML MIDI Player')
parser.add_argument('input', type=str, help='input yaml')
parser.add_argument('-c', '--channels', type=str, default='8,9,10,11,12,13,14,15', help='channel numbers to play')
parser.add_argument('-l', '--list-midi-ports', action='store_true', help='lists midi ports and exits')
parser.add_argument('-p', '--midi-port', type=int, default=0, help='midi port number')
parser.add_argument('-s', '--section', type=str, default='Main A', help='name of section to play in a loop')
parser.add_argument('-t', '--tempo', type=int, default=120, help='tempo in beats per minute')
parser.add_argument('-k', '--key', type=str, default='c', help='key to play the style in')
parser.add_argument('-r', '--chord', type=str, default='Maj7', help='chord to play the style in')

args = parser.parse_args()


midiout = rtmidi.MidiOut()

if (args.list_midi_ports):
    availablePorts = midiout.get_ports()

    portIdx = 0
    for port in availablePorts:
        print('{}: {}'.format(portIdx, port))
        portIdx += 1

    del midiout
    exit(0)


channelNos = [int(x) for x in args.channels.split(',')]

style = Style.fromYml(args.input)

style.play(channelNos=channelNos, trackSections=[args.section], tempo=args.tempo, midiPort=args.midi_port, key=args.key, chord=args.chord)