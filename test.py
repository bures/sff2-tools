from pprint import pprint
import yaml
from construct import *

def test(ctx):
    pprint(ctx)
    return True

'''
class GreedyRangeWithLast(Subconstruct):
    def __init__(self, subcon):
        super(GreedyRangeWithLast, self).__init__(subcon)
    def _parse(self, stream, context, path):
        obj = ListContainer()
        context = Container(_ = context, last = None)
        try:
            while True:
                fallback = stream.tell()
                obj.append(self.subcon._parse(stream, context, path))
                context.last = obj[-1]
        except StopIteration:
            pass
        except ExplicitError:
            raise
        except Exception:
            stream.seek(fallback)
        return obj
    def _build(self, obj, stream, context, path):
        if not isinstance(obj, collections.Sequence):
            raise RangeError("expected sequence type, found %s" % type(obj))
        context = Container(_ = context)
        try:
            for i,subobj in enumerate(obj):
                self.subcon._build(subobj, stream, context, path)
        except StopIteration:
            pass
        except ExplicitError:
            raise
        except Exception:
            raise
    def _sizeof(self, context, path):
        raise SizeofError("cannot calculate size, unless element count and size is fixed")
'''

class Type(Construct):
    __slots__ = ["value"]
    def __init__(self, value):
        super(Type, self).__init__()
        self.value = value
    def _parse(self, stream, context, path):
        return self.value
    def _build(self, obj, stream, context, path):
        if obj != self.value:
            raise ConstError("building expected %r but got %r" % (self.value, obj))
    def _sizeof(self, context, path):
        return 0

class VariableLengthUIntAdapter(Adapter):
    def _encode(self, obj, context):
        data = []
        while True:
            val = obj & 0x7f
            obj = obj >> 7

            data.insert(0, val | 0x80)

            if obj == 0:
                lastIdx = len(data) - 1
                data[lastIdx] &= 0x7f
                return data

    def _decode(self, obj, context):
        time = 0
        for idx in range(len(obj)):
            time = (time << 7) + (obj[idx] & 0x7f)
        return time

variableLengthCodec = VariableLengthUIntAdapter(RepeatUntil(lambda obj, lst, ctx: obj < 0x80, Byte))


class OffsetIntAdapter(Adapter):
    __slots__ = ["offset"]
    def __init__(self, subcon, offset):
        super(OffsetIntAdapter, self).__init__(subcon)
        self.offset = offset

    def _encode(self, obj, context):
        return obj - self.offset

    def _decode(self, obj, context):
        return obj + self.offset


midiRunningCodec = Struct(
    EmbeddedBitStruct(
        Const(BitsInteger(1), 0x00),
        "command" / Type("dtto"),
        "data1" / BitsInteger(7)
    ),
    "WARNING" / Computed("Not supported")
)

midiNoteOffCodec = Struct(
    EmbeddedBitStruct(
        Const(BitsInteger(4), 0x08),
        "command" / Type("off"),
        "channel" / BitsInteger(4)
    ),
    "note" / Byte,
    "velocity" / Byte
)

midiNoteOnCodec = Struct(
    EmbeddedBitStruct(
        Const(BitsInteger(4), 0x09),
        "command" / Type("on"),
        "channel" / BitsInteger(4)
    ),
    "note" / Byte,
    "velocity" / Byte
)

midiKeyPressCodec = Struct(
    EmbeddedBitStruct(
        Const(BitsInteger(4), 0x0a),
        "command" / Type("press"),
        "channel" / BitsInteger(4)
    ),
    "key" / Byte,
    "velocity" / Byte
)

midiControlChangeCodec = Struct(
    EmbeddedBitStruct(
        Const(BitsInteger(4), 0x0b),
        "command" / Type("cc"),
        "channel" / BitsInteger(4)
    ),
    "controller" / Byte,
    "value" / Byte
)

midiProgramChangeCodec = Struct(
    EmbeddedBitStruct(
        Const(BitsInteger(4), 0x0c),
        "command" / Type("pc"),
        "channel" / BitsInteger(4)
    ),
    "program" / Byte
)

midiPitchWheelChangeCodec = Struct(
    EmbeddedBitStruct(
        Const(BitsInteger(4), 0x0e),
        "command" / Type("pitch"),
        "channel" / BitsInteger(4)
    ),
    "value" / Int16ul
)

midiSysexCodec = Struct(
    Const(Byte, 0xf0),
    "command" / Type("sysex"),
    "data" / PrefixedArray(OffsetIntAdapter(variableLengthCodec, -1), Byte),
    Const(Byte, 0xf7)
)

