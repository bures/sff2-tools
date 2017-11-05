import yaml
from construct import *

class HexInt(int): pass
def hexIntRepresenter(dumper, data):
    return yaml.ScalarNode('tag:yaml.org,2002:int', hex(data))

flowStyleCmds = {'on', 'off', 'cc', 'cc-volume', 'cc-bank-select-msb', 'cc-bank-select-lsb', 'cc-reverb-level', 'cc-chorus-level', 'cc-pan', 'cc-all-notes-off', 'pc', 'press', 'pitch', 'meta-time', 'meta-key', 'meta-tempo', 'meta-eot', 'meta-marker', 'meta-track', 'meta-text', 'meta', 'sysex'}
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

