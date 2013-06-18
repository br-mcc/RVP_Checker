#!/usr/bin/python

# Exception handling
import sys
# Converting days/months/years
import math
# Handling filesystem paths, files, and directories
import glob
import os
import subprocess
# GUI
from Tkinter import *
# GUI directory browser
from tkFileDialog import askdirectory

def updateStatus(msg):
    progress.set(msg)
    root.mainloop()

def loopConfig(time_res, path):

    base_path = path
    output_file = path+'RelativeViewPeriods.txt'
    
    try:
        o = open(output_file, 'w+')
    except IOError, (errno, strerror):
        # "Config" directory not set.
        if base_path == "/":
            errMessage = 'No Config directory specified.  Please provide a path to a valid configuration directory.'
            progress.set(errMessage)
            print errMessage
        # Can't write output file.  Check permissions.
        else:
            print "I/O Error(%s): %s"% (errno, strerror)
            print "HINTS: Does your user have write permission for %s specified?" % (base_path)
        
    else:
        file_directories = ['DisplayConfigFiles/','ModuleConfigFiles/','PiServiceConfig/','RegionConfigFiles/','SystemConfigFiles/']
        for directory in file_directories:
            if "ModuleConfigFiles" in directory:
                for conf_file in glob.glob(base_path+directory+'*/*.xml'):
                    print conf_file
                    reading = "Reading " + conf_file
                    updateStatus(reading)
                    f = open(conf_file, 'r')
                    check_RVP(f,o,conf_file,time_res)
            else:
                for conf_file in glob.glob(base_path+directory+'*.xml'):
                    reading = "Reading " + conf_file
                    progress.set(reading)
                    f = open(conf_file, 'r')
                    check_RVP(f,o,conf_file,time_res)
        o.close()

def runScript():

    global config_path
    config_path = path.get()+'/'
    
    print "Path: ", config_path
    time_Resolution = int(time.get())
    
    progress.set("Running . . .")
    
    # Run the actual script.
    loopConfig(time_Resolution, config_path)
    
    progress.set("Complete.  Output written to RelativeViewPeriods.txt")
    root.mainloop()
    
def getPath():
    
    global config_path
    config_path = askdirectory(title="Browse Folders",initialdir="/awips/chps_share")
    path.set(config_path)


def check_RVP(input_file,output_file,file_path,time_res):

    file = input_file
    out = output_file
    search_STR = 'relativeViewPeriod'
    line_count = 0
    count = 0
    flag = 0

    # PER FILE
    for line in file:   
        # PER LINE
        line_count += 1
        parameterID_str = '<parameterId>'
        tsType_str = '<timeSeriesType>'
            
        # Grab other parameters for some context on the offending RVPs.
        if parameterID_str in line:
            parameterID = line.strip()
        if tsType_str in line:
            tsType = line.strip()
        if search_STR in line:
            # If none of the timeseries is selected in the GUI, default to find all timeseries.
            if histVar.get() == 0 and simVar.get() == 0:
                pass
            # If historical isn't selected, skip to next line.
            elif "historical" in tsType and histVar.get() == 0:
                continue
            # If simulated isn't selected, skip to next line.
            elif "forecasting" in tsType and simVar.get() == 0:
                continue
                
            start_str = ''
            end_str = ''
            unit = ''
            line = line.strip()
                
            # Split the line between each attribute and assign to array "tag".
            tag = line.rsplit(" ")
            # Determine start and end times.  They can vary on which position in the index they are found.
            for atr in tag:
                if "start=" in atr:
                    start_str = atr
                elif "end=" in atr:
                    end_str = atr
                elif "unit=" in atr:
                    unit = atr
                        
            # Try to parse the start and end times.  If either doesn't exist, skip via exception handler.
            try:
                start = start_str.rsplit("=",1)[1].split('"')[1]
                end = end_str.rsplit("=",1)[1].split('"')[1]
                time = int(end) - int(start)

                # Convert everything to days.  The exception being if ">1 year" selected in GUI.  Then do years.
                if "year" in unit:
                    mult = 365
                elif "month" in unit:
                    mult = 30
                elif "week" in unit:
                    mult = 7
                elif "day" in unit:
                    mult = 1
                elif "hour" in unit:
                    mult = 1.0/24.0
                elif "minute" in unit:
                    mult = (1.0/24.0)/60.0
                RVP_days = time * mult

                ''' If the RVP is more than the day threshold, and the threshold is no less than 100,
                    print out detailed information on matching lines. Else, print out only a summary
                    in order to limit "flooding" of the terminal window. ''' 
                if RVP_days > time_res:
                    count += 1
                    if flag == 0:
                        print >> out, "======================"
                        print >> out, ""
                        print >> out, "filename: ", file_path
                        flag = 1
                    if 365 > time_res >= 100:
                        print >> out, "Line %d: %s" % (line_count,line)
                        print >> out, "     RVP = %d day(s)" % (RVP_days)
                        print >> out, "     ParameterID = ", parameterID
                        print >> out, "     TimeSeriesType: ", tsType
                    elif time_res >= 365:
                        RVP_years = RVP_days / 365.0
                        print >> out, "Line %d: %s" % (line_count,line)
                        print >> out, "     RVP = %d year(s)" % (RVP_years)
                        print >> out, "     ParameterID = ", parameterID
                        print >> out, "     TimeSeriesType: ", tsType

            
            
            except:
                if len(start_str)!=0 and len(end_str)!=0 and len(unit)!=0:
                    print "Unexpected error:", tag
                    print start_str, start
                    print end_str, end
                    print unit
                    print sys.exc_info()[0]
            
            

    if time_res < 100 and flag == 1:
        print >> out, "%d occurrence(s) of RVPs configured greater than %d days." % (count, time_res)
    
    
    
