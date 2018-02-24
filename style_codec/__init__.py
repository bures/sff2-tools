import time
import rtmidi
from construct import Container
import json

from .codecs import styleCodec, multiPadCodec, midiEventCodec, beatResolution as beats, TrackSplitAdapter, sectionMarkers, csegEntriesCodec
from .yamlex import yaml

from pprint import pprint

getChannelId = TrackSplitAdapter.getChannelId

allTrackSections = ['Prologue', 'SInt', 'Main A', 'Main B', 'Main C', 'Main D', 'Fill In AA', 'Fill In BB',
                 'Fill In CC', 'Fill In DD', 'Intro A', 'Intro B', 'Intro C', 'Ending A', 'Ending B',
                 'Ending C', 'Fill In BA', 'Epilogue']

allTrackSectionsWithNotes = ['Main A', 'Main B', 'Main C', 'Main D', 'Fill In AA', 'Fill In BB',
                 'Fill In CC', 'Fill In DD', 'Intro A', 'Intro B', 'Intro C', 'Ending A', 'Ending B',
                 'Ending C', 'Fill In BA']


allChannels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]


transpositions = {
    'chord': {
        ('Maj7', 'Maj7'): [0, None, None, None, 0, None, None, 0, None, None, None, 0],
        ('Maj7', 'Maj'): [0, None, None, None, 0, None, None, 0, None, None, None, None],
        ('min7(11)', 'Maj7'): [0, None, None, +1, None, +2, None, 0, None, None, +1, None],
        ('min7(11)', 'Maj'): [0, None, None, +1, None, +2, None, 0, None, None, None, None],
        ('Maj7', 'min'): [0, None, None, None, -1, None, None, 0, None, None, None, None],
    },
    'melody': {
        ('Maj7', 'Maj7'): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ('Maj7', 'Maj'): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ('Maj', 'Maj7'): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ('Maj7', 'min'): [0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0],
    }
}

transpositionNotes = {
    'a': 0,
    'a#': 1,
    'b': 2,
    'c': 3,
    'c#': 4,
    'd': 5,
    'd#': 6,
    'e': 7,
    'f': 8,
    'f#': 9,
    'g': 10,
    'g#': 11
}


def clone(obj):
    if isinstance(obj, dict):
        newDict = Container()
        for key, val in obj.items():
            newDict[key] = clone(val)
        return newDict

    elif isinstance(obj, list):
        return [clone(x) for x in obj]
    else:
        return obj


def getEmptyMultipad(cm='1111', rp='1111'):
    return {
        'section': 'midi',
        "tracks": [
            [
                {"time": 0, "command": "meta-time", "num": 4, "denom": 2},
                {"time": 0, "command": "meta-tempo", "value": 500000},
                {"time": 0, "command": "meta-text", "value": "CM" + cm},
                {"time": 0, "command": "meta-text", "value": "RP" + rp},
                {"time": 0, "command": "meta-text", "value": "Pad1"},
                {"time": 0, "command": "meta-text", "value": "Pad2"},
                {"time": 0, "command": "meta-text", "value": "Pad3"},
                {"time": 0, "command": "meta-text", "value": "Pad4"},
                {"time": 0, "command": "meta-text", "value": "I1S096"},
                {"time": 0, "command": "meta-text", "value": "I2S096"},
                {"time": 0, "command": "meta-text", "value": "I3S096"},
                {"time": 0, "command": "meta-text", "value": "I4S096"},
                {"time": 0, "command": "meta-eot"}
            ],
            [
                {"time": 0, "command": "meta-eot"}
            ],
            [
                {"time": 0, "command": "meta-eot"}
            ],
            [
                {"time": 0, "command": "meta-eot"}
            ],
            [
                {"time": 0, "command": "meta-eot"}
            ]
        ]
    }

