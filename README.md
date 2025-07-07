# FE-PyCam2

That projects represents a python-netsocket (server) to manage a Raspberry Pi HQ-Camera based on libcamera (picamera2) as scientific imaging sensor for the measurement of field emission electron sources.

Note: Depending on your settings and setup, it is recommended (for security reasons) to run the server only in your local network after the pi is set up.


# Setup
## Hardware
The scripts are developed and tested on a Raspberry Pi 4 Model B (8GB).
The following setup assumes you have access to the internet with the pi (during the setup), e.g. using a USB-Ethernet adapter with forwarded internet connection.

## Underlaying system and libraries
1.) Operating System

Install Raspbian OS 11 x64 Lite (Debian Bullseye, no desktop) or higher on a SD-Card. Newer versions (Rasperry Pi OS 12, Debian Bookworm) in principle works, but is not fully tested yet. For deployment, you can use the [Raspberry Pi Imager][rPiImager] (easiest way) or download the [sd-card-image][rPiOS] and use your favourite disk-imager software.


2.) Picamera2 (python library for libcamera)

As we are using the system headless, the GUI-package installations are skipped.

First, install the necessary dependencies by running the following lines in the shell:
```
sudo apt install -y python3-libcamera python3-kms++
sudo apt install -y python3-prctl libatlas-base-dev ffmpeg python3-pip
pip3 install numpy --upgrade (on bookworm you may need to run ``sudo apt install python3-numpy`` for global installation)
```

Afterwards you can run
```pip3 install picamera2``` (pip)
or
```sudo apt install -y python3-picamera2``` (apt-install)
to install the python-library for libcamera.


3.) Additional Software

Some features of picamera2 can use parts of the following packages:
```
sudo apt install -y python3-opencv
sudo apt install -y opencv-data
pip3 install tflite-runtime (if faced problems, please visit https://stackoverflow.com/questions/74968761/pip3-cant-download-the-latest-tflite-runtime)
sudo apt install -y ffmpeg
```


## Get PyCam2 to work
1.) Disable legacy camera stack by running ```sudo raspi-config```, enter ```interface options``` and make sure, that the ```legacy camera stack``` is ```disabled```.

2.) Make sure, git is installed by running ```sudo apt install git -y```.

3.) Clone the repository content directly in to the pis home-folder (rPiHQCamServer2.py in /home/pi) by running
```bash
cd ~
git clone https://github.com/Dephrilibrium/FE-PyCam2-Server.git
mv FE-PyCam2-Server/* FE-PyCam2-Server/.??* .
rmdir FE-PyCam2-Server/
```

You should now be able to create gray test-images by running:
```./Pictures/stdShot2.sh <Testimage-Filename: String> <AnalogueGain: 1.0-8.0> <ExposureTime_us: 100-100000>```
If you are using VS-Code for the remote-connection, you can use the file-explorer to directly have a look on the image which is stored in your current ```pwd```.

4.) You can adjust some startup-options by opening and modify the rPiHQCamServer2.py, e.g.: ```srvr_ClipWinBayer```: Adjusts the image size in bayer-space before any post-processing or saving.

5.) Run the script by hand (or start it automatically via a ssh-connection remote controlled) and connect with your measurement-programm to the server via the RasPis IP or DNS and port (default: ```5060```).

6.) Query commands (Details in the code-documentation of the functions):

| Command           | Description                                                                                                                 |
|:------------------|:----------------------------------------------------------------------------------------------------------------------------|
| CAM:CONF:ET       | Adjusts the Exposuretime                                                                                                    |
| CAM:CONF:SS       | Adjusts the ShutterSpeed. (Legacy-Support of CAM:CONF:ET)                                                                  |
| CAM:CONF:FR       | Adjusts the FrameRate                                                                                                       |
| CAM:CONF:AG       | Adjusts the AnalogGain                                                                                                      |
| CAM:CONF:AWB      | Adjusts the AutoWhiteBalance                                                                                                |
| CAM:CONF:SCLCRP   | ScalerCrop-functionality not used, because done by SRV:BCLP                                                                 |
| CAP:SEQFET        | FETches a SEQuence of images; Timeout not used at the moment                                                                |
| SRV:ARCHV         | Archvies the given folder to a tar or tar.gz                                                                                |
| SRV:IMG:BCLP      | Sets the image size. Clipping is done in bayer-space directly after receiving from camera.                                  |
| SRV:IMG:DBAY      | (Post-processing) Sets if the pi is debayering the images before saving                                                     |
| SRV:IMG:SHRNK     | (Post-processing) Sets the pi to do pixel-binning                                                                           |
| IDN?              | Grabs information from the pi (can be used for connection test)                                                             |
| SRV:ECHO          | Echoes the given message (can be used for connection test)                                                                  |
| SRV:PATH:RDDIR?   | Returns the path where the RamDisk is mounted.                                                                              |
| SRV:PATH:SDDIR?   | Returns the path where SD-Card images captured (is just a shortcut, which is changed by hand in script-code (imFolderPath)) |
| SRV:PATH:IMDIR?   | Returns the path where the images stored.                                                                                   |
| SRV:CLOSE         | Closes the connection and shuts down the pycam-server (not the pi)                                                          |

7.) Images can be downloaded via a SCP-connection from your measurement-program asynchrone from the pi.
    This is also hardly recommended, as the images can become huge and cause may an out of RAM/Diskspace exception which crashes the script.
    If you don't want to make the effort to program a downloader, you can also try to use a bigger SD-Card and change the image-folderpath from:
    ```imFolderPath = join(mntPnt_RAMDisk, "Captures") # Path to the RAMDISK + Subfolder```
    to
    ```imFolderPath = join(SDCardPath, "Captures") # Path to the SD-Card + Subfolder```



2025 © haum



[rPiImager]:(https://www.raspberrypi.com/software/)
[rPiOS]:(https://www.raspberrypi.com/software/operating-systems/)