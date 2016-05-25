#!/usr/bin/python2.7
import csv
import argparse

###############################################################
# Description: 	Parse the vdbench csv and add column of 
#		read/write ratio
#
###############################################################

parser = argparse.ArgumentParser(description='Read write ratio parser for vdbench')
parser.add_argument('-i', '--input', help='Input file name', required=True)
parser.add_argument('-o', '--output', help='Output file name', required=True)
args = parser.parse_args()


def find_row(input_f):
    total = 0
    with open(input_f) as csv_file:
        for row in csv.reader(csv_file, delimiter=','):
            for i, col in enumerate(row):
                if col == "Read(MB/sec)":
                    return(int(i))



def add_column(input_f, output_f,read_column):
    all = []
    with open(input_f, 'r') as input_file, open(output_f, 'w') as output_file:
        reader = csv.reader(input_file, delimiter = ',')
        writer = csv.writer(output_file, delimiter = ',')
        row = next(reader)
        row.insert(0, 'Read/Write ratio')
        all.append(row)
        for row in reader:
            read = float(row[read_column])+0.01
            write = float(row[read_column+1])+0.01
            read_ratio = int((read/write)*100)
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
            write_ratio = 100-read_ratio
            row.insert(0, str(read_ratio)+"/"+str(write_ratio))
            all.append(row)
        writer.writerows(all)
read_column = find_row(args.input)
add_column(args.input, args.output, read_column)