def getEmptyStyle(name, tempo=100):
    return [
        {
            'section': 'midi',
            'track-sections': [
                {
                    'name': 'Prologue',
                    'length': 0,
                    'channels': {
                        'common': [
                            {'time': 0, 'command': 'meta-time', 'num': 4, 'denom': 2},
                            {'time': 0, 'command': 'meta-tempo', 'value': 60000000 / tempo},
                            {'time': 0, 'command': 'meta-marker', 'value': 'SFF2'},
                            {'time': 0, 'command': 'meta-track', 'value': name},
                            {'time': 0, 'command': 'sysex', 'data': [0x43, 0x76, 0x1a, 0x10, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1]},
                            {'time': 0, 'command': 'sysex', 'data': [0x43, 0x73, 0x39, 0x11, 0x0, 0x46, 0x0]},
                            {'time': 0, 'command': 'sysex', 'data': [0x43, 0x73, 0x1, 0x51, 0x5, 0x0, 0x1, 0x8, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]},
                            {'time': 0, 'command': 'sysex', 'data': [0x43, 0x73, 0x1, 0x51, 0x5, 0x0, 0x2, 0x8, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]}
                        ]
                    }
                },
                {
                    'name': 'SInt',
                    'length': 7680,
                    'channels': {
                        'common': [
                            {'time': 0, 'command': 'meta-marker', 'value': 'SInt'},
                            {'time': 0, 'command': 'sysex', 'data': [0x7e, 0x7f, 0x9, 0x1]},
                            {'time': 225, 'command': 'sysex', 'data': [0x43, 0x10, 0x4c, 0x0, 0x0, 0x7e, 0x0]},
                            {'time': 480, 'command': 'sysex', 'data': [0x43, 0x10, 0x4c, 0x2, 0x1, 0x5a, 0x1]},
                            {'time': 485, 'command': 'sysex', 'data': [0x43, 0x10, 0x4c, 0x8, 0x8, 0x7, 0x3]},
                            {'time': 490, 'command': 'sysex', 'data': [0x43, 0x10, 0x4c, 0x8, 0x9, 0x7, 0x2]}
                        ]
                    }
                },
                {
                    'name': 'Epilogue',
                    'length': 0,
                    'channels': {
                        'common': [
                            {'time': 0, 'command': 'meta-eot'}
                        ]
                    }
                }
            ]
        }
    ]


def getCtb2(name, sourceChannel, destChannel, autostart, ntr, ntt, rtr, chordKey, chordType, noteLowLimit, noteHighLimit):
    return {
        "type": "ctb2",
        "source-channel": sourceChannel,
        "name": name,
        "destination-channel": destChannel,
        "editable": True,
        "note-play": { "b": 1, "a#": 1, "a": 1, "g#": 1, "g": 1, "f#": 1, "f": 1, "e": 1, "d#": 1, "d": 1, "c#": 1, "c": 1 },
        "chord-play": { "bit35": 0, "autostart": 1 if autostart else 0, "1+2+5": 1, "sus4": 1, "1+5": 1, "1+8": 1, "7aug": 1, "Maj7aug": 1, "7(#9)": 1,
            "7(b13)": 1, "7(b9)": 1, "7(13)": 1, "7#11": 1, "7(9)": 1, "7b5": 1, "7sus4": 1, "7th": 1, "dim7": 1, "dim": 1, "minMaj7(9)": 1,
            "minMaj7": 1, "min7(11)": 1, "min7(9)": 1, "min(9)": 1, "m7b5": 1, "min7": 1, "min6": 1, "min": 1, "aug": 1, "Maj6(9)": 1,
            "Maj7(9)": 1, "Maj(9)": 1, "Maj7#11": 1, "Maj7": 1, "Maj6": 1, "Maj": 1 },
        "source-chord-key": chordKey,
        "source-chord-type": chordType,
        "lowest-note-of-middle-notes": 0,
        "highest-note-of-middle-notes": 127,
        "low": {
            "ntr": ntr,
            "ntt": {
                "bass": False,
                "rule": ntt
            },
            "high-key": "g",
            "note-low-limit": noteLowLimit,
            "note-high-limit": noteHighLimit,
            "retrigger-rule": rtr
        },
        "middle": {
            "ntr": ntr,
            "ntt": {
                "bass": False,
                "rule": ntt
            },
            "high-key": "g",
            "note-low-limit": noteLowLimit,
            "note-high-limit": noteHighLimit,
            "retrigger-rule": rtr
        },
        "high": {
            "ntr": ntr,
            "ntt": {
                "bass": False,
                "rule": ntt
            },
            "high-key": "g",
            "note-low-limit": noteLowLimit,
            "note-high-limit": noteHighLimit,
            "retrigger-rule": rtr
        },
        "unknown": [ 0, 0, 0, 0, 0, 0, 0 ]
    }


