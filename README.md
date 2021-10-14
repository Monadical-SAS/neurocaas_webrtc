# NEUROCAAS WEBRTC

## Overview

To run this server, you need to install the [DLCLive](https://github.com/DeepLabCut/DeepLabCut-live) package in your computer. You can use conda or pyenv to manage virtual enviroments with specific versions of python.

## Installation

To run the server and the client you need to install this, additionally to DeepLabCutLive
```bash
Install pyav https://pyav.org/docs/develop/overview/installation.html

sudo apt-get install -y python-dev pkg-config
sudo apt-get install -y \
    libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libswscale-dev libswresample-dev libavfilter-dev

sudo apt install python3-pip -y
pip3 install aiortc av opencv-python aiohttp
```


Also, if you need to send a video, you need to install loopback:

```bash
sudo apt install v4l2loopback-dkms
sudo modprobe v4l2loopback

# List devices
v4l2-ctl --list-devices
```

To run the DeepLabCup-Live proccess, you need to have the trained model that you require in the folder `model`

## Quickstart

:construction:

### Run DeepLabCut-Live process
You will stimate poses from the video `dog_clip.avi` using deeplabcut-live.

**1. Download the model**
```bash

wget models http://deeplabcut.rowland.harvard.edu/models/DLC_Dog_resnet_50_iteration-0_shuffle-0.tar.gz -O - | tar -xz -C ./model/

```
**2. Update the config file**

To run DeepLabCut, you need to set it in the video_transform field and set a low video resolution (200x200) to get the ML pipeline to go faster

```json
{
    "cameras": {
        "type": "stream",
        "params": {
            "device": "/dev/video4",  # Set the device
            "file": null,
            "resolution": [   # set the resolution
                200,
                200
            ],
            "fps": 60,    # Set frame per seconds
        },
        "video_transform": "dlclive"   # Set the dlclive mode
    },
    
        ...
```

**3. Send video to virtual device**

you can send it directly or use the bash script. With bash script you will have more options. Remember that you need to have installed  v4l2loopback

```bash
 ffmpeg -re -stream_loop -1 -i dog_clip.avi -vf scale=640:480 -f v4l2 /dev/video4
```
**4. Run the server**
```bash
python server.py
```
**5. Run the client**
```bash
python client.py --url http://127.0.0.1:8080/offer --record False --ping False --show True
```
Note that in this case, the server and the client is runnning at the same machine. If the server is running
in a remote machine, you need to pass the public ip in the `--url` option of the client. 

For the case of a remote server, you need to download the model in it because the server is responsible of run 
the DeepLabCutLive ML pipeline and transform the frames.

## How to use

### Set the configuration

You can  use the `dlc_config.json` file to change some input parameters like the resolution (resolution), 
frame per seconds (fps), the type of operation over the video (video_transform) and the device (device)

The server support four types of transformation over the video:
 - edges
 - cartoon
 - rotate
 - dlclive

 If you don't select any of the options or misspell the option, the frames of the video will not be modified.

 Both the client and the server need to read this file to set some parameters

### Send a video
The client allows you to send image using your webcam but you can send video to an specific device using loopback and ffmpeg:

webcam -> ffmpeg -> virtual webcam

```bash
 ffmpeg -re -stream_loop -1 -i dog_clip.avi -vf scale=640:480 -f v4l2 /dev/video4
```

This allows you to send the video `dog_clip.avi` in stream mode and infinite loop, to the virtual device/webcam `/dev/video4`. You need to check that video4 does not correspond to a real device. 

You can also send the video running the script `send_video.sh`:

```bash
bash send_video.sh [DEVICE] OPTION

OPTION:
  - time
  - timeframe
```

### Run the server

To run the server you need execute this:

```bash

# to show the help
python server.py --help

OUTPUT:
------

usage: server.py [-h] [--cert-file CERT_FILE] [--key-file KEY_FILE]       
                 [--host HOST] [--port PORT] [--record-to RECORD_TO]      
                 [--verbose]                                              
                                                                          
WebRTC audio / video / data-channels demo                                 
                                                                          
optional arguments:                                                       
  -h, --help            show this help message and exit                   
  --cert-file CERT_FILE                                                   
                        SSL certificate file (for HTTPS)                  
  --key-file KEY_FILE   SSL key file (for HTTPS)                          
  --host HOST           Host for HTTP server (default: 0.0.0.0)           
  --port PORT           Port for HTTP server (default: 8080)              
  --record-to RECORD_TO                                                   
                        Write received media to a file.                   
  --verbose, -v


# To run the server
python server.py
```


### Run the Client

```bash

# Tho show the help
python client.py -h

OUTPUT: 

usage: client.py [-h] [--url [URL]] [--show {True,False}] [--record {True,False}] [--ping-pong {True,False}] [--filename [FILENAME]]
                 [--play-from PLAY_FROM] [--verbose] [--signaling {apprtc,copy-and-paste,tcp-socket,unix-socket}]
                 [--signaling-host SIGNALING_HOST] [--signaling-port SIGNALING_PORT] [--signaling-path SIGNALING_PATH]
                 [--signaling-room SIGNALING_ROOM]

Data channels ping/pong

optional arguments:
  -h, --help            show this help message and exit
  --url [URL]
  --show {True,False}   Show the video window. True or False
  --record {True,False}
                        Record the video. True or False
  --ping-pong {True,False}
                        Benchmark data channel with ping pong
  --filename [FILENAME]
                        Video Record filename
  --play-from PLAY_FROM
  --verbose, -v
  --signaling {apprtc,copy-and-paste,tcp-socket,unix-socket}, -s {apprtc,copy-and-paste,tcp-socket,unix-socket}
  --signaling-host SIGNALING_HOST
                        Signaling host (tcp-socket only)
  --signaling-port SIGNALING_PORT
                        Signaling port (tcp-socket only)
  --signaling-path SIGNALING_PATH
                        Signaling socket path (unix-socket only)
  --signaling-room SIGNALING_ROOM
                        Signaling room (apprtc only)


# Run the client
python client.py --url http://127.0.0.1:8080/offer --record False --ping False --show True
```
The client requires that the server is running, otherwise, it will show an error connection. If you are going to send a video, you need to begin to send it first, before running the client, otherwise, the client will not be able to read the virtual device. In the case you are going to use the webcam, the client will load the device itself.
