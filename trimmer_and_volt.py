#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import datetime
import numpy as np
import os

trim_map = {}
volt_map = {}
savedkey_map = {}


def epoch_to_datetime(x): # convert epoch values from DARMA to datetime values which can be plotted nicely
    return datetime.datetime.fromtimestamp(x) # handled as timestamps
    #return datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S') # handled as strings => not practical


def graphtrimmer():
    os.system("cat trimmerOffset_2023-10-01_12.txt | tr '.' ';' | tr '/' ';' | cut -d';' -f 1,4,6,10,11 | sed 's/AVDD/0/' | sed 's/DVDD/1/' | sed 's/L//' | tr '_' ';' | sed 's/HIC0/HIC0;-1/' |sed 's/HIC//' | sed 's/U/;1/' | sed 's/L/;0/' | grep -v monitoring > trimandvolt_reduced.txt")
    
    # 0 - Time ; 1 - Layer ; 2- Stave ; Module ; Half-Stave (-1 IB, 0 L, 1 U); Domain (0 AVDD, 1 DVDD); trimmer offset
    f="trimandvolt_reduced.txt"
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
                            trim_key = f"L{layer}_{stave:02d}_HS{halfStave}_M{module}_D{domain}"
                            trim_map[trim_key] = [data[:-1,6],x]
                            plt.stairs(data[:-1,6], x)
                            #plt.plot(x, data[:,6])
                            plt.xlabel("Date")
                            plt.ylabel("Trimmer Offset")
                            plt.ylim([-20, 20])
                            plt.xlim([datetime.date(2023,9,30),datetime.date(2023,10,13)])
                            plt.grid()
                            plt.gcf().autofmt_xdate()
                            plt.savefig(f"L{layer}_{stave:02d}_HS{halfStave}_M{module}_D{domain}_trimmerOffset.png", dpi=300, format='png')
                            plt.close()
                            badStaves.append(f"L{layer}_{stave:02d}")
                            
    badStaves = list(sorted(set(badStaves)))
    print()
    print(badStaves)

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
        sel.plot(x='Timestamp', y=hic, xlabel="Time", ylabel=hic)
        plt.xlabel("Time")
        plt.ylabel("Voltage difference measurement to set value")
        plt.ylim([-120, 120])
        plt.savefig(hic+"_"+d+".png", dpi=300, format='png')
        plt.close()
        sel = sel.loc[(sel[hic]>-110) & (sel[hic]<110)]
        # print(f"Domain: {d}, Stave/HIC: {hic}, Lines {len(sel)} after cuts")
        sel.plot(x='Timestamp', y=hic, xlabel="Time", ylabel=hic)
        plt.xlabel("Time")
        plt.ylabel("Voltage difference measurement to set value")
        plt.ylim([-120, 120])
        plt.savefig(hic+"_"+d+"_cut.png", dpi=300, format='png')
        plt.close()

def plot_together():
    for x in savedkey_map.keys():
        for y in savedkey_map[x]:
            trim_values = trim_map[y]
            sel = volt_map["L0_02_AVDD"]
            sel.plot(x='Timestamp', y="L0_02", xlabel="Time", ylabel="L0_02")
            plt.stairs(trim_values[0], trim_values[1], color = 'g', label = 'trim')
            plt.xlabel("Time")
            plt.ylabel("Voltage difference measurement to set value")
            plt.ylim([-120, 120])
            plt.savefig(f"together_{y}.png", dpi=300, format='png')
            plt.close()    

def graphvolt():
    # sed 's/its_dcs:ITS\///g' voltageDiffPU.txt | sed 's/\/PU0\/HIC0.monitoring.actual.voltageDiff.PU.DVDD//g' | sed 's/its_ob_bot:ITS\///g' | sed 's/its_ob_top:ITS\///g' | sed 's/\/PU0\//_/g' | sed 's/.monitoring.actual.voltageDiff.PU.DVDD/;DVDD/g' | sed 's/.monitoring.actual.voltageDiff.PU.AVDD/;AVDD/g' > voltageDiffPU_reduced.txt
    # sed 's/its_dcs:ITS\///g' voltageDiffPU.txt | sed 's/\/PU0\/HIC0.monitoring.actual.voltageDiff.PU./;/g' |sed 's/\/PU0\/HIC0.monitoring.actual.voltageDiff.HIC./;/g' | sed 's/its_ob_bot:ITS\///g' | sed 's/its_ob_top:ITS\///g' | sed 's/\/PU0\//_/g' | sed 's/.monitoring.actual.voltageDiff.PU./;/g' > voltageDiffPU_reduced.txt

    f= "ex2.txt"   #"voltageDiffPU_reduced.txt"
    df = pd.read_csv(f, sep=';', header=None, names=( "Timestamp", "HIC", "Domain", "Value" ))
    df['Value']*=1000
    # print(df.head())

    # print("Changing timestamps")
    df['Timestamp']=df['Timestamp'].apply(epoch_to_datetime)
    # print("Changing timestamps - done.")
    # print(df.head())

    # print("Collecting HIC names")
    # cat voltageDiffPU_reduced.txt | cut -d';' -f2 | sort | uniq > HICs.txt
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
        plot_hic(hic, df)

    # parallel
    # p = Pool(10)
    # with p:
    #     p.trim_map(plot_hic, HICs)

graphtrimmer()
graphvolt()
plot_together()
# print(max(trim_map["L6_S0_HS0_M1_D1"]))
# print(min(trim_map["L6_S0_HS0_M1_D1"]))
# print(volt_map["L0_02_AVDD"])