def getTrackSectionCommon(name):
    return [
        {'time': 0, 'command': 'meta-marker', 'value': name},
        {'time': 0, 'command': 'meta-marker', 'value': 'fn:' + name + '\0'}
    ]


def getChannelSetupEvents(bankMsb, bankLsb, program, volume=100, pan=64, reverb=20, chorus=10, channel=None):
    def withChannel(event):
        if channel is not None:
            event['channel'] = channel
        return event

    return [
        withChannel({ "time": 0, "command": "cc-volume", "value": volume }),
        withChannel({ "time": 0, "command": "cc-pan", "value": pan }),
        withChannel({ "time": 0, "command": "cc-reverb-level", "value": reverb }),
        withChannel({ "time": 0, "command": "cc-chorus-level", "value": chorus }),
        withChannel({ "time": 0, "command": "cc-bank-select-msb", "value": bankMsb }),
        withChannel({ "time": 0, "command": "cc-bank-select-lsb", "value": bankLsb }),
        withChannel({ "time": 0, "command": "pc", "program": program }),
    ]


def getOTSEvents(right1=None, right2=None, right3=None, left=None):
    # http://www.jososoft.dk/yamaha/articles/ots.htm

    def addVoice(part, voice):
        def getOpt(key, defaultVal):
            if key in voice:
                return voice[key]
            else:
                return defaultVal

        nonlocal events

        if voice is not None:
            events.append({'time': 0, 'command': 'sysex', 'data': [0x43, 0x73, 0x1, 0x50, 0x8, part, 0x0, 0xf7 if getOpt('enabled', False) else 0x00]})
            events.append({'time': 0, 'command': 'sysex', 'data': [0x43, 0x73, 0x1, 0x50, 0x8, part, 0x4, getOpt('volume', 100)]})
            events.append({'time': 0, 'command': 'sysex', 'data': [0x43, 0x73, 0x1, 0x50, 0x8, part, 0x3, 0x40 + getOpt('octave', -1)]})

            events.extend(
                getChannelSetupEvents(
                    bankMsb=getOpt('bankMsb', 0),
                    bankLsb=getOpt('bankLsb', 115),
                    program=getOpt('program', 0),
                    volume=getOpt('mixer', 100),
                    pan=getOpt('pan', 64),
                    reverb=getOpt('reverb', 20),
                    chorus=getOpt('chorus', 10),
                    channel=part
                )
            )

    events = [
        {'time': 0, 'command': 'sysex', 'data': [0x43, 0x73, 0x1, 0x50, 0x5, 0x1, 0x1, 0x2a]}, # Header 1
        {'time': 0, 'command': 'sysex', 'data': [0x43, 0x73, 0x1, 0x50, 0x5, 0x1, 0x2, 0x32]}, # Header 2
    ]

    addVoice(0, right1)
    addVoice(1, right2)
    addVoice(2, right3)
    addVoice(3, left)

    events.append({'time': 0, 'command': 'meta-eot'})

    return events


