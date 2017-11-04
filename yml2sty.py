#!/usr/bin/env python3

from style_codec import *
import argparse

parser = argparse.ArgumentParser(description='YML -> STY Converter')
parser.add_argument('input', type=str, help='input yaml')
parser.add_argument('output', type=str, help='output style')

args = parser.parse_args()

style = loadYaml(args.input)
saveSty(args.output, style)
