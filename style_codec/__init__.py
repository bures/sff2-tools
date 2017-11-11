import time
import rtmidi
from construct import Container

from .codecs import styleCodec, midiEventCodec, beatResolution, TrackSplitAdapter, sectionMarkers, csegEntriesCodec
from .yamlex import yaml

from pprint import pprint

allTrackSections = ['Prologue', 'SInt', 'Main A', 'Main B', 'Main C', 'Main D', 'Fill In AA', 'Fill In BB',
                 'Fill In CC', 'Fill In DD', 'Intro A', 'Intro B', 'Intro C', 'Ending A', 'Ending B',
                 'Ending C', 'Fill In BA', 'Epilogue']

allTrackSectionsWithNotes = ['Main A', 'Main B', 'Main C', 'Main D', 'Fill In AA', 'Fill In BB',
                 'Fill In CC', 'Fill In DD', 'Intro A', 'Intro B', 'Intro C', 'Ending A', 'Ending B',
                 'Ending C', 'Fill In BA']


allChannelNos = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]


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


def deepcopy(obj):
    if isinstance(obj, dict):
        newDict = Container()
        for key, val in obj.items():
            newDict[key] = deepcopy(val)
        return newDict

    elif isinstance(obj, list):
        return [deepcopy(x) for x in obj]
    else:
        return obj


def getEmptyStyle(name):
    data = '''- section: midi
  track-sections:
  - name: Prologue
    length: 0
    channels:
      common:
      - {time: 0, command: meta-time, num: 4, denom: 2}
      - {time: 0, command: meta-tempo, value: 428571}
      - {time: 0, command: meta-marker, value: SFF2}
      - {time: 0, command: meta-track, value: "''' + name + '''"}
      - {time: 0, command: sysex, data: [0x43, 0x76, 0x1a, 0x10, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1]}
      - {time: 0, command: sysex, data: [0x43, 0x73, 0x39, 0x11, 0x0, 0x46, 0x0]}
      - {time: 0, command: sysex, data: [0x43, 0x73, 0x1, 0x51, 0x5, 0x0, 0x1, 0x8, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]}
      - {time: 0, command: sysex, data: [0x43, 0x73, 0x1, 0x51, 0x5, 0x0, 0x2, 0x8, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]}
  - name: SInt
    length: 7680
    channels:
      common:
      - {time: 0, command: meta-marker, value: SInt}
      - {time: 0, command: sysex, data: [0x7e, 0x7f, 0x9, 0x1]}
      - {time: 225, command: sysex, data: [0x43, 0x10, 0x4c, 0x0, 0x0, 0x7e, 0x0]}
      - {time: 480, command: sysex, data: [0x43, 0x10, 0x4c, 0x2, 0x1, 0x5a, 0x1]}
      - {time: 485, command: sysex, data: [0x43, 0x10, 0x4c, 0x8, 0x8, 0x7, 0x3]}
      - {time: 490, command: sysex, data: [0x43, 0x10, 0x4c, 0x8, 0x9, 0x7, 0x2]}
  - name: Epilogue
    length: 0
    channels:
      common:
      - {time: 0, command: meta-eot}
'''

    return yaml.safe_load(data)


def getTrackSectionCommon(name):
    return [
        {'time': 0, 'command': 'meta-marker', 'value': name},
        {'time': 0, 'command': 'meta-marker', 'value': 'fn:' + name + '\0'}
    ]


class RawStyle(object):
    def __init__(self, name = '', style = None):
        if style is None:
            self._style = getEmptyStyle(name)
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
        with open(fn, 'wb') as f:
            f.write(yaml.safe_dump(self._style, width=65536))