class MultiPad(object):
    translateMode6Table = {
        0x30: 0x30,
        0x31: 0x2B,
        0x34: 0x30,
        0x35: 0x34,
        0x37: 0x37,
        0x39: 0x3C,
        0x3B: 0x40,
        0x3C: 0x30,
        0x3D: 0x2B,
        0x40: 0x30,
        0x41: 0x37,
        0x43: 0x3C,
        0x45: 0x40,
        0x47: 0x43,
        0x48: 0x30,
        0x49: 0x37,
        0x4A: 0x30,
        0x4C: 0x37,
        0x4D: 0x3C,
        0x4F: 0x40,
        0x51: 0x43,
        0x53: 0x48,
        0x54: 0x30,
        0x55: 0x37,
        0x58: 0x3C,
        0x59: 0x40,
        0x5B: 0x43,
        0x5D: 0x48,
        0x5F: 0x4C
    }


    def __init__(self, data = None, cm='1111', rp='1111'):
        if data is None:
            self._data = getEmptyMultipad(cm, rp)
        else:
            self._data = data

    def translateNoteMode6(note):
        if note >= 96:
            return note
        elif note in MultiPad.translateMode6Table:
            return MultiPad.translateMode6Table[note]
        else:
            return None



    @classmethod
    def fromPad(cls, fn):
        with open(fn, 'rb') as f:
            data = f.read()
        return MultiPad(data = multiPadCodec.parse(data))


    @classmethod
    def fromYml(cls, fn):
        with open(fn, 'r') as f:
            data = yaml.safe_load(f)
        return MultiPad(data = data)


    def saveAsPad(self, fn):
        with open(fn, 'wb') as f:
            f.write(multiPadCodec.build(self._data))

    def saveAsYml(self, fn):
        with open(fn, 'w') as f:
            f.write(yaml.safe_dump(self._data, width=65536))

    def saveAsJson(self, fn):
        with open(fn, 'w') as f:
            f.write(json.dumps(self._data, indent=2))

    def getEvents(self, trackNo, startTime=12, timeOffset=0, translateMode6=False):
        result = []
        globalTime = 0

        for event in self._data['tracks'][trackNo]:
            globalTime += event['time']

            if globalTime < startTime:
                continue

            if event['command'] == 'meta-eot':
                continue

            newEvent = clone(event)
            newEvent['time'] = globalTime - startTime + timeOffset
            if 'channel' in newEvent:
                del newEvent['channel']

            if translateMode6:
                cmd = event['command']
                if cmd == 'on' or cmd == 'off':
                    trNote = MultiPad.translateNoteMode6(event['note'])
                    if trNote is not None:
                        newEvent['note'] = trNote
                        result.append(newEvent)
                else:
                    result.append(newEvent)

            else:
                result.append(newEvent)

        return result

    def setEvents(self, trackNo, events):
        rawEvents = []
        globalTime = 0

        for event in events:
            if event['command'] == 'meta-eot':
                continue

            rawEvent = clone(event)
            rawEvent['time'] = event['time'] - globalTime
            rawEvent['channel'] = trackNo - 1

            globalTime = event['time']

            rawEvents.append(rawEvent)

        rawEvents.append(
            {"time": 0, "command": "meta-eot"}
        )

        self._data['tracks'][trackNo] = rawEvents



class RawStyle(object):
    def __init__(self, name = '', tempo=100, style = None):
        if style is None:
            self._style = getEmptyStyle(name, tempo)
        else:
            self._style = style

    @classmethod
    def fromSty(cls, fn):
        with open(fn, 'rb') as f:
            data = f.read()
        return RawStyle(style = styleCodec.parse(data))


    @classmethod
    def fromYml(cls, fn):
        with open(fn, 'r') as f:
            data = yaml.safe_load(f)
        return RawStyle(style = data)


    def saveAsSty(self, fn):
        with open(fn, 'wb') as f:
            f.write(styleCodec.build(self._style))

    def saveAsYml(self, fn):
        with open(fn, 'w') as f:
            f.write(yaml.safe_dump(self._style, width=65536))

    def saveAsJson(self, fn):
        with open(fn, 'w') as f:
            f.write(json.dumps(self._style, indent=2))



