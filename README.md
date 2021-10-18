# NEUROCAAS WEBRTC

## Overview

To run this server, you need to install the [DLCLive](https://github.com/DeepLabCut/DeepLabCut-live) package in your computer. You can use conda or pyenv to manage virtual environments with specific versions of python.

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

To run the DeepLabCup-Live process, you need to have the trained model that you require in the folder `model`

## :construction: Quickstart


You can run the server and the client together in your local machine but if you need more resources, you should run
the server in a remote machine.


### Run DeepLabCut-Live process
You will estimate poses from the video `dog_clip.avi` using deeplabcut-live.

**1. Download the model**

This is required to run the ML pipeline in the server

```bash

wget models http://deeplabcut.rowland.harvard.edu/models/DLC_Dog_resnet_50_iteration-0_shuffle-0.tar.gz -O - | tar -xz -C ./model/
```
or download manually the file `.tar.gz` and uncompress it in folder `model/`

**2. Update the config file**

To run DeepLabCut, you need to set a low video resolution (200x200) to get the ML pipeline to go faster.

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
        ...
    },
    
        ...
```

**3. Send video to virtual device**

you can send it directly or use the bash script. With bash script, you will have more options. Remember that you need to have installed  v4l2loopback

```bash
# command line
ffmpeg -re -stream_loop -1 -i dog_clip.avi -vf scale=200:200 -f v4l2 /dev/video4

# with bash script
bash send_video_ffmpeg.sh '/dev/video4' 'time' '200x200'
```

**4. Run the server**
```bash
python server.py
```

**5. Run the client**
```bash
python client.py --url http://127.0.0.1:8080/offer --show True
```

Note that in this case, the server and the client are running on the same machine. If the server is running
in a remote machine, you need to pass the public IP in the `--url` option of the client. 

For the case of a remote server, you need to download the model in it because the server is in charge of run  
the DeepLabCutLive ML pipeline and transform the frames.

## How to use

### Set the configuration

You can  use the `dlc_config.json` file to change some input parameters like the resolution (resolution), 
frame per second (fps), the type of operation over the video (video_transform) and the device (device)

The server support four types of transformation over the video:
 - edges
 - cartoon
 - rotate
 - dlclive

 If you don't select any of the options or misspell the option, the frames of the video will not be modified.

 Both the client and the server need to read this file to set some parameters

### Send a video
The client allows you to send images using your webcam, but you can send video to a specific device using loopback and ffmpeg:

```mermaid
webcam --> ffmpeg --> virtual webcam
```

To send the video, you can run the following command directly in the command line:
```bash
 ffmpeg -re -stream_loop -1 -i dog_clip.avi -vf scale=640:480 -f v4l2 /dev/video4
```

This allows you to send the video `dog_clip.avi` in stream mode and infinite loop, to the virtual device/webcam `/dev/video4`. You need to check that video4 does not correspond to a real device. 

You can also send the video running the script `send_video_ffmpeg.sh`:

```bash
bash send_video_ffmpeg.sh [DEVICE] OPTION


  OPTION:
  -------

  - device [defaul /dev/video4]: path of video device

  - mode:
      - notime [default]        
      - time   : to send video with timestamp written over it
      - timeframe   : to send video with timestamp and frame number written over it

  - size [default 640x480]: to stablish the frame size

  - fps [default 30]: to stablish the frame per seconds of the video


 EXAMPLE:
 --------
 bash send_video_ffmpeg.sh /dev/video4 time 200x200 30 
```

### Run the server

To run the server, you need to execute this:

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

# To show the help
python client.py -h

OUTPUT: 

uusage: client.py [-h] [--url [URL]] [--show {True,False}]
                 [--record {True,False}] [--ping-pong {True,False}]
                 [--filename [FILENAME]] [--play-from PLAY_FROM]
                 [--poses {True,False}] [--transform TRANSFORM] [--verbose]
                 [--signaling {apprtc,copy-and-paste,tcp-socket,unix-socket}]
                 [--signaling-host SIGNALING_HOST]
                 [--signaling-port SIGNALING_PORT]
                 [--signaling-path SIGNALING_PATH]
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
  --poses {True,False}  Return poses in datachannel
  --transform TRANSFORM, -tf TRANSFORM
                        Video transform option
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
python client.py --url http://127.0.0.1:8080/offer --show True --poses True --transform dlclive
```

In the command above, the option `show` allows showing the video with the poses over it, returned by the ML pipeline. The option `--poses` allows you to get the poses using the datachannel. In this case, you will obtain both, video and poses, but you can set the options to get one of them.

The client requires that the server is running, otherwise, it will show an error connection. If you are going to send a video, you need to begin to send it first, before running the client, otherwise, the client will not be able to read the virtual device. In the case you are going to use the webcam, the client will load the device itself.
