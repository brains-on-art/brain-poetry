import argparse
import json

# Iniit argparse stuff
parser = argparse.ArgumentParser(description='ADD YOUR DESCRIPTION HERE')
parser.add_argument('--name', help='Device name', required=False)
parser.add_argument('--serial_number', help='Serial number', required=False)
parser.add_argument('--config_file', help='Configuration file', required=False)
args = parser.parse_args()

# Check if we were given a config file
if args.config_file:
    config_filename = args.config_file
else:
    config_filename = 'epoc_config.json'

# Check if we got a serial number of if we are gonna dig it from config_file
if args.serial_number:
    serial_number = args.serial_number
elif args.name:
    with open(config_filename) as config_file:
        config = json.load(config_file)
    if args.name in config.keys():
        serial_number = int(config[args.name])
        print(serial_number)
    else:
        print('Device name not found in %s!' % config_filename)
else:
    print('Specify either device name or serial number')