def buildMetaFixedLenCodec(id, command, length, valueCodec):
    return Struct(
        Const(Byte, 0xff),
        Const(Byte, id),
        "command" / Type(command),
        Const(Byte, length),
        "value" / valueCodec
    )

def buildMetaTextCodec(id, command):
    return Struct(
        Const(Byte, 0xff),
        Const(Byte, id),
        "command" / Type(command),
        "value" / PascalString(variableLengthCodec, encoding="utf8")
    )

midiMetaSequenceCodec = buildMetaFixedLenCodec(0x00, "meta-sequence", 2, Int16ub)
midiMetaTextCodec = buildMetaTextCodec(0x01, "meta-text")
midiMetaCopyrightCodec = buildMetaTextCodec(0x02, "meta-copyright")
midiMetaTrackNameCodec = buildMetaTextCodec(0x03, "meta-track")
midiMetaTrackInstrumentNameCodec = buildMetaTextCodec(0x04, "meta-instrument")
midiMetaLyricCodec = buildMetaTextCodec(0x05, "meta-lyric")
midiMetaMarkerCodec = buildMetaTextCodec(0x06, "meta-marker")
midiMetaCueCodec = buildMetaTextCodec(0x07, "meta-cue")
midiMetaChannelPrefixCodec = buildMetaFixedLenCodec(0x20, "meta-channel-prefix", 1, Byte)
midiMetaPortCodec = buildMetaFixedLenCodec(0x21, "meta-port", 1, Byte)
midiMetaTempoCodec = buildMetaFixedLenCodec(0x51, "meta-tempo", 3, Int24ub)
midiMetaSMPTEOffsetCodec = buildMetaFixedLenCodec(0x54, "meta-smpte-offset", 5, Byte[5])

midiMetaEOTCodec = Struct(
    Const(Byte, 0xff),
    Const(Byte, 0x2f),
    "command" / Type("meta-eot"),
    Const(Byte, 0)
)

midiMetaTimeSigCodec = Struct(
    Const(Byte, 0xff),
    Const(Byte, 0x58),
    "command" / Type("meta-time"),
    Const(Byte, 4),
    "num" / Byte,
    "denom" / Byte,
    Const(Byte, 24),
    Const(Byte, 8)
)

midiMetaKeySigCodec = Struct(
    Const(Byte, 0xff),
    Const(Byte, 0x59),
    "command" / Type("meta-key"),
    Const(Byte, 2),
    "key" / Int8sl,
    "mode" / Enum(Byte, major=0, minor=1)
)

midiGenericMetaCodec = Struct(
    Const(Byte, 0xff),
    "command" / Type("meta"),
    "id" / Byte,
    "data" / PrefixedArray(variableLengthCodec, Byte),
)

midiEventCodec = Struct(
    "time" / variableLengthCodec,
    "data" / Embedded(Select(
        midiRunningCodec,
        midiNoteOnCodec,
        midiNoteOffCodec,
        midiKeyPressCodec,
        midiControlChangeCodec,
        midiProgramChangeCodec,
        midiPitchWheelChangeCodec,
        midiSysexCodec,
        midiMetaSequenceCodec,
        midiMetaTextCodec,
        midiMetaCopyrightCodec,
        midiMetaTrackNameCodec,
        midiMetaTrackInstrumentNameCodec,
        midiMetaLyricCodec,
        midiMetaMarkerCodec,
        midiMetaCueCodec,
        midiMetaChannelPrefixCodec,
        midiMetaPortCodec,
        midiMetaEOTCodec,
        midiMetaTempoCodec,
        midiMetaSMPTEOffsetCodec,
        midiMetaTimeSigCodec,
        midiMetaKeySigCodec,
        midiGenericMetaCodec
    ))
)

midiTrackCodec = FocusedSeq(1, Const(b"MTrk"), Prefixed(Int32ub, GreedyRange(midiEventCodec)))

midiSectionCodec = Struct(
    Const(b"MThd"),
    "section" / Type("midi"),
    Const(Int32ub, 6),
    Const(Int16ub, 0),
    Const(Int16ub, 1),
    Const(Int16ub, 1920),
    "track" / midiTrackCodec
)



sdecCodec = Struct(
    Const(b"Sdec"),
    "type" / Type("sdec"),
    "name" / PascalString(Int32ub, encoding="utf8")
)

keyCodec = Enum(Byte, **{
    "c": 0,
    "c#": 1,
    "d": 2,
    "d#": 3,
    "e": 4,
    "f": 5,
    "f#": 6,
    "g": 7,
    "g#": 8,
    "a": 9,
    "a#": 10,
    "b": 11
})