class Style(object):
    def __init__(self, name = '', tempo=100, style = None):
        if style is None:
            self._style = getEmptyStyle(name, tempo)
        else:
            self._style = style

        self._explodeAll()
        self._upgradeCASM()


    def _explodeAll(self):
        self.trackSections = self._explodeTrackSections()
        self.casm = self._explodeCASM()
        self.ots = self._explodeOTS()


    def _implodeAll(self):
        self._style = [
            self._implodeTrackSections(self.trackSections),
            self._implodeCASM(self.casm),
            self._implodeOTS(self.ots)
        ]


    def _explodeCASM(self):
        channelsPerPart = {}

        for sect in self._style:
            if sect['section'] == 'casm':
                for cseg in sect['csegs']:
                    sdec = next(entry for entry in cseg['entries'] if entry['type'] == 'sdec')
                    parts = sdec['name'].split(',')

                    for part in parts:
                        partChannels = {}
                        channelsPerPart[part] = partChannels

                        for entry in cseg['entries']:
                            if entry['type'] in ['ctb2', 'ctab', 'cntt']:
                                partChannels[entry['source-channel']] = clone(entry)

        return channelsPerPart


    def _implodeCASM(self, channelsPerPart):
        csegs = {}

        for partName, channels in channelsPerPart.items():
            channelEntries = list(channels.values())
            channelEntries.sort(key=lambda x: x['source-channel'])

            csegHash = csegEntriesCodec.build(channelEntries)

            if csegHash in csegs:
                csegs[csegHash]['names'].append(partName)
            else:
                csegs[csegHash] = {
                    'names': [partName],
                    'entries': channelEntries
                }

        sect = {
            'section': 'casm',
            'csegs': []
        }

        for cs in csegs.values():
            cseg = {
                'entries': [
                    {
                        'type': 'sdec',
                        'name': ','.join(cs['names'])
                    }
                ]
            }

            cseg['entries'].extend(cs['entries'])
            sect['csegs'].append(cseg)

        return sect


    def _explodeTrackSections(self):
        trackSections = {}

        for sect in self._style:
            if sect['section'] == 'midi':
                for trackSect in sect['track-sections']:
                    trackSections[trackSect['name']] = trackSect

        return trackSections


    def _implodeTrackSections(self, trackSections):
        sect = {
            'section': 'midi',
            'track-sections': []
        }

        for name in allTrackSections:
            if name in trackSections:
                sect['track-sections'].append(trackSections[name])

        return sect


    def _explodeOTS(self):
        ots = []

        for sect in self._style:
            if sect['section'] == 'ots':
                ots.extend(sect['tracks'])

        return ots


    def _implodeOTS(self, ots):
        sect = {
            'section': 'ots',
            'tracks': ots
        }

        return sect


    def _upgradeCASM(self, channels=allChannels, trackSections=allTrackSections):
        for name in trackSections:
            if name in self.casm:
                for channel in channels:
                    if channel in self.casm[name]:
                        entry = self.casm[name][channel]

                        if entry['type'] == 'ctab':
                            entry['type'] = 'ctb2'
                            entry['lowest-note-of-middle-notes'] = 0
                            entry['highest-note-of-middle-notes'] = 0
                            entry['low'] = entry['middle'] = entry['high'] = {
                                'ntr': entry['ntr'],
                                'ntt': {
                                    'bass': entry['ntt'] == 'bass',
                                    'rule': entry['ntt'] if entry['ntt'] != 'bass' else 'melody'
                                },
                                'high-key': entry['high-key'],
                                'note-low-limit': entry['note-low-limit'],
                                'note-high-limit': entry['note-high-limit'],
                                'retrigger-rule': entry['retrigger-rule']
                            }
                            entry['unknown'] = [0, 0, 0, 0, 0, 0, 0]

                            del entry['ntr']
                            del entry['ntt']
                            del entry['high-key']
                            del entry['note-low-limit']
                            del entry['note-high-limit']
                            del entry['retrigger-rule']
                            del entry['special-features-type']
                            del entry['special-features-data']

                        elif entry['type'] == ['cntt']:
                            raise Exception('CNTT -> CTB2 upgrade is not supported.')


    def _transposeEvents(self, events, nttRule, fromKey, fromChord, toKey, toChord):
        if nttRule != 'bypass':
            if nttRule not in transpositions:
                print(f'Warning: Transposition table for rule "{nttRule}" not found. Skipping transposition for the affected channel.')
                return events

            if (fromChord, toChord) not in transpositions[nttRule]:
                print(f'Warning: Transposition table for rule "{nttRule}" ({fromChord} -> {toChord}) not found. Skipping transposition for the affected channel.')
                return events

            transTable = transpositions[nttRule][(fromChord, toChord)]
            transBase = transpositionNotes[toKey] - transpositionNotes[fromKey]

            newEvents = []
            for event in events:
                if event['command'] == 'on' or event['command'] == 'off':
                    chordTrans = transTable[event['note'] % 12]
                    if chordTrans is not None:
                        event['note'] += transBase + chordTrans
                        newEvents.append(event)

                else:
                    newEvents.append(event)

            return newEvents

        else:
            return events


    def _createTrackSection(self, trackSection, length):
        self.trackSections[trackSection] = {
            'name': trackSection,
            'length': length,
            'channels': {
                'common': getTrackSectionCommon(trackSection)
            }
        }

        self.casm[trackSection] = {}


    def _loopEvents(self, events, loopLength, targetLength):
        outEvents = []
        timeOffset = 0
        while True:
            for event in events:
                event = clone(event)
                event['time'] += timeOffset

                if event['time'] < targetLength:
                    outEvents.append(event)
                else:
                    break
            else:
                timeOffset += loopLength
                continue

            break

        return outEvents


    @classmethod
    def fromSty(cls, fn):
        with open(fn, 'rb') as f:
            data = f.read()
        return Style(style = styleCodec.parse(data))


    @classmethod
    def fromYml(cls, fn):
        with open(fn, 'r') as f:
            data = yaml.safe_load(f)
        return Style(style = data)


    def saveAsSty(self, fn):
        self._implodeAll()
        with open(fn, 'wb') as f:
            f.write(styleCodec.build(self._style))


    def saveAsYml(self, fn):
        self._implodeAll()
        with open(fn, 'w') as f:
            f.write(yaml.safe_dump(self._style, width=65536))


    def saveAsJson(self, fn):
        with open(fn, 'w') as f:
            f.write(json.dumps(self._style, indent=2))


    def deleteTrackSections(self, trackSections):
        for name in trackSections:
            del self.trackSections[name]
            del self.casm[name]


    def deleteChannels(self, channels, trackSections=allTrackSections):
        for channel in channels:
            channelId = getChannelId(channel)

            for name in trackSections:
                if name in self.trackSections and channelId in self.trackSections[name]['channels']:
                    del self.trackSections[name]['channels'][channelId]

                if name in self.casm and channel in self.casm[name]:
                    del self.casm[name][channel]



    def renumberChannel(self, oldChannel, newChannel, trackSections=allTrackSections):
        oldChannelName = getChannelId(oldChannel)
        newChannelName = getChannelId(newChannel)

        for name in trackSections:
            if name in self.trackSections:
                self.trackSections[name]['channels'][newChannelName] = self.trackSections[name]['channels'][oldChannelName]
                del self.trackSections[name]['channels'][oldChannelName]

            if name in self.casm:
                self.casm[name][newChannel] = self.casm[name][oldChannel]
                self.casm[name][newChannel]['source-channel'] = newChannel
                del self.casm[name][oldChannel]


    def importChannels(self, other, channels, trackSections=allTrackSections):
        for channel in channels:
            if isinstance(channel, tuple):
                fromChannel, toChannel = channel
            else:
                fromChannel = channel
                toChannel = channel

            fromChannelName = getChannelId(fromChannel)
            toChannelName = getChannelId(toChannel)

            for name in trackSections:
                if isinstance(name, tuple):
                    if len(name) == 2:
                        fromTrackSection, toTrackSection = name
                        targetLength = None
                    else:
                        fromTrackSection, toTrackSection, noOfBeats = name
                        targetLength = beats * noOfBeats

                else:
                    fromTrackSection = name
                    toTrackSection = name
                    targetLength = None

                if fromTrackSection in other.trackSections and fromChannelName in other.trackSections[fromTrackSection]['channels']:
                    if targetLength is None:
                        targetLength = other.trackSections[fromTrackSection]['length']

                    if toTrackSection not in self.trackSections:
                        self._createTrackSection(toTrackSection, targetLength)
                    else:
                        if self.trackSections[toTrackSection]['length'] != targetLength:
                            print(f'Warning: The length of target track section "{toTrackSection}" is different. You have to check the resulting style and manually correct the respective midi channel.')

                    self.trackSections[toTrackSection]['channels'][toChannelName] = \
                        self._loopEvents(other.trackSections[fromTrackSection]['channels'][fromChannelName], other.trackSections[fromTrackSection]['length'], targetLength)

                if fromTrackSection in other.casm and fromChannel in other.casm[fromTrackSection]:
                    if toTrackSection not in self.casm:
                        self.casm[toTrackSection] = {}

                    self.casm[toTrackSection][toChannel] = clone(other.casm[fromTrackSection][fromChannel])
                    self.casm[toTrackSection][toChannel]['source-channel'] = toChannel


    def transposeChannel(self, channel, toKey, toChord, part='middle', trackSections=allTrackSectionsWithNotes):
        channelId = getChannelId(channel)

        for name in trackSections:
            if name in self.trackSections:
                if name not in self.casm or channel not in self.casm[name] or self.casm[name][channel]['type'] != 'ctb2':
                    print(f'Warning: Skipping channel {channel} in track section "{name}" because ctb2 entry was not found in CASM')
                    continue

                fromChord = self.casm[name][channel]['source-chord-type']
                fromKey = self.casm[name][channel]['source-chord-key']

                ctb2 = self.casm[name][channel]
                ctb2Part = ctb2[part]

                nttRule = ctb2Part['ntt']['rule']

                self.trackSections[name]['channels'][channelId] = self._transposeEvents(self.trackSections[name]['channels'][channelId], nttRule, fromKey, fromChord, toKey, toChord)

                self.casm[name][channel]['source-chord-type'] = toChord
                self.casm[name][channel]['source-chord-key'] = toKey


    def createEnding(self, sourceTrackSection, destTrackSection, sourceLength=100, channels=allChannels, sourceStartBeat=0, endStartBeat=0, destNoOfBeats=4, mutePos=-20):
        if destTrackSection in self.trackSections:
            length = self.trackSections[destTrackSection]['length']
        else:
            length = destNoOfBeats * beats

        self.importChannels(self, channels=channels, trackSections=[(sourceTrackSection, destTrackSection, int(length / beats))])

        ts = self.trackSections[destTrackSection]

        #self._addEnding(destTrackSection, channels, sourceStartBeat, sourceLength, endStartBeat * beats, length + mutePos)
        #def _addEnding(self, trackSection, channels, fromTime, toTime, offset, mutePos):

        offset = endStartBeat * beats
        fromTime = sourceStartBeat * beats

        for channel in channels:
            channelId = getChannelId(channel)

            if channelId in ts['channels']:
                newEvents = []
                for event in ts['channels'][channelId]:
                    if event['time'] < offset:
                        newEvents.append(event)

                    if event['command'] == 'on' and event['time'] >= fromTime and event['time'] < sourceLength:
                        newEvents.append({
                            "time": event['time'] + offset,
                            "command": "on",
                            "note": event['note'],
                            "velocity": event['velocity']
                        })

                        newEvents.append({
                            "time": length + mutePos,
                            "command": "off",
                            "note": event['note'],
                            "velocity": 0
                        })

                newEvents.sort(key=lambda event: event['time'])
                ts['channels'][channelId] = newEvents


    def createTrackSection(self, trackSection, noOfBeats):
        if trackSection not in self.trackSections:
            self._createTrackSection(trackSection, noOfBeats * beats)


    def setupChannel(self, channel, name, bankMsb, bankLsb, program, autostart=False, destChannel=None, volume=100, pan=64, reverb=20, chorus=10, ntr='root-fixed', ntt='chord', rtr='pitch-shift', chordKey='c', chordType='Maj7', noteLowLimit=0, noteHighLimit=127):
        if destChannel is None:
            destChannel = channel

        channelId = getChannelId(channel)

        for tsName in allTrackSectionsWithNotes:
            if tsName in self.trackSections:
                self.casm[tsName][channel] = getCtb2(name, autostart=autostart, sourceChannel=channel, destChannel=destChannel, ntr=ntr, ntt=ntt, rtr=rtr, chordKey=chordKey, chordType=chordType, noteLowLimit=noteLowLimit, noteHighLimit=noteHighLimit)

        self.trackSections['SInt']['channels'][channelId] = getChannelSetupEvents(bankLsb=bankLsb, bankMsb=bankMsb, program=program, pan=pan, reverb=reverb, chorus=chorus, volume=volume)


    def setEvents(self, channel, noOfBeats, events, trackSections=allTrackSectionsWithNotes, loop=True):
        channelId = getChannelId(channel)
        length = noOfBeats * beats
        for trackSection in trackSections:
            ts = self.trackSections[trackSection]

            if loop:
                if loop and ts['length'] % length != 0:
                    print(f'Warning: The length of track section "{trackSection}" is not a multiply of channel length. You have to check the resulting style and manually correct the respective midi channel.')

                ts['channels'][channelId] = self._loopEvents(events, length, ts['length'])

            else:
                if ts['length'] != length:
                    print(f'Warning: The length of track section "{trackSection}" is different. You have to check the resulting style and manually correct the respective midi channel.')
                ts['channels'][channelId] = events


    def addOTS(self, right1=None, right2=None, right3=None, left=None):
        self.ots.append(getOTSEvents(right1=right1, right2=right2, right3=right3, left=left))


    def play(self, channels=allChannels, trackSections=['Main A'], tempo=120, midiPort=0, key='c', chord='Maj7'):
        channels.insert(0, None)

        def getEvents(trackSections, eot=True, transpose=True):
            sectionTime = 0
            events = []

            for name in trackSections:
                section = self.trackSections[name]

                for channel in channels:
                    channelId = getChannelId(channel)

                    if channelId in section['channels']:
                        inEvents = clone(section['channels'][channelId])

                        if channel is None or not transpose:
                            pass
                        elif name not in self.casm or channel not in self.casm[name] or self.casm[name][channel]['type'] != 'ctb2':
                            print(
                                f'Warning: Skipping transposition of channel {channel} in track section "{name}" because ctb2 entry was not found in CASM')
                        else:
                            fromChord = self.casm[name][channel]['source-chord-type']
                            fromKey = self.casm[name][channel]['source-chord-key']

                            ctb2 = self.casm[name][channel]
                            ctb2Part = ctb2['middle']

                            nttRule = ctb2Part['ntt']['rule']

                            inEvents = self._transposeEvents(inEvents, nttRule, fromKey, fromChord, key, chord)

                        for event in inEvents:
                            if channel != None:
                                event['channel'] = channel

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
                    time.sleep(tm * (60 / tempo / beats))

                if event['command'][0:4] != 'meta':
                    data = midiEventCodec.build(event)
                    midiout.send_message(data)

        initEvents = getEvents(trackSections=['Prologue', 'SInt'], eot=False, transpose=False)
        loopEvents = getEvents(trackSections=trackSections)

        midiout = rtmidi.MidiOut()
        midiout.open_port(midiPort)

        playEvents(initEvents)

        try:
            while True:
                playEvents(loopEvents)
        except KeyboardInterrupt:
            pass

        for channel in channels:
            if channel is not None:
                event = {
                    'command': 'cc-all-notes-off',
                    'channel': channel
                }

                data = midiEventCodec.build(event)
                midiout.send_message(data)

        del midiout
