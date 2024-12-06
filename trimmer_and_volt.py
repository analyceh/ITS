#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import datetime 
from datetime import timedelta
import numpy as np
import os
import subprocess


trim_map = {}
volt_map = {}
savedkey_map = {}


def epoch_to_datetime(x): # convert epoch values from DARMA to datetime values which can be plotted nicely
    return datetime.datetime.fromtimestamp(x) # handled as timestamps
    #return datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S') # handled as strings => not practical


def graphtrimmer():
    os.system("cat trimmerOffset_9_16to30.txt | tr '.' ';' | tr '/' ';' | cut -d';' -f 1,4,6,10,11 | sed 's/AVDD/0/' | sed 's/DVDD/1/' | sed 's/L//' | tr '_' ';' | sed 's/HIC0/HIC0;-1/' |sed 's/HIC//' | sed 's/U/;1/' | sed 's/L/;0/' | grep -v monitoring > trimmerOffset_reduced.txt")
    
    # 0 - Time ; 1 - Layer ; 2 - Stave ; 3 - Module ; 4 - Half-Stave (-1 IB, 0 L, 1 U); 5 - Domain (0 AVDD, 1 DVDD); 6 - trimmer offset
    f="trimmerOffset_reduced.txt"
    arr = np.loadtxt(f, delimiter=';')
    print(arr.shape)

    staves     =(12, 16, 20, 24, 30, 42, 48)
    firstHS    =(-1, -1, -1,  0,  0,  0,  0)
    lastHS     =(-1, -1, -1,  1,  1,  1,  1)
    firstModule=( 0,  0,  0,  1,  1,  1,  1)
    lastModule =( 0,  0,  0,  4,  4,  7,  7)

    badStaves = []

    for layer in range(7):
        for stave in range(staves[layer]):
            for halfStave in range(firstHS[layer], lastHS[layer]+1):
                for module in range(firstModule[layer], lastModule[layer]+1):
                    for domain in range(2):
                        data = arr[(arr[:, 1] == layer) & (arr[:,2] == stave) & (arr[:,3] == module) & (arr[:,4] == halfStave) & (arr[:,5] == domain) & ((arr[:,0]< 1694400000) | (arr[:,0]> 1694512800))]
                        if (len(data) > 0) and (float(np.min(data[:,6]) <= -8.)):
                            x = [epoch_to_datetime(x) for x in data[:,0]]
                            # print(f"L{layer}_{stave:02d}_HS{halfStave}_M{module}_DOMAIN{domain}: entries {len(data[:,6])}, min {np.min(data[:,6])}, max {np.max(data[:,6])}, mean {np.mean(data[:,6])}, median {np.median(data[:,6])}")
                            
                            # save trim arrays of [value, time] in a map for later access
                            trim_key = f"L{layer}_{stave:02d}_HS{halfStave}_M{module}_D{domain}"
                            trim_map[trim_key] = [data[:-1,6],x]
                            # plt.stairs(data[:-1,6], x)
                            # #plt.plot(x, data[:,6])
                            # plt.xlabel("Date")
                            # plt.ylabel("Trimmer Offset")
                            # plt.ylim([-20, 20])
                            # # plt.xlim([datetime.date(2023,9,30),datetime.date(2023,10,13)])
                            # plt.grid()
                            # plt.gcf().autofmt_xdate()
                            # plt.savefig(f"L{layer}_{stave:02d}_HS{halfStave}_M{module}_D{domain}_trimmerOffset.png", dpi=300, format='png')
                            # plt.close()
                            badStaves.append(f"L{layer}_{stave:02d}")
                            
    badStaves = list(sorted(set(badStaves)))
    print()
    print(badStaves)

    # new map to correlate the badStaves label with trim_map
    # i.e, badStave L4_27 has many halfstaves and modules and domains under it
    # this takes L4_27 and will save all L4_27_x_y_z 
    savedkeys = []
    for x in badStaves:
        for key in trim_map.keys():
            if key.startswith(x):
                savedkeys.append(key)
        savedkey_map[x] = savedkeys
        savedkeys = []

    # print(savedkey_map)

