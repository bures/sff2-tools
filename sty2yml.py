#!/usr/bin/env python3

from style_codec import *
import argparse

parser = argparse.ArgumentParser(description='STY -> YML Converter')
parser.add_argument('input', type=str, help='input style')
parser.add_argument('output', type=str, help='output yaml')

args = parser.parse_args()

style = RawStyle.fromSty(args.input)
style.saveAsYml(args.output)
