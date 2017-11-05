# sff2-tools
Command line tools for editing Yamaha SFF2 style files (for Tyros and PSR workstations)

## Prerequisities

Install Python from https://www.python.org/. Make sure to use the executable installer to get also pip.

Install the following packages using pip: PyYAML, construct, python-rtmidi

```
pip install PyYAML
pip install construct
pip install python-rtmidi
```

## Using ymlplay

```
python ymlplay.py TB1.sty -c 15 -p 1 -s 2 -t 100
```