def plot_hic(hic, df):    
    for d in [ 'AVDD', 'DVDD' ]:
        sel = df.loc[df['HIC'].str.contains(hic) & df['Domain'].str.contains(d)]
        sel = sel.rename(columns={"Value":hic})
        # print(f"Domain: {d}, Stave/HIC: {hic}, Lines {len(sel)}")
        volt_key = hic+"_"+d 
        volt_map[volt_key] = sel
        # sel.plot(x='Timestamp', y=hic, xlabel="Time", ylabel=hic)
        # plt.xlabel("Time")
        # plt.ylabel("Voltage difference measurement to set value")
        # plt.ylim([-120, 120])
        # plt.savefig(hic+"_"+d+".png", dpi=300, format='png')
        # plt.close()
        # sel = sel.loc[(sel[hic]>-110) & (sel[hic]<110)]
        # # print(f"Domain: {d}, Stave/HIC: {hic}, Lines {len(sel)} after cuts")
        # sel.plot(x='Timestamp', y=hic, xlabel="Time", ylabel=hic)
        # plt.xlabel("Time")
        # plt.ylabel("Voltage difference measurement to set value")
        # plt.ylim([-120, 120])
        # plt.savefig(hic+"_"+d+"_cut.png", dpi=300, format='png')
        # plt.close()



# trigger on the difference in subsequent trimmerOffset values
# instead of a single threshold
def trigger(trim_values):
    trigger_pairs = []
    scaled_trim = [a / 0.00486 for a in trim_values[0]]
    for i,yval in enumerate(scaled_trim):
        if(i < (len(scaled_trim)-1)):
            diff = abs(yval - scaled_trim[i+1]) #calculate difference in subsequent trimmer values
            if(diff > 850): #trigger if the change is greater than 850 (eyeball value)
                trigger_pairs.append(trim_values[1][i])
    print(trigger_pairs)
    return trigger_pairs


def plot_together():
    print("inside together")
    sub0 = "D0"
    sub1 = "D1"
    # for LX_XX in savedkey_map.keys():
    for y in savedkey_map["L4_27"]: #only looking at L4_27 for now to test things quickly
        if sub0 in y: #to be able to check both domains
            z = "L4_27" + "_AVDD"
            # get the trimmer values
            trim_values = trim_map[y] #trim_values is the trimmerOffset array [values, time]
            scaled_trim = [a / 0.00486 for a in trim_values[0]]
            trig_times = trigger(trim_values) #run the trigger to pick out interesting peaks
            for x in trig_times:
                sel = volt_map[z]
                sel.plot(x='Timestamp', y="L4_27", xlabel="Time", ylabel="volt", zorder=1)
                plt.stairs(scaled_trim, trim_values[1], color = 'r', label = 'trim', zorder=2)
                plt.xlabel("Time")
                plt.ylabel("Voltage difference measurement to set value")
                plt.ylim([-50, 50])
                plt.legend(["voltageDiff.PU", "trimmerOffset"])
                # plot ~hour window around the trigger time
                lowlim = x - timedelta(minutes=15)
                uplim = x + timedelta(hours=1)
                plt.xlim([lowlim, uplim])
                # saving and organizing
                formatted_time = x.strftime("%Y-%m-%d_%H-%M")
                if not os.path.exists("L4_27"):
                    os.makedirs("L4_27")
                if not os.path.exists("L4_27/"+y):
                    os.makedirs("L4_27/"+y)
                plt.savefig(f"L4_27/{y}/triggered_{formatted_time}.png", dpi=300, format='png')
                plt.close()       
            # sel = volt_map[z]
            # sel.plot(x='Timestamp', y="L4_27", xlabel="Time", ylabel="volt", zorder=1)
            # plt.stairs(scaled_trim, trim_values[1], color = 'r', label = 'trim', zorder=2)
            # plt.xlabel("Time")
            # plt.ylabel("Voltage difference measurement to set value")
            # # plt.ylim([-100, 100])
            # plt.legend(["voltageDiff.PU", "trimmerOffset"])
            # plt.xlim([datetime.datetime(2024,9,19,15,0,0),datetime.datetime(2024,9,19,16,0,0)])
            # plt.savefig(f"together_{y}.png", dpi=300, format='png')
            # plt.close()  
        elif sub1 in y:
            z = "L4_27" + "_DVDD"
            trim_values = trim_map[y]
            scaled_trim = [a / 0.00486 for a in trim_values[0]]
            trig_times = trigger(trim_values)
            for x in trig_times:
                sel = volt_map[z]
                sel.plot(x='Timestamp', y="L4_27", xlabel="Time", ylabel="volt", zorder=1)
                plt.stairs(scaled_trim, trim_values[1], color = 'r', label = 'trim', zorder=2)
                plt.xlabel("Time")
                plt.ylabel("Voltage difference measurement to set value")
                plt.ylim([-50, 50])
                plt.legend(["voltageDiff.PU", "trimmerOffset"])
                lowlim = x - timedelta(minutes=15)
                uplim = x + timedelta(hours=1)
                plt.xlim([lowlim, uplim])
                formatted_time = x.strftime("%Y-%m-%d_%H-%M")
                if not os.path.exists("L4_27"):
                    os.makedirs("L4_27")
                if not os.path.exists("L4_27/"+y):
                    os.makedirs("L4_27/"+y)
                plt.savefig(f"L4_27/{y}/triggered_{formatted_time}.png", dpi=300, format='png')
                plt.close()  
            # sel = volt_map[z]
            # sel.plot(x='Timestamp', y="L4_27", xlabel="Time", ylabel="volt", zorder=1)
            # plt.stairs(scaled_trim, trim_values[1], color = 'r', label = 'trim', zorder=2)
            # plt.xlabel("Time")
            # plt.ylabel("Voltage difference measurement to set value")
            # # plt.ylim([-100, 100])
            # plt.legend(["voltageDiff.PU", "trimmerOffset"])
            # plt.xlim([datetime.datetime(2024,9,18,13,30,0),datetime.datetime(2024,9,18,14,30,0)])
            # plt.savefig(f"together_{y}.png", dpi=300, format='png')
            # plt.close() 
  

