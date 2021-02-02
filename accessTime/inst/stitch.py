#!/usr/bin/env python
# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), an agency of the Federal Government.
# Pursuant to title 17 United States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States and
# are considered to be in the public domain. Permission to freely use, copy,
# modify, and distribute this software and its documentation without fee is
# hereby granted, provided that this notice and disclaimer of warranty
# appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER
# EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY
# WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL
# CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR
# FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT
# LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING
# OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE,
# WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER
# OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND
# WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF, OR
# USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.

import re
import subprocess
import shutil
import os
import argparse
import tempfile
import shlex

#default video and audio codecs
vc_default='libx264'
ac_default='aac'
					

class LastingDirectory(object):
	"""Written as a replacement for TemporaryDirectory where the directory remains after the object has been destroyed
	"""

	def __init__(self, dir):
		#name given by argument
		self.name=dir
		#create directory if it doesn't exist
		os.makedirs(self.name,exist_ok=True)

	def __repr__(self):
		return "<{} {!r}>".format(self.__class__.__name__, self.name)

	def __enter__(self):
		return self.name

	def __exit__(self, exc, value, tb):
		#dummy method, leave directory in place
		pass

	def cleanup(self):
		pass

class FrameStitcher:

	def __init__(self,fFold,verbosity=1):
		
		self.verbosity=verbosity
		
		#first look for ffmpeg in the path
		self.ffmpeg_path=shutil.which('ffmpeg')

		if(not self.ffmpeg_path):
			#ffmpeg not found in path, look in current directory
			self.ffmpeg_path=os.path.join('.','ffmpeg')

		try:
			cp=subprocess.run([self.ffmpeg_path,'-version'],capture_output=True)
		except FileNotFoundError:
			self.ffmpeg_path=None
			
		if(not self.ffmpeg_path):
			raise RuntimeError('ffmpeg could not be found')
			
		#could check ffmpeg version here
		
		#set default codecs
		self.v_codec=vc_default
		self.a_codec=ac_default
		
		#audio to play with curve fit frame
		self.cf_audio=''
		
		#set default input framerate
		self.in_frate=10
		
		#set default examples to play tx audio on
		self.tx_example=[]
		
		#set default extra ffmpeg options
		self.ex_opt=[]
		
		#set frame folder
		self.frameFolder=fFold
		
		#set the output directory
		self.outDir=''
				
		if(not os.path.isdir(self.frameFolder)):
			raise FileNotFoundError('\''+self.frameFolder+'\' does not exist or is not a directory.')
		#list files in frame folder
		frames=os.listdir(self.frameFolder)

		self.message('Determining frame numbers')

		self.frame_dict=dict()
		max_sect=0

		for n in frames:
			m_sect=re.search('Section(?P<num>\d+)',n)
			m_frame=re.search('Frame(?P<num>\d+)',n)
			if(m_sect and m_frame):
				max_sect=max(max_sect,int(m_sect.group('num')))
				try:
					self.frame_dict[m_sect.group(0)+'-name'].append(n)
					self.frame_dict[m_sect.group(0)+'-num'].append(int(m_frame.group('num')))
				except KeyError:
					#key does not exist, create it
					self.frame_dict[m_sect.group(0)+'-name']=[n]
					self.frame_dict[m_sect.group(0)+'-num']=[int(m_frame.group('num'))]
	
		self.sections=max_sect
		
	def generate(self,outname):

		#split extension from filename
		name,out_ext=os.path.splitext(outname)
		if(not out_ext):
			#no extension given, default to .mp4
			self.message("no extension given defaulting to .mp4")
			outname=name+".mp4"
			out_ext=".mp4"
			
		self.message('creating clips')

		if(self.outDir):
			dir_obj=LastingDirectory(self.outDir)
		else:
			dir_obj=tempfile.TemporaryDirectory(prefix='stitch')

		with dir_obj as temp_dir:
		
			clipfile=os.path.join(temp_dir,'clipList.txt')

			with open(clipfile,'w') as f:
				
				#name for tx frame and audio
				tx_fname=os.path.join(self.frameFolder,'Transmit_frame.png')
				tx_audio=os.path.join(self.frameFolder,'Transmit.wav')
				#if we have a frame and a clip, play Tx audio at the begining
				if(os.path.isfile(tx_fname) and os.path.isfile(tx_audio)):
					self.message(f"\tGenerating transmit section")
					out_name=os.path.join(temp_dir,f"Transmit_section{out_ext}")
					#create an end section with a static frame
					self.ffmpeg_run(['-i',tx_audio,'-loop','1','-i',tx_fname,\
						'-filter:v','fps=fps=30','-vb','10M','-shortest','-ac','2','-vcodec',self.v_codec,'-acodec',self.a_codec]+self.ex_opt+[out_name])
					f.write(f"file \'{out_name}\'\n")
			
				for sect in range(1,self.sections+1):
					self.message(f"\tGenerating clip {sect}")
					if((str(sect)+'-name') in self.frame_dict):
						in_name=os.path.join(self.frameFolder,f"Section{sect:02}_Frame%03d.png")
						out_name=os.path.join(temp_dir,f"Section{sect:02}{out_ext}")
						self.ffmpeg_run(['-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-framerate',self.in_frate,'-i',in_name,\
							'-filter:v','fps=fps=30','-vcodec',self.v_codec,'-acodec',self.a_codec,'-vb','10M','-shortest']+self.ex_opt+[out_name])
						f.write(f"file \'{out_name}\'\n")
					
					in_name=os.path.join(self.frameFolder,f"Section{sect:02}_Example.png")
					audio_name=os.path.join(self.frameFolder,f"receive_example{sect:02}.wav")
					if( os.path.isfile(in_name) and os.path.isfile(audio_name)):
						self.message(f"\tGenerating playback clip {sect}")
						out_name=os.path.join(temp_dir,f"Section{sect:02}_example{out_ext}")
						if(sect in self.tx_example):
							audio_temp=os.path.join(temp_dir,'audio_temp.wav')
							self.message('Combining audio files')
							#make temporary audio file
							self.ffmpeg_run(['-f','lavfi','-i','anullsrc=r=48000:cl=mono','-i',audio_name,'-i',tx_audio,\
								'-filter_complex','[2:a][0:a]concat=n=2:v=0:a=1[txa];[1:a][txa]join=inputs=2:channel_layout=stereo[a]','-map','[a]','-shortest',audio_temp])
							audio_args=['-i',audio_temp]
						else:
							audio_args=['-i',audio_name,'-ac','2']
						self.ffmpeg_run(['-loop','1','-i',in_name]+audio_args+\
							['-filter:v','fps=fps=30','-vcodec',self.v_codec,'-acodec',self.a_codec,'-vb','10M','-shortest']+self.ex_opt+[out_name])
						f.write(f"file \'{out_name}\'\n")
					
				self.message(f"\tGenerating end section")
				frame_nums=self.frame_dict[f"Section{self.sections:02}-num"]
				frame_names=self.frame_dict[f"Section{self.sections:02}-name"]
				max_frame_idx=frame_nums.index(max(frame_nums))
				in_name=os.path.join(self.frameFolder,frame_names[max_frame_idx])
				
				#use curve fit frame for end
				#TODO: do some cool animation overlay??
				in_name=os.path.join(self.frameFolder,'curve_fit.png')
				out_name=os.path.join(temp_dir,f"Section{self.sections+1:02}{out_ext}")
				if(self.cf_audio):
					audio_args=['-i',self.cf_audio]
				else:
					audio_args=['-f','lavfi','-i','anullsrc=r=48000:cl=mono']
				#create an end section with a static frame
				self.ffmpeg_run(audio_args+['-framerate','0.5','-i',in_name,\
					'-filter:v','fps=fps=30','-vb','10M','-shortest','-ac','2','-vcodec',self.v_codec,'-acodec',self.a_codec]+self.ex_opt+[out_name])
				f.write(f"file \'{out_name}\'\n")

			self.ffmpeg_run(['-safe','0','-f','concat','-i',clipfile,'-c','copy',outname])
	
	def powerPoint(self):
		#set codecs
		self.v_codec='libx264'
		self.a_codec='aac'
		
		#set h.264 profile and pixel format
		self.ex_opt+=['-profile:v','baseline','-pix_fmt','yuv420p']

	def message(self,mesg,level=0):
		if(level<self.verbosity):
			print(mesg,flush=True)

	def ffmpeg_run(self,args):
		#add ffmpeg path to call
		#also add -y to always say yes
		args=[self.ffmpeg_path,'-y']+args
		self.message(' '.join(args),level=1)
		cp=subprocess.run(args,capture_output=True)
		if(cp.returncode != 0):
			#get message from ffmpeg
			err_msg=cp.stderr
			#decode message to string
			err_msg=err_msg.decode('ascii')
			#print error message
			self.message(err_msg,level=-1)
			raise RuntimeError('Error ffmpeg was not successful')
		#get message from ffmpeg
		out_msg=cp.stderr
		#decode message to string
		out_msg=out_msg.decode('ascii')
		#print message with verbosity level of 2
		self.message(out_msg,level=2)