ctCommonCodec = Struct(
    "source-channel" / Byte,
    "name" / String(8, encoding="utf8"),
    "destination-channel" / Byte,
    "editable" / Flag,
    "note-play" / BitStruct(
        Const(BitsInteger(4), 0),
        "b" / Bit,
        "a#" / Bit,
        "a" / Bit,
        "g#" / Bit,
        "g" / Bit,
        "f#" / Bit,
        "f" / Bit,
        "e" / Bit,
        "d#" / Bit,
        "d" / Bit,
        "c#" / Bit,
        "c" / Bit
    ),
    "chord-play" / BitStruct(
        Const(BitsInteger(4), 0),
        "bit35" / Bit,
        "autostart" / Bit,
        "1+2+5" / Bit,
        "sus4" / Bit,
        "1+5" / Bit,
        "1+8" / Bit,
        "7aug" / Bit,
        "Maj7aug" / Bit,
        "7(#9)" / Bit,
        "7(b13)" / Bit,
        "7(b9)" / Bit,
        "7(13)" / Bit,
        "7#11" / Bit,
        "7(9)" / Bit,
        "7b5" / Bit,
        "7sus4" / Bit,
        "7th" / Bit,
        "dim7" / Bit,
        "dim" / Bit,
        "minMaj7(9)" / Bit,
        "minMaj7" / Bit,
        "min7(11)" / Bit,
        "min7(9)" / Bit,
        "min(9)" / Bit,
        "m7b5" / Bit,
        "min7" / Bit,
        "min6" / Bit,
        "min" / Bit,
        "aug" / Bit,
        "Maj6(9)" / Bit,
        "Maj7(9)" / Bit,
        "Maj(9)" / Bit,
        "Maj7#11" / Bit,
        "Maj7" / Bit,
        "Maj6" / Bit,
        "Maj" / Bit
    ),
    "source-chord-key" / keyCodec,
    "source-chord-type" / Enum(Byte, **{
        "Maj": 0,
        "Maj6": 1,
        "Maj7": 2,
        "Maj7#11": 3,
        "Maj(9)": 4,
        "Maj7(9)": 5,
        "Maj6(9)": 6,
        "aug": 7,
        "min": 8,
        "min6": 9,
        "min7": 10,
        "m7b5": 11,
        "min(9)": 12,
        "min7(9)": 13,
        "min7(11)": 14,
        "minMaj7": 15,
        "minMaj7(9)": 16,
        "dim": 17,
        "dim7": 18,
        "7th": 19,
        "7sus4": 20,
        "7b5": 21,
        "7(9)": 22,
        "7#11": 23,
        "7(13)": 24,
        "7(b9)": 25,
        "7(b13)": 26,
        "7(#9)": 27,
        "Maj7aug": 28,
        "7aug": 29,
        "1+8": 30,
        "1+5": 31,
        "sus4": 32,
        "1+2+5": 33,
        "cancel": 34
    })
);

ctabCodec = Struct(
    Const(b"Ctab"),
    "type" / Type("ctab"),
    Embedded(Prefixed(Int32ub, Struct(
        Embedded(ctCommonCodec),
        "ntr" / Enum(Byte, **{
            "root-transposition": 0,
            "root-fixed": 1
        }),
        "ntt" / Enum(Byte, **{
            "bypass": 0,
            "melody": 1,
            "chord": 2,
            "bass": 3,
            "melodic-minor": 4,
            "harmonic-minor": 5
        }),
        "high-key" / keyCodec,
        "note-low-limit" / Byte,
        "note-high-limit" / Byte,
        "retrigger-rule" / Enum(Byte, **{
            "stop": 0,
            "pitch-shift": 1,
            "pitch-shift-to-root": 2,
            "retrigger": 3,
            "retrigger-to-root": 4,
            "note-generator": 5
        }),
        "special-features-type" / Byte,
        "special-features-data" / If(this["special-features-type"] == 1, Array(4, Byte))
    )))
)

ctb2SubCodec = Struct(
    "ntr" / Enum(Byte, **{
        "root-transposition": 0,
        "root-fixed": 1,
        "guitar": 2
    }),
    "ntt" / BitStruct(
        "bass" / Flag,
        "rule" / IfThenElse(this._.ntr == "guitar",
            Enum(BitsInteger(7), **{
                "all-purpose": 0,
                "stroke": 1,
                "arpeggio": 2,
            }),
            Enum(BitsInteger(7), **{
                "bypass": 0,
                "melody": 1,
                "chord": 2,
                "melodic-minor": 3,
                "melodic-minor-5th": 4,
                "harmonic-minor": 5,
                "harmonic-minor-5th": 6,
                "natural-minor": 7,
                "natural-minor-5th": 8,
                "dorian": 9,
                "dorian-5th": 10,
            })
        )
    ),
    "high-key" / keyCodec,
    "note-low-limit" / Byte,
    "note-high-limit" / Byte,
    "retrigger-rule" / Enum(Byte, **{
        "stop": 0,
        "pitch-shift": 1,
        "pitch-shift-to-root": 2,
        "retrigger": 3,
        "retrigger-to-root": 4,
        "note-generator": 5
    })
)

