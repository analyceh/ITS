#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import datetime 
from datetime import timedelta
import numpy as np
import os
import subprocess

def epoch_to_datetime(x): # convert epoch values from DARMA to datetime values which can be plotted nicely
    return datetime.datetime.fromtimestamp(x) # handled as timestamps
    #return datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S') # handled as strings => not practical

def VCON_conversion():
    print("converting VCON")
    input_file = "test_L5_31_vcon.txt"
    output_file = "test_L5_31_vcon_processed.txt"
    
    # First read and sort the file
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        # Sort lines by the timestamp (first field before semicolon)
        sorted_lines = sorted(lines, key=lambda x: float(x.split(';')[0]))
        
        # Write sorted lines to a temporary file
        with open('temp_sorted.txt', 'w') as f:
            f.writelines(sorted_lines)
        
        # Now process the sorted file with PowerShell
        sed_command = f'powershell -Command "Get-Content temp_sorted.txt | ForEach-Object {{$_ -replace \'^(.*?);.*?;(.*?)$\', \'$1;$2\'}} | Set-Content {output_file}"'
        subprocess.run(sed_command, shell=True, check=True)
        os.remove('temp_sorted.txt')  # Clean up temporary file
        print(f"File processed successfully. Output saved to {output_file}")
    except Exception as e:
        print(f"Error processing file: {e}")

def VMON_conversion():
    print("converting VMON")
    input_file = "test_L5_31_vmon.txt"
    output_file = "test_L5_31_vmon_processed.txt"
    
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        sorted_lines = sorted(lines, key=lambda x: float(x.split(';')[0]))
        
        with open('temp_sorted.txt', 'w') as f:
            f.writelines(sorted_lines)
        
        sed_command = f'powershell -Command "Get-Content temp_sorted.txt | ForEach-Object {{$_ -replace \'^(.*?);.*?;(.*?)$\', \'$1;$2\'}} | Set-Content {output_file}"'
        subprocess.run(sed_command, shell=True, check=True)
        os.remove('temp_sorted.txt')
        print(f"File processed successfully. Output saved to {output_file}")
    except Exception as e:
        print(f"Error processing file: {e}")

def IMON_conversion():
    print("converting IMON")
    input_file = "test_L5_31_imon.txt"
    output_file = "test_L5_31_imon_processed.txt"
    
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        sorted_lines = sorted(lines, key=lambda x: float(x.split(';')[0]))
        
        with open('temp_sorted.txt', 'w') as f:
            f.writelines(sorted_lines)
        
        sed_command = f'powershell -Command "Get-Content temp_sorted.txt | ForEach-Object {{$_ -replace \'^(.*?);.*?;(.*?)$\', \'$1;$2\'}} | Set-Content {output_file}"'
        subprocess.run(sed_command, shell=True, check=True)
        os.remove('temp_sorted.txt')
        print(f"File processed successfully. Output saved to {output_file}")
    except Exception as e:
        print(f"Error processing file: {e}")

def graph_each():
    print("graphing each")
    # Read the processed files
    vcon_df = pd.read_csv("test_L5_31_vcon_processed.txt", sep=';', header=None, names=['timestamp', 'value'])
    vmon_df = pd.read_csv("test_L5_31_vmon_processed.txt", sep=';', header=None, names=['timestamp', 'value'])
    imon_df = pd.read_csv("test_L5_31_imon_processed.txt", sep=';', header=None, names=['timestamp', 'value'])

    # Convert timestamps to datetime
    vcon_df['timestamp'] = pd.to_datetime(vcon_df['timestamp'], unit='s')
    vmon_df['timestamp'] = pd.to_datetime(vmon_df['timestamp'], unit='s')
    imon_df['timestamp'] = pd.to_datetime(imon_df['timestamp'], unit='s')

    # Plotting each graph
    plt.figure(figsize=(10, 6))
    
    plt.subplot(3, 1, 1)
    plt.plot(vcon_df['timestamp'], vcon_df['value'], label='VCON', color='blue')
    plt.title('VCON over Time')
    plt.xlabel('Time')
    plt.ylabel('VCON Value')
    
    plt.subplot(3, 1, 2)
    plt.plot(vmon_df['timestamp'], vmon_df['value'], label='VMON', color='green')
    plt.title('VMON over Time')
    plt.xlabel('Time')
    plt.ylabel('VMON Value')

    plt.subplot(3, 1, 3)
    plt.plot(imon_df['timestamp'], imon_df['value'], label='IMON', color='red')
    plt.title('IMON over Time')
    plt.xlabel('Time')
    plt.ylabel('IMON Value')

    plt.tight_layout()
    plt.savefig("VCON_VMON_IMON.png", dpi=300, format='png')

def graph_resistance():
    print("graphing resistance")
    # Read the processed files
    vcon_df = pd.read_csv("test_L5_31_vcon_processed.txt", sep=';', header=None, names=['timestamp', 'value'])
    vmon_df = pd.read_csv("test_L5_31_vmon_processed.txt", sep=';', header=None, names=['timestamp', 'value'])
    imon_df = pd.read_csv("test_L5_31_imon_processed.txt", sep=';', header=None, names=['timestamp', 'value'])

    # Convert timestamps to datetime
    vcon_df['timestamp'] = pd.to_datetime(vcon_df['timestamp'], unit='s')
    vmon_df['timestamp'] = pd.to_datetime(vmon_df['timestamp'], unit='s')
    imon_df['timestamp'] = pd.to_datetime(imon_df['timestamp'], unit='s')

    # Merge dataframes on closest timestamps
    # First merge: combines VCON and VMON based on closest timestamps
    first_merge = pd.merge_asof(vcon_df.sort_values('timestamp'),  # First dataframe (VCON)
                               vmon_df.sort_values('timestamp'),    # Second dataframe (VMON)
                               on='timestamp',                      # Match on timestamp column
                               suffixes=('_vcon', '_vmon'))        # Add suffixes to distinguish values

    # Second merge: takes result of first merge and combines with IMON
    merged_df = pd.merge_asof(first_merge,                        # Result of VCON+VMON merge
                             imon_df.sort_values('timestamp'),     # IMON dataframe
                             on='timestamp')                       # Match on timestamp column

    # Result: merged_df now contains rows where timestamps are closely aligned
    # Each row has: timestamp, value_vcon, value_vmon, value (IMON)
    
    # Calculate resistance: (VCON - VMON) / IMON
    merged_df['resistance'] = (merged_df['value_vcon'] - merged_df['value_vmon']) / (merged_df['value'])

    # Plot resistance
    plt.figure(figsize=(10, 6))
    plt.plot(merged_df['timestamp'], merged_df['resistance'], label='Resistance', color='purple')
    plt.title('Cable Resistance over Time')
    plt.xlabel('Time')
    plt.ylabel('Resistance (Ω)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("Resistance.png", dpi=300, format='png')

# Main execution
VCON_conversion()
VMON_conversion()
IMON_conversion()
graph_each()
graph_resistance()