def graphvolt():
    # sed 's/its_dcs:ITS\///g' voltageDiffPU.txt | sed 's/\/PU0\/HIC0.monitoring.actual.voltageDiff.PU.DVDD//g' | sed 's/its_ob_bot:ITS\///g' | sed 's/its_ob_top:ITS\///g' | sed 's/\/PU0\//_/g' | sed 's/.monitoring.actual.voltageDiff.PU.DVDD/;DVDD/g' | sed 's/.monitoring.actual.voltageDiff.PU.AVDD/;AVDD/g' > voltageDiffPU_reduced.txt
    # sed 's/its_dcs:ITS\///g' voltageDiffPU.txt | sed 's/\/PU0\/HIC0.monitoring.actual.voltageDiff.PU./;/g' |sed 's/\/PU0\/HIC0.monitoring.actual.voltageDiff.HIC./;/g' | sed 's/its_ob_bot:ITS\///g' | sed 's/its_ob_top:ITS\///g' | sed 's/\/PU0\//_/g' | sed 's/.monitoring.actual.voltageDiff.PU./;/g' > voltageDiffPU_reduced.txt

    f= "voltageDiffPU_reduced.txt"
    df = pd.read_csv(f, sep=';', header=None, names=( "Timestamp", "HIC", "Domain", "Value" ))
    df['Value']*=1000
    # print(df.head())

    # print("Changing timestamps")
    df['Timestamp']=df['Timestamp'].apply(epoch_to_datetime)
    # print("Changing timestamps - done.")
    # print(df.head())

    # print("Collecting HIC names")
    # cat voltageDiffPU_reduced.txt | cut -d';' -f2 | sort | uniq > HICs.txt
    # os.system("cat voltageDiffPU_reduced.txt | cut -d';' -f2 | sort | uniq > HICs.txt")
    fHICs = open("HICs.txt")
    HICs = [ line.rstrip("\n") for line in fHICs.readlines() ]

    #HICs = []
    #for hic in df['HIC']:
    #    if hic not in HICs:
    #        HICs.append(hic)
    #HICs.sort()
    print("Collecting HIC names - done.")

    # single threaded
    for hic in HICs:
        # if hic in savedkey_map.keys():
        if hic == "L4_27":
            plot_hic(hic, df)

    # parallel
    # p = Pool(10)
    # with p:
    #     p.trim_map(plot_hic, HICs)






print("here")
graphtrimmer()
print("running graphvolt")
graphvolt()
print("running plot_together")
plot_together()
# print(max(trim_map["L6_S0_HS0_M1_D1"]))
# print(min(trim_map["L6_S0_HS0_M1_D1"]))
# print(volt_map["L0_02_AVDD"])