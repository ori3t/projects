#!/usr/bin/python2.7
import csv
import argparse

parser = argparse.ArgumentParser(description='Read write ratio parser for vdbench')
parser.add_argument('-i', '--input', help='Input file name', required=True)
parser.add_argument('-o', '--output', help='Output file name', required=True)
args = parser.parse_args()
#args = parser.add_argument('--version', action='version', version='%(prog)s 1.0')

data = []  # Buffer list
with open(args.input, 'r') as input_file, open(args.output, 'w') as output_file:
    reader = csv.reader(input_file, delimiter = ',')
    writer = csv.writer(output_file, delimiter = ',')

    all = []
    row = next(reader)
    row.insert(0, 'Read/Write ratio')
    all.append(row)
    count = 0
    for row in reader:
        read=float(row[10])+0.01
        write=float(row[11])+0.01
        read_ratio=int((read/write)*100)
        if read_ratio <= 2:
            read_ratio = 0
        elif read_ratio >= 23 and read_ratio < 27:
            read_ratio = 25
        elif read_ratio >= 73 and read_ratio < 77:
            read_ratio = 75
        elif read_ratio >= 98 and read_ratio <= 102:
            read_ratio = 50
        elif read_ratio >= 103:
            read_ratio = 100
        else:
            pass
        write_ratio=100-read_ratio
        row.insert(0, str(read_ratio)+"/"+str(write_ratio))
        all.append(row)
    writer.writerows(all)