#check if we are the top level script
if __name__== "__main__":

	parser = argparse.ArgumentParser(description='Stitch frames into video')
	parser.add_argument('frameFolder', type=str,metavar='f',
						help='Folder name for animation frames')
						
	parser.add_argument('-f','--input-framerate', type=str,metavar='f',dest='in_frate',default="10",
						help='Frame rate to show input frames at')
						
	parser.add_argument('-o','--output',type=str,metavar='f',dest='out',default='output.mp4',
						help='Output filename');
						
	parser.add_argument('--curve-fit-audio',type=str,metavar='a',dest='cf_audio',default='',
						help='Audio to play when the curve fit is shown');
						
	parser.add_argument('--video-codec',type=str,metavar='vc',dest='v_codec',default=vc_default,
						help='Video codec to use');
						
	parser.add_argument('--audio-codec',type=str,metavar='ac',dest='a_codec',default=ac_default,
						help='Audio codec to use');
						
	parser.add_argument('--simultaneous-tx',action='append',type=int,metavar='sec',dest='smtx',default=[],
						help='Play the tx audio with the Rx audio in the section sec');
						
	parser.add_argument('-v','--verbose',action='count',default=1,dest='verbosity',
						help='print more information to stdout')
						
	parser.add_argument('-q','--quiet',action='store_const',const=0,dest='verbosity',
						help='don\'t print anything to stdout')
						
	parser.add_argument('-e','--extra-option',action='append',dest='ex_op',type=str,metavar='op',
						help='extra options to pass to ffmpeg')
						
	parser.add_argument('--powerPoint',action='store_true',dest='pp',
						help='Create a viedo for import into PowerPoint')
						
	parser.add_argument('--output-directory',type=str,metavar='d',dest='outDir',default='',
						help='Directory to save intermediate files to')

	args = parser.parse_args()

	#create a new FrameStitcher object to use
	stitcher=FrameStitcher(args.frameFolder,args.verbosity)
		
	#check if blank v_codec was given
	if(args.v_codec):
		stitcher.v_codec=args.v_codec
		
	#check if blank a_codec was given
	if(args.a_codec):
		stitcher.a_codec=args.a_codec
		
	#set options from args
	stitcher.cf_audio=args.cf_audio
	stitcher.in_frate=args.in_frate
	stitcher.tx_example=args.smtx
	stitcher.outDir=args.outDir
	
	if(args.pp):
		stitcher.powerPoint()
	
	#check if extra options were given
	if(args.ex_op):
		#add extra options
		for opt in args.ex_op:
			#split option so it can be added to the list
			stitcher.ex_opt+=shlex.split(opt)
			
	#generate video
	stitcher.generate(args.out)