root = Tk()
time = IntVar()
path = StringVar()
progress = StringVar()

textBoxFrame = Frame(root).pack()

radioFrame = Frame(root).pack()

# Type in config path and set as path for analysis.
T1 = Label(textBoxFrame, text = "Enter the path of the 'Config' directory: (../Config)").pack( anchor = W )
E1 = Entry(textBoxFrame, width=50, textvariable=path).pack(side=TOP, padx=20, pady=10, anchor = W )
# Select Config directory path via browser.
T2 = Label(textBoxFrame, text = "Or browse for the directory:").pack( anchor = W )
browseFilesButton = Button(textBoxFrame, text="Browse Folders", command=getPath).pack( anchor = W, padx=20, pady=10 )

separator1 = Frame(height=2, bd=1, relief=SUNKEN).pack(fill=X, padx=5, pady=5)

# Choose resolution of response.  Execute script upon click.
T2 = Label(radioFrame,text = "Show locations with an RVP configured > than:").pack( anchor = W )
R30 = Radiobutton(radioFrame, text=" > 30 days", variable=time, value=30).pack( anchor = W, padx=20 )
R100 = Radiobutton(radioFrame, text=" > 100 days", variable=time, value=100).pack( anchor = W, padx=20 )
R1 = Radiobutton(radioFrame, text=" > 1 year", variable=time, value=365).pack( anchor = W, padx=20 )
R50 = Radiobutton(radioFrame, text=" > 50 years", variable=time, value=18250).pack( anchor = W, padx=20 )

# For filtering output
extraOptionsFrame = LabelFrame(root, text="Filter your output:", bd = 2).pack(fill="both",expand="yes", pady= 5)
extraOptionsLabel = Label(extraOptionsFrame, text="Refine your search")
tsChooseLabel = Label(extraOptionsFrame, text="Which timeseries type do you wish to inspect? (Select all which apply)").pack( anchor = W)
histVar = IntVar()
HistoricalBox = Checkbutton(extraOptionsFrame, text="Historical Timeseries", variable=histVar, onvalue=1, offvalue=0).pack( anchor = W, padx=20 )
simVar = IntVar()
SimulatedBox = Checkbutton(extraOptionsFrame, text="Simulated Timeseries", variable=simVar, onvalue=1, offvalue=0).pack( anchor = W, padx=20 )

separator2 = Frame(height=2, bd=1, relief=SUNKEN).pack(fill=X, padx=5, pady=5)

bottomFrame = Frame(root).pack( side = BOTTOM )
Run = Button(bottomFrame, text = 'Run', command=runScript).pack( padx=10,side = LEFT )
Exit = Button(bottomFrame, text = 'Exit', command=root.quit).pack( padx=10,pady=15, side = LEFT )
ProgressLabel = Label(root, textvariable=progress).pack(padx=10, pady=15, side = LEFT)
progress.set("Idle")

root.mainloop()
