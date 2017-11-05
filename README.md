# SFF2 Tools
Command line tools for editing Yamaha SFF2 style files (for Tyros and PSR workstations).

The key trick is conversion to/from YAML files. This allows using a text editor to edit the style file. The
textual representation separates style sections and channels. This makes it easy to assemble a style from other
styles just by converting them to YAML and then copy-pasting the respective sections/channels in a text editor.
The resulting YAML file can be then converted back to a SFF2 style file.

Tested on Windows 10. However, there is nothing I'm aware of that prevents it from working on Linux too. 

## Prerequisities

Install Python 3 from https://www.python.org/. Make sure to use the executable installer to get also pip.

Install the following packages using pip: PyYAML, construct, python-rtmidi

```
pip install PyYAML
pip install construct
pip install python-rtmidi
```

## Using sty2yml
The command `sty2yml` converts an SFF1/SFF2 style file to a textual representation in YAML. 

```
python sty2yml.py XXXXX.sty XXXXX.yml
```

## Using sty2yml
The command `yml2sty` converts a textual representation of a style in YAML to an SFF2 style file. 

```
python yml2sty.py XXXXX.yml XXXXX.sty
```

## Using ymlplay

The command `ymlplay` can be used to play a selected part and selected channels of the style in YML formal. Run
without parameters to get help.

Example is below. It plays source channel 15 (counted from 0) of the 2nd section (counted from 0) in the style file 
(this corresponds to Main A). The output goes to MIDI port 1. A list of available MIDI ports can be obtained
by `ymlplay -l`.

```
python ymlplay.py XXXXX.sty -c 15 -p 1 -s 2 -t 100
```

## Limitations

- MH section of the style file is preserved as a binary chunk, but not interpreted. I'm not aware of any style
  files that would use this section. 

- CASM section is ignored by `ymlplay`. This in particular concerns the channel mapping and
  note/chord transpositions. Here the problem is a lack of information how exactly the transposition
  is performed under different settings in CASM. Any guidance here is more than welcome. If there is
  an exact spec (at least of some transposition rules), I'll be happy to implement them.


## Acknowledgements

My big thanks to Peter Wierzba and Michael P. Bedesem for creating
a documentation of SFF2 style files. Available from http://www.wierzba.homepage.t-online.de/stylefiles.htm.  