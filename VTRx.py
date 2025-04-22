import pandas as pd
import matplotlib.pyplot as plt
import datetime 
from datetime import timedelta
import numpy as np
import os
import argparse
import subprocess

VTRx_map = {}
values_map = {}

def epoch_to_datetime(x): # convert epoch values from DARMA to datetime values which can be plotted nicely
    return datetime.datetime.fromtimestamp(x) # handled as timestamps

def convert_to_epoch(date_str, time_str):
    # Convert date and time strings to epoch
    dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())

def VTRx_org():
    # Process input file with sed commands
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help='Input file to process')
    args = parser.parse_args()
    
    # First convert timestamps to epoch
    temp_file = "temp_epoch.txt"
    with open(args.input_file, 'r') as infile, open(temp_file, 'w') as outfile:
        for line in infile:
            parts = line.strip().split(';')
            if len(parts) >= 4:  # Ensure line has enough elements
                epoch_time = convert_to_epoch(parts[0], parts[1])
                new_line = f"{epoch_time};{';'.join(parts[2:])}\n"
                outfile.write(new_line)
            else:
                new_line = f"{line.strip()}\n"  # Write the line as is if it doesn't match the expected format
                outfile.write(new_line)
    
    # Now apply the sed commands to the converted file
    reduced_file = "VTRx_reduced.txt"
    sed_cmd = f"sed 's/its.*:ITS\///g' {temp_file} | sed 's/\\/RU.monitoring.actual.SCA.I_/;/g' > {reduced_file}"
    subprocess.run(sed_cmd, shell=True)
    
    # Clean up temporary file
    os.remove(temp_file)
    
    # Create HICs file
    subprocess.run(f"cat {reduced_file} | cut -d';' -f2 | sort | uniq > VTRx_HICs_actual.txt", shell=True)
    
    df = pd.read_csv(reduced_file, sep=';', header=None, names=("Timestamp", "HIC", "Domain", "Value"))
    
    # commented out date-time conversion for batch client download
    df['Timestamp']=df['Timestamp'].apply(epoch_to_datetime)

    fHICs = open("VTRx_HICs_actual.txt")
    HICs = [ line.rstrip("\n") for line in fHICs.readlines() ]
    HICs.sort()
    print("Collecting HIC names - done.")

    sub1 = "VTRx1"
    sub2 = "VTRx2"

    for hic in HICs:
        for d in [ 'VTRx1', 'VTRx2' ]:
            sel = df.loc[df['HIC'].str.contains(hic) & df['Domain'].str.contains(d)]
            VTRx_key = hic+"_"+d #LX_XX_VTRxA     (A= 1 or 2)
            VTRx_map[VTRx_key] = sel
            values_map[VTRx_key] = list(zip(sel["Timestamp"], sel["Value"]))
            


# trigger on the difference in subsequent values
# instead of a single threshold
def trigger(VTRx_values):             #, output_file="VTRx_timestamps.txt"):
    trigger_vals = []
    for i,yval in enumerate(VTRx_values):
        if(i < (len(VTRx_values)-1)):
            if(yval[1] <= 0): continue
            if(VTRx_values[i+1][1] <= 0): continue
            diff = abs(yval[1] - VTRx_values[i+1][1]) #calculate difference in subsequent trimmer values
            if(diff > 25): #trigger if the change is greater than 5
                trigger_vals.append(VTRx_values[i][0])

    # with open(output_file, "w") as file:
    #     for timestamp in trigger_vals:
    #         file.write(f"{timestamp}\n")

    return trigger_vals


def month_trend(VTRx_values, output_file="VTRx_month_trend.txt"):
    month_data = {}
    
    # Group by month
    for timestamp, value in VTRx_values:
        if value <= 0:  # Skip invalid values
            continue
        month_key = timestamp.strftime('%Y-%m')
        if month_key not in month_data:
            month_data[month_key] = {'first': (timestamp, value)} #dictionary of a dictionary
        #relies on VTRx_values being sorted by timestamp
        month_data[month_key]['last'] = (timestamp, value) #this overwrites itself, so is last by construction
    
    # Write results to file
    with open(output_file, "w") as file:
        file.write("Month,First Timestamp,First Value,Last Timestamp,Last Value,Diff\n")
        for month in sorted(month_data.keys()):
            first_time, first_val = month_data[month]['first']
            last_time, last_val = month_data[month]['last']
            diff = last_val- first_val
            file.write(f"{month},{first_time},{first_val:.2f},{last_time},{last_val:.2f},{diff}\n")


