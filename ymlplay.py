#!/usr/bin/env python3

import time
import rtmidi
from pprint import pprint
import sys
from style_codec import *
import argparse

parser = argparse.ArgumentParser(description='YML MIDI Player')
parser.add_argument('input', type=str, help='input yaml')
parser.add_argument('-c', '--channels', type=str, default='8,9,10,11,12,13,14,15', help='channel numbers to play')
parser.add_argument('-l', '--list-midi-ports', action='store_true', help='lists midi ports and exits')
parser.add_argument('-p', '--midi-port', type=int, default=0, help='midi port number')
parser.add_argument('-s', '--section', type=int, default=2, help='index of section to play in a loop')
parser.add_argument('-t', '--tempo', type=int, default=100, help='tempo in beats per minute')

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
channelNos.insert(0, None)

initSectionIdxs = [0, 1]
loopSectionIdxs = [args.section]


style = loadYaml(args.input)


trackSections = next(x['track-sections'] for x in style if x['section'] == 'midi')


def getChannelId(no=None):
    if no == None:
        return 'common'
    else:
        return 'channel' + str(no)

def getEvents(sectionIdxs, eot=True):
    sectionTime = 0
    events = []

    for sectionIdx in sectionIdxs:
        section = trackSections[sectionIdx]

        for channelNo in channelNos:

            channelId = getChannelId(channelNo)

            if channelId in section['channels']:
                for event in section['channels'][channelId]:

                    if channelNo != None:
                        event['channel'] = channelNo

                    event['time'] += sectionTime
                    events.append(event)

        sectionTime += section['length']

    events.sort(key=lambda event: event['time'])

    globalTime = 0
    for event in events:
        event['time'] -= globalTime
        globalTime += event['time']

    if eot:
        events.append({
            'time': sectionTime - globalTime,
            'command': 'meta-eot'
        })

    return events


def playEvents(events):
    for event in events:
        tm = event['time']
        if tm > 0:
            time.sleep(tm * (60 / args.tempo / beatResolution))

        if event['command'][0:4] != 'meta':
            data = midiEventCodec.build(event)
            midiout.send_message(data)


initEvents = getEvents(initSectionIdxs, eot=False)
loopEvents = getEvents(loopSectionIdxs)



midiout.open_port(args.midi_port)

playEvents(initEvents)

try:
    while True:
        playEvents(loopEvents)
except KeyboardInterrupt:
    pass


for channelNo in channelNos:
    if channelNo is not None:
        event = {
            'command': 'cc-all-notes-off',
            'channel': channelNo
        }

        data = midiEventCodec.build(event)
        midiout.send_message(data)


del midiout