class Style(object):
    def __init__(self, name = '', style = None):
        if style is None:
            self._style = getEmptyStyle(name)
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
                                partChannels[entry['source-channel']] = deepcopy(entry)

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


    def _upgradeCASM(self, channelNos=allChannelNos, trackSections=allTrackSections):
        for name in trackSections:
            if name in self.casm:
                for channelNo in channelNos:
                    if channelNo in self.casm[name]:
                        entry = self.casm[name][channelNo]

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



    def deleteTrackSections(self, trackSections):
        for name in trackSections:
            del self.trackSections[name]
            del self.casm[name]


    def deleteChannels(self, channelNos, trackSections=allTrackSections):
        for channelNo in channelNos:
            channelName = TrackSplitAdapter.getChannelId(channelNo)

            for name in trackSections:
                if name in self.trackSections and channelName in self.trackSections[name]['channels']:
                    del self.trackSections[name]['channels'][channelName]

                if name in self.casm and channelNo in self.casm[name]:
                    del self.casm[name][channelNo]



    def renumberChannel(self, oldChannelNo, newChannelNo, trackSections=allTrackSections):
        oldChannelName = TrackSplitAdapter.getChannelId(oldChannelNo)
        newChannelName = TrackSplitAdapter.getChannelId(newChannelNo)

        for name in trackSections:
            if name in self.trackSections:
                self.trackSections[name]['channels'][newChannelName] = self.trackSections[name]['channels'][oldChannelName]
                del self.trackSections[name]['channels'][oldChannelName]

            if name in self.casm:
                self.casm[name][newChannelNo] = self.casm[name][oldChannelNo]
                self.casm[name][newChannelNo]['source-channel'] = newChannelNo
                del self.casm[name][oldChannelNo]


    def adoptChannel(self, other, fromChannelNo, toChannelNo, trackSections=allTrackSections):
        fromChannelName = TrackSplitAdapter.getChannelId(fromChannelNo)
        toChannelName = TrackSplitAdapter.getChannelId(toChannelNo)

        for name in trackSections:
            if name in other.trackSections and fromChannelName in other.trackSections[name]['channels']:
                if name not in self.trackSections:
                    self.trackSections[name] = {
                        'name': name,
                        'length': other.trackSections[name]['length'],
                        'channels': {
                            'common': getTrackSectionCommon(name)
                        }
                    }
                else:
                    if self.trackSections[name]['length'] != other.trackSections[name]['length']:
                        print(f'Warning: Lengths of source and target track section "{name}" differ')


                self.trackSections[name]['channels'][toChannelName] = deepcopy(other.trackSections[name]['channels'][fromChannelName])

            if name in other.casm and fromChannelNo in other.casm[name]:
                if name not in self.casm:
                    self.casm[name] = {}

                self.casm[name][toChannelNo] = deepcopy(other.casm[name][fromChannelNo])
                self.casm[name][toChannelNo]['source-channel'] = toChannelNo


    def transposeChannel(self, channelNo, toKey, toChord, part='middle', trackSections=allTrackSectionsWithNotes):
        channelName = TrackSplitAdapter.getChannelId(channelNo)

        for name in trackSections:
            if name in self.trackSections:
                if name not in self.casm or channelNo not in self.casm[name] or self.casm[name][channelNo]['type'] != 'ctb2':
                    print(f'Warning: Skipping channel {channelNo} in track section "{name}" because ctb2 entry was not found in CASM')
                    continue

                fromChord = self.casm[name][channelNo]['source-chord-type']
                fromKey = self.casm[name][channelNo]['source-chord-key']

                ctb2 = self.casm[name][channelNo]
                ctb2Part = ctb2[part]

                nttRule = ctb2Part['ntt']['rule']

                self.trackSections[name]['channels'][channelName] = self._transposeEvents(self.trackSections[name]['channels'][channelName], nttRule, fromKey, fromChord, toKey, toChord)

                self.casm[name][channelNo]['source-chord-type'] = toChord
                self.casm[name][channelNo]['source-chord-key'] = toKey


    def play(self, channelNos=allChannelNos, trackSections=['Main A'], tempo=120, midiPort=0, key='c', chord='Maj7'):
        channelNos.insert(0, None)

        def getEvents(trackSections, eot=True, transpose=True):
            sectionTime = 0
            events = []

            for name in trackSections:
                section = self.trackSections[name]

                for channelNo in channelNos:
                    channelId = TrackSplitAdapter.getChannelId(channelNo)

                    if channelId in section['channels']:
                        inEvents = deepcopy(section['channels'][channelId])

                        if channelNo is None or not transpose:
                            pass
                        elif name not in self.casm or channelNo not in self.casm[name] or self.casm[name][channelNo]['type'] != 'ctb2':
                            print(
                                f'Warning: Skipping transposition of channel {channelNo} in track section "{name}" because ctb2 entry was not found in CASM')
                        else:
                            fromChord = self.casm[name][channelNo]['source-chord-type']
                            fromKey = self.casm[name][channelNo]['source-chord-key']

                            ctb2 = self.casm[name][channelNo]
                            ctb2Part = ctb2['middle']

                            nttRule = ctb2Part['ntt']['rule']

                            inEvents = self._transposeEvents(inEvents, nttRule, fromKey, fromChord, key, chord)

                        for event in inEvents:
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
                    time.sleep(tm * (60 / tempo / beatResolution))

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

        for channelNo in channelNos:
            if channelNo is not None:
                event = {
                    'command': 'cc-all-notes-off',
                    'channel': channelNo
                }

                data = midiEventCodec.build(event)
                midiout.send_message(data)

        del midiout
