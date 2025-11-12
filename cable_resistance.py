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

def get_input_file():
    input_file = input("Enter input file name containing VCON, VMON, and IMON data: ")
    return input_file

def get_output_filename(input_file):
    # Split filename and extension
    name, ext = os.path.splitext(input_file)
    return f"{name}_processed{ext}"

def process_data(input_file):
    print("Processing data from combined file")
    
    # Dictionary to store data by channel
    channel_data = {}
    
    # Debug: Print raw data example
    # print("\nFirst 5 lines of input file:")
    # with open(input_file, 'r') as f:
    #     for i, line in enumerate(f):
    #         if i < 5:
    #             print(line.strip())
    #             parts = line.strip().split(';')
    #             print(f"Split parts: {parts}")
    #             if 'channel' in parts[1]:
    #                 channel = parts[1].split('channel')[1][:3]
    #                 print(f"Extracted channel: {channel}")
    #                 print(f"Type detection: {'vMon' if 'vMon' in parts[1] else 'vCon' if 'vCon' in parts[1] else 'iMon' if 'iMon' in parts[1] else 'unknown'}")
    
    with open(input_file, 'r') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) >= 2:
                timestamp = float(parts[0])
                value = float(parts[2])
                
                # Extract channel number with debug output
                channel = None
                if 'channel' in parts[1]:
                    channel = parts[1].split('channel')[1][:3]
                    
                    # Extract measurement type more reliably
                    measurement_type = 'unknown'
                    if 'actual.vMon' in parts[1]:
                        measurement_type = 'vMon'
                    elif 'actual.vCon' in parts[1]:
                        measurement_type = 'vCon'
                    elif 'actual.iMon' in parts[1]:
                        measurement_type = 'iMon'
                        
                    if measurement_type == 'unknown':
                        print(f"Warning: Unknown measurement type in line: {parts[1]}")

                if channel:
                    if channel not in channel_data:
                        channel_data[channel] = {'vMon': [], 'vCon': [], 'iMon': []}
                        print(f"Created new channel entry for channel {channel}")
                    
                    if 'vmon' in parts[1].lower():
                        channel_data[channel]['vMon'].append((timestamp, value))
                    elif 'vcon' in parts[1].lower():
                        channel_data[channel]['vCon'].append((timestamp, value))
                    elif 'imon' in parts[1].lower():
                        channel_data[channel]['iMon'].append((timestamp, value))
    
    # Debug: Print data counts for each channel
    # for channel, data in channel_data.items():
    #     print(f"\nChannel {channel} data counts:")
    #     print(f"VMON points: {len(data['vMon'])}")
    #     print(f"VCON points: {len(data['vCon'])}")
    #     print(f"IMON points: {len(data['iMon'])}")
    
    # Create individual plots for each channel
    for idx, (channel, data) in enumerate(channel_data.items()):
        # Convert to DataFrames
        vCon_df = pd.DataFrame(data['vCon'], columns=['timestamp', 'value'])
        vMon_df = pd.DataFrame(data['vMon'], columns=['timestamp', 'value'])
        iMon_df = pd.DataFrame(data['iMon'], columns=['timestamp', 'value'])
        
        # Debug: Print DataFrame sizes
        print(f"\nDataFrame sizes for channel {channel}:")
        print(f"VCON: {len(vCon_df)}")
        print(f"VMON: {len(vMon_df)}")
        print(f"IMON: {len(iMon_df)}")
        
        # Convert timestamps
        for df in [vCon_df, vMon_df, iMon_df]:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Merge dataframes
        first_merge = pd.merge_asof(vCon_df.sort_values('timestamp'),
                                   vMon_df.sort_values('timestamp'),
                                   on='timestamp',
                                   suffixes=('_vCon', '_vMon'))
        
        merged_df = pd.merge_asof(first_merge,
                                 iMon_df.sort_values('timestamp'),
                                 on='timestamp')
        
        # Calculate resistance with zero current check
        merged_df['resistance'] = float('nan')  # Initialize with NaN
        # Create boolean mask for non-zero current values
        # merged_df['value'] != 0 creates an array like:
        # [True, True, False, True, False, True, ...]
        # where True means current is non-zero
        non_zero_current = merged_df['value'] != 0
        
        # We can use this mask to select only the rows we want:
        # merged_df.loc[non_zero_current, 'resistance'] will only
        # operate on rows where non_zero_current is True
        merged_df.loc[non_zero_current, 'resistance'] = (
            (merged_df.loc[non_zero_current, 'value_vCon'] - 
             merged_df.loc[non_zero_current, 'value_vMon']) / 
             merged_df.loc[non_zero_current, 'value']
        )

        # Filter unrealistic values and NaN
        filtered_df = merged_df[
            (merged_df['resistance'] >= 0.1) & 
            (merged_df['resistance'] <= 0.5) &
            (merged_df['resistance'].notna())
        ].copy()
        
        # Debug: Print merge results
        print(f"After first merge: {len(first_merge)} rows")
        print(f"After final merge: {len(merged_df)} rows")
        print(f"After filtering: {len(filtered_df)} rows")
        
        if len(filtered_df) == 0:
            print("Warning: No data points after filtering!")
            print("Sample of resistance values:", merged_df['resistance'].head())
            print("Min resistance:", merged_df['resistance'].min())
            print("Max resistance:", merged_df['resistance'].max())
            
        print(f"\nChannel {channel}:")
        print(f"Filtered out {len(merged_df) - len(filtered_df)} unrealistic resistance values")
        print(f"Remaining measurements: {len(filtered_df)}")
        
        # Create new figure for each channel
        plt.figure(figsize=(10, 6))
        plt.plot(filtered_df['timestamp'], filtered_df['resistance'],
                color='purple', marker='.', markersize=2, 
                linestyle='-', linewidth=1)
        
        plt.xlabel('Time')
        plt.ylabel('Resistance (Ω)')
        plt.ylim([0.18, 0.22])
        plt.grid(True)
        plt.tight_layout()
        stave_label = input(f"Enter stave label for Channel {channel} plot title: ")
        plt.title(f'Cable Resistance over Time - Stave {stave_label}, Channel {channel}, Filtered: 0.1 ≤ R ≤ 0.5 Ω')
        plt.savefig(f"resistance_{stave_label}_ch{channel}.png", dpi=300, format='png')
        plt.close()

def separate_channels(input_file, output_base):
    """Separate input file into channel-specific files"""
    # Create dictionaries to store lines for each channel
    channels = {
        'channel008': [],
        'channel009': [],
        'channel010': [],
        'channel011': []
    }
    
    # Read input file and separate lines by channel
    with open(input_file, 'r') as f:
        for line in f:
            for channel in channels.keys():
                if channel in line:
                    channels[channel].append(line)
                    break
    
    # Write separated files
    for channel, lines in channels.items():
        if lines:  # Only create file if there are lines for this channel
            output_file = f"{output_base}_{channel}.txt"
            with open(output_file, 'w') as f:
                f.writelines(lines)
            print(f"Created {output_file}")
            
    return channels.keys()

def process_all_channels(input_file):
    """Process and create resistance plots for each channel"""
    print("Processing all channels directly from input file...")
    # Process input file directly without creating temporary files
    process_data(input_file)

# Main execution
if __name__ == "__main__":
    input_file = get_input_file()
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
    else:
        process_all_channels(input_file)