ctb2Codec = Struct(
    Const(b"Ctb2"),
    "type" / Type("ctb2"),
    Embedded(Prefixed(Int32ub, Struct(
        Embedded(ctCommonCodec),
        "lowest-note-of-middle-notes" / Byte,
        "highest-note-of-middle-notes" / Byte,
        "low" / ctb2SubCodec,
        "middle" / ctb2SubCodec,
        "high" / ctb2SubCodec,
        "unknown" / Array(7, Byte)
    )))
)

cnttCodec = Struct(
    Const(b"Cntt"),
    "type" / Type("cntt"),
    Embedded(Prefixed(Int32ub, Struct(
        "source-channel" / Byte,
        "ntt" / BitStruct(
            "bass" / Flag,
            "rule" / Enum(BitsInteger(7), **{
                "bypass": 0,
                "melody": 1,
                "chord": 2,
                "melodic-minor": 3,
                "melodic-minor-5th": 4,
                "harmonic-minor": 5,
                "harmonic-minor-5th": 6,
                "natural-minor": 7,
                "natural-minor-5th": 8,
                "dorian": 9,
                "dorian-5th": 10,
            })
        )
    )))
)

debugCodec = Struct(
    "signature" / Const(b"Ctb2"),
    "type" / Type("ctb2"),
    "debug" / GreedyRange(Byte)
)

csegCodec = Struct(
    Const(b"CSEG"),
    "entries" / Prefixed(Int32ub, GreedyRange(Select(sdecCodec, ctabCodec, ctb2Codec, cnttCodec)))
)

casmSectionCodec = Struct(
    Const(b"CASM"),
    "section" / Type("casm"),
    "csegs" / Prefixed(Int32ub, GreedyRange(csegCodec))
)


otsSectionCodec = Struct(
    Const(b"OTSc"),
    "section" / Type("ots"),
    "tracks" / Prefixed(Int32ub, GreedyRange(midiTrackCodec))
)


mdbSectionCodec = Struct(
    Const(b"FNRc"),
    "section" / Type("mdb"),
    "data" / PascalString(Int32ub)
)


styleCodec = GreedyRange(Select(midiSectionCodec, casmSectionCodec, otsSectionCodec, mdbSectionCodec))


class HexInt(int): pass
def hexIntRepresenter(dumper, data):
    return yaml.ScalarNode('tag:yaml.org,2002:int', hex(data))

flowStyleCmds = {'on', 'off', 'cc', 'pc', 'press', 'pitch', 'meta-time', 'meta-key', 'meta-tempo', 'meta-eot', 'meta-marker', 'meta-track', 'meta-text', 'meta', 'sysex'}
flowContainerKeys = {'ntt', 'chord-play', 'note-play'}
hexListKeys = {'data'}
def containerRepresenter(dumper, data, flow_style = None):
    value = []
    node = yaml.MappingNode(u'tag:yaml.org,2002:map', value, flow_style=None)

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)

        if item_key in flowContainerKeys and type(item_value) is Container:
            node_value = containerRepresenter(dumper, item_value, True)

        elif item_key in hexListKeys and type(item_value) is ListContainer:
            node_value = dumper.represent_data([HexInt(val) for val in item_value])

        else:
            node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    if flow_style or ('command' in data and data['command'] in flowStyleCmds):
        node.flow_style = True

    return node

def listContainerRepresenter(dumper, data):
    return dumper.represent_sequence(u'tag:yaml.org,2002:seq', list(data))

yaml.add_representer(Container, containerRepresenter, Dumper=yaml.SafeDumper)
yaml.add_representer(ListContainer, listContainerRepresenter, Dumper=yaml.SafeDumper)
yaml.add_representer(HexInt, hexIntRepresenter, Dumper=yaml.SafeDumper)


with open('sample/KeherwaTaalT226.sty', 'rb') as f:
    data = f.read()

style = styleCodec.parse(data)

styleYml = yaml.safe_dump(style, width=65536)

with open('sample/KeherwaTaalT226.yml', 'w') as f:
    f.write(styleYml)

with open('sample/KeherwaTaalT226-out.sty', 'wb') as f:
    f.write(styleCodec.build(yaml.load(styleYml)))

