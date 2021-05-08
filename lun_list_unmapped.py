#!/usr/bin/env python

import csv

csv_columns = ['path', 'volume', 'multiprotocol-type', 'mapped']

with open("D4_unmapped.csv", 'r') as csv_file, open("volumes.txt", 'r') as vols_file:
    luns = csv.DictReader(csv_file, fieldnames=csv_columns)
    vols = vols_file.readlines()
    volumes = [s.rstrip('\n') for s in vols]
    for lun in luns:
        if lun['volume'] in volumes:
            print(lun['path'])
            