def plotting():
    print("plotting now")
    sub1 = "VTRx1"
    sub2 = "VTRx2"
    for y in VTRx_map.keys():
        if sub1 in y:
            sel = VTRx_map[y]
            VTRx_values = values_map[y]
            # trig_times = trigger(VTRx_values)            #, y+"_trigger_timestamps.txt")
            month_trend(VTRx_values, f"VTRx_allstaves/{y}_month_trend.txt")  # Add monthly trend analysis
            # for x in trig_times:
            #     sel.plot(x='Timestamp', y='Value', xlabel='Time', ylabel='value')
            #     plt.ylim([-100, 500])
            #     formatted_time = x.strftime("%Y-%m-%d_%H-%M")
            #     lowlim = x - timedelta(minutes=15)
            #     uplim = x + timedelta(hours=1)
            #     plt.xlim([lowlim, uplim])
            #     plt.xlabel("Time")
            #     plt.ylabel("VTRx1 ($\mu$A)")
            #     plt.title(y)
            #     plt.savefig(f"VTRx/{y}_triggered_{formatted_time}.png", dpi=300, format='png')
            #     plt.close()
        elif sub2 in y:
            sel = VTRx_map[y]
            VTRx_values = values_map[y]
            # trig_times = trigger(VTRx_values)            #, y+"_trigger_timestamps.txt")
            month_trend(VTRx_values, f"VTRx_allstaves/{y}_month_trend.txt")  # Add monthly trend analysis
            # for x in trig_times:
            #     sel.plot(x='Timestamp', y='Value', xlabel='Time', ylabel='value')
            #     plt.ylim([-100, 500])
            #     formatted_time = x.strftime("%Y-%m-%d_%H-%M")
            #     lowlim = x - timedelta(minutes=15)
            #     uplim = x + timedelta(hours=1)
            #     plt.xlim([lowlim, uplim])
            #     plt.xlabel("Time")
            #     plt.ylabel("VTRx1 ($\mu$A)")
            #     plt.title(y)
            #     plt.savefig(f"VTRx/{y}_triggered_{formatted_time}.png", dpi=300, format='png')
            #     plt.close()

def plot_diff():
    print("plotting monthly differences")
    # if not os.path.exists("VTRx_monthly"):
    #     os.makedirs("VTRx_monthly")
        
    for y in VTRx_map.keys():
        sub1 = "VTRx1"
        sub2 = "VTRx2"
        trend_file = f"VTRx_allstaves/{y}_month_trend.txt"
        if not os.path.exists(trend_file):
            continue
            
        # Read the trend data
        df = pd.read_csv(trend_file)
        maximum_diff = df['Diff'].max()
        if sub1 in y:
            if maximum_diff >= 10:
                # Create the plot
                plt.figure(figsize=(10, 6))
                plt.bar(df['Month'], df['Diff'])
                plt.xticks(rotation=45)
                plt.xlabel('Month')
                plt.ylabel('Change in Value ($\mu$A)')
                plt.title(f'Monthly Changes - {y}')
                plt.tight_layout()
                # Save the plot
                plt.savefig(f"VTRx_allstaves/{y}_monthly_diff.png", dpi=300, format='png')
                plt.close()
            elif maximum_diff < 10:
                if os.path.exists(trend_file):
                    os.remove(trend_file)
                    print(f"removed non-triggered file {trend_file}")
                else:
                    print("The file does not exist")
        elif sub2 in y:
            if maximum_diff >= 5:
                # Create the plot
                plt.figure(figsize=(10, 6))
                plt.bar(df['Month'], df['Diff'])
                plt.xticks(rotation=45)
                plt.xlabel('Month')
                plt.ylabel('Change in Value ($\mu$A)')
                plt.title(f'Monthly Changes - {y}')
                plt.tight_layout()
                # Save the plot
                plt.savefig(f"VTRx_allstaves/{y}_monthly_diff.png", dpi=300, format='png')
                plt.close()
            elif maximum_diff < 5:
                if os.path.exists(trend_file):
                    os.remove(trend_file)
                    print(f"removed non-triggered file {trend_file}")
                else:
                    print("The file does not exist")

def analyze_monthly_diffs():
    print("analyzing monthly differences")
    alert_number = input("Enter batch # for monthly alert file name:")
    print("File name is: monthly_alerts_" + alert_number)
    with open(f"VTRx_allstaves/monthly_alerts_{alert_number}.txt", "w") as outfile:
        outfile.write("HIC,Month,Difference,Threshold\n")
        for y in VTRx_map.keys():
            trend_file = f"VTRx_allstaves/{y}_month_trend.txt"
            if not os.path.exists(trend_file):
                continue
                
            # Read the trend data
            df = pd.read_csv(trend_file)
            
            # Apply appropriate threshold based on VTRx type
            threshold = 10 if "VTRx1" in y else 5
            alerts = df[abs(df['Diff']) >= threshold]
            
            # Write alerts to file
            for _, row in alerts.iterrows():
                outfile.write(f"{y},{row['Month']},{row['Diff']:.2f},{threshold}\n")

if __name__ == "__main__":
    VTRx_org()
    plotting()
    plot_diff()
    analyze_monthly_diffs()
