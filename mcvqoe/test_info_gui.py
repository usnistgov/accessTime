import datetime
import git
import os
import scipy.io.wavfile
import scipy.signal
import sys

from audio_player import AudioPlayer
from fractions import Fraction
from misc import audio_float
from radio_interface import RadioInterface
from tkinter import scrolledtext

import numpy as np
import sounddevice as sd
import tkinter as tk

def check_audio(audio_file="test.wav"):
    """Perform a single test to check audio equipment. Auto deletes recorded file"""

    if os.path.exists("temp0.wav"):
        os.remove("temp0.wav")
    
    # Initialize audio_player object
    ap = AudioPlayer()
    
    # Initialize variables
    fs = 48e3
        
    # Gather audio data in numpy array and audio samplerate
    fs_file, audio_dat = scipy.io.wavfile.read(audio_file)
    # Calculate resample factors
    rs_factor = Fraction(fs/fs_file)
    # Convert to float sound array
    audio_dat = audio_float(audio_dat)
    # Resample audio
    audio = scipy.signal.resample_poly(audio_dat, rs_factor.numerator, rs_factor.denominator)
    
    with RadioInterface("") as ri:
        ri.led(1, True)
        ri.ptt(True)
        temp_file = ap.play_rec_mono(audio, filename='temp0.wav')
        ri.ptt(False)
        os.remove(temp_file)
    
def exit_prog():
    """Exit if user presses 'cancel' in Tkinter prompt."""
    
    print(f"\n\tExited by user")
    sys.exit(1)

def coll_user_vars():
    """Collect user input from Tkinter input window."""
    
    global test_type
    global tran_dev
    global rec_dev
    global system
    global test_loc
    global test_notes
    
    test_type = e1.get()
    tran_dev = e2.get()
    rec_dev = e3.get()
    system = e4.get()
    test_loc = e5.get()
    test_notes = e6.get(1.0, tk.END)
    
    # Delete window 
    root.destroy()

def collect_post():
    """Collect user's post-test notes."""
    
    global post_test
    
    post_test = entry.get(1.0, tk.END)
    
    # Delete window
    root.destroy()

def post_test():
    """
    Give user post test GUI and return input as dictionary item.
    
    ...
    
    Returns
    -------
    dict
        The "Post Test Notes" dictionary entry.
    """
    #--------------------[Obtain Post Test Notes From User]--------------------
    
    # Window creation
    global root
    root = tk.Tk()
    root.title("Test Information")
    root.after(1, lambda: root.focus_force())
    
    # Prevent error if user exits
    root.protocol("WM_DELETE_WINDOW", collect_post)
    
    # Pre-test notes prompt
    label = tk.Label(root, text="Please enter post-test notes")
    label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
    global entry
    entry = scrolledtext.ScrolledText(root, bd=2, width=100, height=15)
    entry.grid(row=1, column=0, padx=10, pady=5)
    entry.focus()
    
    # 'Submit' and 'Cancel' buttons
    button_frame = tk.Frame(root)
    button_frame.grid(row=2, column=0, sticky=tk.E)
    
    button = tk.Button(button_frame, text="Submit", command=collect_post)
    button.grid(row=0, column=0, padx=10, pady=10)
    
    button = tk.Button(button_frame, text="Cancel", command=exit_prog)
    button.grid(row=0, column=1, padx=10, pady=10)
    
    # Run Tkinter window
    root.mainloop()
    
    return {"Post Test Notes": post_test}
        
