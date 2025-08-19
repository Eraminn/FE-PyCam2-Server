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

| Command                        | Description                                                                                                                  | Example (sent string)          | Comment                                                         |
|:-------------------------------|:---------------------------------------------------------------------------------------------------------------------------- |:-------------------------------|:----------------------------------------------------------------|
||||
| **Measurement and archiving**:      |||
| CAP:SEQFET \<Prefix\> \<StorePath\> \<ETs\> \<nPics\> \<tMax\> \<LogBit\>       | FETches a SEQuence consisting of `nPics` for a list of `ETs` (ExposureTimes). The images get a File-`Prefix` and are stored into a `StorePath`. When the captureing exceeds `tMax` a warning is added to a logfile which is created when `LogBit` is enabled.                                                                                     | `CAP:SEQFET rPiImgs /media/ramdisk/Captures/ 100000:31500:10000:3150 3 3.0 1` | Captures a sequence of 12 images (4x`ETs` each 3x`nPics`) and stores them into `/media/ramdisk/Captures/` for subsequent compression/packing. |
| SRV:ARCHV \<FPath\> \<APath\> \<CmprsBit\> \<MCoreBit\> \<SuppressParentsBit\>  | Creates an archive `APath` (full path) from the given Folder `FPath`. `CmprsBit` enables compression into tar.gz (otherwise its an uncompressed tar). This can be done with multiple cores by enabling `MCoreBit`. With `SuppressParentsBit` active, the parentfolder is not included into the archive. | `SRV:ARCHV /media/ramdisk/dataPnt_0001/ /media/ramdisk/dataPnt_0001.tar 0 1 1` | Packs the contents of `/media/ramdisk/Captures/` into `/media/ramdisk/dp0001.tar` with multiple cores without the parent-folder. |
||||
| **Settings (before measurement)**:           |||
| CAM:CONF:ET \<ET_µs\>          | Adjusts the Exposuretime in `µs`. Allowed values: `100`-`100000`.                                                            | `CAM:CONF:ET 10000`            | Sets an Exposure Time of `10 ms`.                               |
| CAM:CONF:SS \<ET_µs\>          | Legacy-Support of `CAM:CONF:ET` (SS = ShutterSpeed)                                                                          | `CAM:CONF:SS 10000`            | Sets an Exposure time of `10 ms`.                               |
| CAM:CONF:FR \<FR_FPS\>         | Adjusts the FrameRate in `FPS`. Allowed values (tested): `1`-`10`. Other Sensor modes may allow FPS, but these are untested. | `CAM:CONF:FR 10`               | Sets the FrameRate to `10 FPS`.                                 |
| CAM:CONF:AG \<AG\>             | Adjusts the AnalogGain. Allowed values (tested): `1.0`-`8.0`.                                                                | `CAM:CONF:AG 3.5`              | Set an AnalogGain of `3.5`.                                     |
| CAM:CONF:AWB \<R:B\>           | Adjusts the AutoWhiteBalance. Allowed values: `0.0`-`8.0`                                                                    | `CAM:CONF:AWB 1.8:2.1`         | Sets gain for red pixels to `1.8` and blue pixels `2.1`.        |
| CAM:CONF:SCLCRP \<XY\> \<WH\>  | ScalerCrop-functionality not used, because done by SRV:BCLP. (Note: also untested!)                                          | `CAM:CONF:SCLCRP 9:12 123:456` | Creates a crop-window with a Width x Height of `123`x`456` pixel at a pixel position of X x Y of `9`x`12`(left upper corner) |
| SRV:IMG:BCLP \<[X:Y:]W:H\>     | Clips image in bayer-space after receiving it from camera. `W`x`H` respresents the target image-size around the image sensor center. However, if `X`x`Y` is given, these are used as left upper corner coordinate instead. | `SRV:IMG:BCLP 120:90:1200:900` | Clips an image with `900`x`900` pixels beginning at the starting pixel position `90`x`90`.|
| SRV:IMG:CLP \<[X:Y:]W:H\>     | Clips image in bayer-space after receiving it from camera. `W`x`H` respresents the target image-size around the image sensor center. However, if `X`x`Y` is given, these are used as left upper corner coordinate instead. | N/A | Planned for future, but not implemented yet. (Workaround: Use BCLIP with the X- and W-pixelcoordinate multiplied by `1.5`) |
| SRV:IMG:DBAY \<DebayerBit\>    | (Post-processing) The `DebayerBit` sets if the images is debayered on server-side before being saved.                        | `SRV:IMG:DBAY 0` | Deactivates server-side debayering. |
| SRV:IMG:SHRNK \<Exp\>                  | (Post-processing) Sets the pi to do pixel-binning with 2^`Exp`.                                                                            | `SRV:IMG:SHRNK 1` | Server-side pixel-binning of 2x2 pixels into 1 pixel. |
||||
| **Testing, Pathinfo and Server-Termination**: |||
| IDN?                           | Grabs information from the pi (can be used for connection test)                                                              | `IDN?`| Returns system information: `PyCam2, V1.0.0.0` |
| SRV:ECHO                       | Echoes the given message (can be used for connection test)                                                                   | `ECHO Hello World`| Returns `Hello World` |
| SRV:PATH:RDDIR?                | Returns the path where the RamDisk is mounted.                                                                               | `SRV:PATH:RDDIR?` | Returns the set path of variable `mntPnt_RAMDisk` (e.g. `/media/ramdisk/`). |
| SRV:PATH:SDDIR?                | Returns the path where SD-Card images captured (is just a shortcut, which is changed by hand in script-code (imFolderPath))  | `SRV:PATH:SDDIR?` | Returns the set path of variable `SDCardPath` (e.g. `/mnt/sdcard/`). |
| SRV:PATH:IMDIR?                | Returns the path where the images stored.                                                                                    | `SRV:PATH:IMDIR?` | Returns the set path of variable `imFolderPath` (e.g. `/media/ramdisk/Captures/`). |
| SRV:CLOSE                      | Closes the connection and shuts down the pycam-server (not the pi)                                                           | `SRV:CLOSE` | Terminates the server-instance. |

Note: All commands are (not) acknowledged by returning `nak`/`ack`.

7.) Images can be downloaded via a SCP-connection from your measurement-program asynchrone from the pi.
    This is also hardly recommended, as the images can become huge and cause may an out of RAM/Diskspace exception which crashes the script.
    If you don't want to make the effort to program a downloader, you can also try to use a bigger SD-Card and change the image-folderpath from:
    ```imFolderPath = join(mntPnt_RAMDisk, "Captures") # Path to the RAMDISK + Subfolder```
    to
    ```imFolderPath = join(SDCardPath, "Captures") # Path to the SD-Card + Subfolder```



2025 © haum



[rPiImager]:(https://www.raspberrypi.com/software/)
[rPiOS]:(https://www.raspberrypi.com/software/operating-systems/)