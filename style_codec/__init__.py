import yaml
from construct import *

from .codecs import styleCodec, midiEventCodec, beatResolution
from .yamlex import yaml

__all__ = ["loadSty", "saveSty", "loadYaml", "saveYaml", "beatResolution", "styleCodec", "midiEventCodec"]

def loadSty(fn):
    with open(fn, 'rb') as f:
        data = f.read()

    return styleCodec.parse(data)


def saveSty(fn, style):
    with open(fn, 'wb') as f:
        f.write(styleCodec.build(style))


def loadYaml(fn):
    with open(fn, 'r') as f:
        return yaml.safe_load(f)


def saveYaml(fn, style):
    with open(fn, 'w') as f:
        f.write(yaml.safe_dump(style, width=65536))