def pretest(outdir=""):
    """
    Provide user pretest GUI and return input as dictionary.
    
    ...
    
    Parameters
    ----------
    outdir : str
        The directory to write test-type.txt to.
    
    Returns
    -------
    dict
        The user entry in dictionary form.
    """
    
    # Get start time, deleting microseconds
    time_n_date = datetime.datetime.now().replace(microsecond=0)
    
    #-----------------------[Obtain Previous Test Notes]-----------------------
    
    try:
        with open("test-type.txt", 'r') as prev_test:
            testing = prev_test.readline().split('"')[1]
            transmit = prev_test.readline().split('"')[1]
            receive = prev_test.readline().split('"')[1]
            systems = prev_test.readline().split('"')[1]
            locate = prev_test.readline().split('"')[1]
    except FileNotFoundError:
        testing = ""
        transmit = ""
        receive = ""
        systems = ""
        locate = ""
        
    #--------------------[Get Test Info and Notes From User]-------------------

    # Window creation
    global root
    root = tk.Tk()
    root.title("Test Information")
    
    # End the program if the window is exited out
    root.protocol("WM_DELETE_WINDOW", exit_prog)
    
    # Test type prompt
    l1 = tk.Label(root, text="Test Type")
    l1.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
    global e1
    e1 = tk.Entry(root, bd=2, width=50)
    e1.insert(tk.END, '')
    e1.insert(0, testing)
    e1.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
    e1.focus()
    
    # Transmit device prompt
    l2 = tk.Label(root, text="Transmit Device")
    l2.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
    global e2
    e2 = tk.Entry(root, bd=2)
    e2.insert(0, transmit)
    e2.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
    
    # Receive device prompt
    l3 = tk.Label(root, text="Receive Device")
    l3.grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
    global e3
    e3 = tk.Entry(root, bd=2)
    e3.insert(0, receive)
    e3.grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
    
    # System prompt
    l4 = tk.Label(root, text="System")
    l4.grid(row=6, column=0, padx=10, pady=5, sticky=tk.W)
    global e4
    e4 = tk.Entry(root, bd=2, width=60)
    e4.insert(0, systems)
    e4.grid(row=7, column=0, padx=10, pady=5, sticky=tk.W)
    
    # Test location prompt
    l5 = tk.Label(root, text="Test Location")
    l5.grid(row=8, column=0, padx=10, pady=5, sticky=tk.W)
    global e5
    e5 = tk.Entry(root, bd=2, width=100)
    e5.insert(0, locate)
    e5.grid(row=9, column=0, padx=10, pady=5, sticky=tk.W)
    
    # Pre-test notes prompt
    l6 = tk.Label(root, text="Please enter notes on pre-test conditions")
    l6.grid(row=10, column=0, padx=10, pady=5, sticky=tk.W)
    global e6
    e6 = scrolledtext.ScrolledText(root, bd=2, width=100, height=15)
    e6.grid(row=11, column=0, padx=10, pady=5, sticky=tk.W)
    
    # 'Submit', 'Test', and 'Cancel' buttons
    button_frame = tk.Frame(root)
    button_frame.grid(row=12, column=1, sticky=tk.E)
    
    exit_frame = tk.Frame(root)
    exit_frame.grid(row=12, column=0, sticky=tk.W)
    
    button = tk.Button(exit_frame, text="Check Audio", command=check_audio)
    button.grid(row=0, column=0, padx=10, pady=10)
    
    button = tk.Button(button_frame, text="Submit", command=coll_user_vars)
    button.grid(row=0, column=0, padx=10, pady=10)
    
    button = tk.Button(button_frame, text="Cancel", command=exit_prog)
    button.grid(row=0, column=1, padx=10, pady=10)
    
    # Run Tkinter window
    root.mainloop()
    
    #----------------------------[Get Git Hash]--------------------------------

    sha = ""
    try:
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
    except git.exc.InvalidGitRepositoryError:
        sha = "No Git Hash Found"
    
    #--------------------[Print Test Type and Test Notes]----------------------
    
    # Print info to screen
    print('\nTest type: %s\n' % test_type, flush=True)
    print('Pre test notes:\n%s' % test_notes, flush=True)
    
    # Write info to .txt file
    test_dir = os.path.join(outdir,'test-type.txt')
    with open(test_dir, 'w') as file:
        file.write('Test Type : "%s"\n' % test_type)
        file.write('Tx Device : "%s"\n' % tran_dev)
        file.write('Rx Device : "%s"\n' % rec_dev)
        file.write('System    : "%s"\n' % system)
        file.write('Test Loc  : "%s"\n' % test_loc)
        
    #--------------------[Place Everything Into Dictionary]--------------------
    
    test_info = {"Test Type": test_type, "Tx Device": tran_dev,
                 "Rx Device": rec_dev, "System": system,
                 "Test Loc": test_loc, "Pre Test Notes": test_notes,
                 "Git Hash": sha, "Time": time_n_date}
    
    return test_info