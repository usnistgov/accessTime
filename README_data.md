Background
===============================================================================
Access time generally describes the time associated with the establishment of a talk pathupon user request to speak and has been identified as a key component of Quality of Experience (QoE) in communications. NIST’s Public Safety Communications Research (PSCR) division developed a method to measure and quantify the access time of any Push To Talk (PTT) communication system. PSCR presents a broad definition of access time that is applicable across multiple PTT technologies. The measurement system builds off of the following definitions: 
* **End-to-end access time** is the total amount of time from when a transmitting user first presses PTT until a receiving user hears intelligible audio. It consists of two components: mouth-to-ear latency and access delay.
* **Mouth-to-ear latency** characterizes the time between speech being input into one device and its output through another.
* **Access delay** is minimum length of time a user must wait between pressing a PTT button and starting to speak to ensure that the start of the message is not lost.

A speech intelligibility-based access delay measurement system is introduced.  This system measures the intelligibility of a target word based on when PTT was pushed within a pre-defined message.  It relies only on speech going into and coming out of a voice communications system and PTT timing, so it functions as a fair platform to compare different technologies.  Example measurements were performed across the following Land Mobile Radio (LMR) technologies:  analog direct and conventional modes,and digital Project 25 (P25) direct and trunked (both phase 1 and phase 2) modes.

This data was created in support of NISTIR 8275, Mission Critical Voice QoE Access Time Measurement Methods, available free of charge from https://doi.org/10.6028/NIST.IR.8275

Structure of the Data
===============================================================================
The data is stored with the following structure:
- **Audio Clips**
  - Folder containing audio files used in measurement
  - Audio files are stored as wav files
  - Cut point files are associated with each audio file. These detail at which sample the first playthrough of the word under test,P1, and and the second playthrough, P2, start. The sampling rate for the audio files is 48 KHz.
- **Measurements** 
  - Folder containing folders for each example measurement performed.
  - Each subfolder has four csv files, one for each speaker word pair used for the testing.
  - CSV files have the following structure:
    - AudioFiles = 'path/to/audiofilename.wav'
    - fs = 48000
    - HEADER: PTT_time,PTT_start,ptt_st_dly,P1_Int,P2_Int,m2e_latency,underRun,overRun
    - Data


Obtaining the Data
===============================================================================
The data is available to download as a both a zip file as well as in the github repository for the access time measurement system code.

Data available at: 
* zip: https://doi.org/10.18434/M32083
* github repository: [accessTime/inst/extdata](https://github.com/usnistgov/accessTime/tree/master/accessTime/inst/extdata). 
  * The data is also available in the accessTime R package, with additional documentation

Code available at: https://github.com/usnistgov/accessTime

Paper available at https://doi.org/10.6028/NIST.IR.8275

System Requirements and Support
===============================================================================
- Software to view csv files
 - Software to process/listen to audio files
 
For more information or assistance on access time measurements please 
contact:

Tim Thompson\
Public Safety Communications Research Division\
National Institute of Standards and Technology\
325 Broadway\
Boulder, CO 80305\
(303) 497-6613; tim.thompson@nist.gov


DISCLAIMER
=======================================================================

This data was developed by employees of the National Institute of Standards and Technology (NIST), an agency of the Federal Government. Pursuant to title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States and are considered to be in the public domain.

The data is provided by NIST as a public service and is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST does not warrant or make any representations regarding the use of the data or the results thereof, including but not limited to the correctness, accuracy, reliability or usefulness of the data. NIST SHALL NOT BE LIABLE AND YOU HEREBY RELEASE NIST FROM LIABILITY FOR ANY INDIRECT, CONSEQUENTIAL, SPECIAL, OR INCIDENTAL DAMAGES (INCLUDING DAMAGES FOR LOSS OF BUSINESS PROFITS, BUSINESS INTERRUPTION, LOSS OF BUSINESS INFORMATION, AND THE LIKE), WHETHER ARISING IN TORT, CONTRACT, OR OTHERWISE, ARISING FROM OR RELATING TO THE DATA (OR THE USE OF OR INABILITY TO USE THIS DATA), EVEN IF NIST HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

To the extent that NIST may hold copyright in countries other than the United States, you are hereby granted the non-exclusive irrevocable and unconditional right to print, publish, prepare derivative works and distribute the NIST data, in any medium, or authorize others to do so on your behalf, on a royalty-free basis throughout the world.

You may improve, modify, and create derivative works of the data or any portion of the data, and you may copy and distribute such modifications or works. Modified works should carry a notice stating that you changed the data and should note the date and nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the source of the data: Data citation recommendations are provided below.

Permission to use this data is contingent upon your acceptance of the terms of this agreement and upon your providing appropriate acknowledgments of NIST's creation of the data.
