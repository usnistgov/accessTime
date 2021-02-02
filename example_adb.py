#!/usr/bin/env python

import subprocess
import argparse
import warnings
import os
import shutil
import re

#first look for adb in the path
adb_path=shutil.which('adb')

if(not adb_path):
	#adb not found in path, look in appdata might be only windows
	adb_path=os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")
#TODO : modify with app name of app
app_name='your.app.name.here'
	
	
def run_adb(cmd,dev=None):
	if(dev):
		adb_cmd=[adb_path,'-s',dev]
	else:
		adb_cmd=[adb_path]
	cp=subprocess.run(adb_cmd+cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	for line in cp.stderr.decode('ascii').splitlines():
		line=line.strip()
		if(line.startswith('error: ')):
			raise RuntimeError('adb returned \''+line+'\'')
		elif(line):
			warnings.warn('adb returned \''+line+'\'',RuntimeWarning);
	
	return cp.stdout
	
def  list():
	#run the adb list command to get a list of devices
	cmd_out=run_adb(['devices'])
	
	lines=cmd_out.decode('ascii').splitlines()
	
	if(lines[0].strip() != 'List of devices attached'):
		raise RuntimeError('Unknown output from adb devices')
	
	devices=[]
	
	for l in lines[1:]:
		words=l.split()		
		if(words and words[-1]=='device'):
			devices.append(words[0])
	
	return devices	
	
def start_app(dev=None):
	run_adb(['shell','monkey','-p',app_name,'1'],dev)
	touch(550,855,dev)

def scr_state(dev=None):
	sd=run_adb(['shell','dumpsys','power'],dev)
	sd=sd.decode('ascii');

	mw=re.search(r"mWakefulness=(?P<state>\w+)",sd)
	return mw.groups('state')[0]
	#ml=re.search(r"mHoldingWakeLockSuspendBlocker=(\w+)",sd)
	#print(ml)
	
def batt_state(dev=None):
	bstats=run_adb(['shell','dumpsys','battery'],dev)
	bstats=bstats.decode('ascii');
	print(bstats)


def unlock(dev=None):
	#Wakes up the device. Behaves somewhat like KEYCODE_POWER but it has no effect if the device is already awake.
	run_adb(['shell','input','keyevent','KEYCODE_WAKEUP'],dev)
	#Swipe UP, brings up pin entry
	run_adb(['shell','input','touchscreen','swipe','930','880','930','380'],dev) 
	#input pin
	#TODO : insert your pin here
	run_adb(['shell','input','text','####'],dev)
	#Press enter to enter pin
	run_adb(['shell','input','keyevent','66'],dev)
	
def stop_app(dev=None):
	run_adb(['shell','am','force-stop',app_name],dev)

def screenshot(dev=None):
	if(dev):
		adb_cmd=[adb_path,'-s',dev]
	else:
		adb_cmd=[adb_path]
	#call screencap using adb and capture output
	img_out=run_adb(['shell','screencap','-p'],dev)
	#return image bytes. fix newlines
	return img_out.replace(b'\r\n', b'\n')
	
def touch(x,y,dev=None):
	run_adb(['shell','input','tap',str(x),str(y)],dev)

def save_scr(name,dat):
	with open(name,'wb') as imgf:
		imgf.write(dat)

def restart_all():
	devs=list()
	
	print('Devices found : '+str(devs))
	
	for dev in devs:
		print(dev)

		batt_state(dev)

		unlock(dev)
		
		stop_app(dev)
		start_app(dev)
		scr=screenshot(dev)
		save_scr('tmp_'+dev+'.png',scr)
		
if __name__== "__main__":	
	parser = argparse.ArgumentParser(description='restart ')
	
	args = parser.parse_args()
	
	restart_all()