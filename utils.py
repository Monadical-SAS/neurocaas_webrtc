import asyncio
import json
import os
from functools import partial

import base64
import numpy as np
from PIL import Image, ImageDraw
import colorcet as cc

class ConfigDLC(object):
    """docstring for ConfigDLC."""
    def __init__(self, namefile):
        super(ConfigDLC, self).__init__()
        self.cfg_name = namefile
        self.cfg_file = ''
        self.cfg = {}
        
    def get_docs_path(self):
        """ Get path to documents folder

        Returns
        -------
        str
            path to documents folder
        """

        # return os.path.normpath(os.path.expanduser("~/Documents/DeepLabCut-live-GUI"))
        return os.path.normpath(os.path.expanduser("./"))

    def get_config_path(self, cfg_name):
        """ Get path to configuration foler

        Parameters
        ----------
        cfg_name : str
            name of config file

        Returns
        -------
        str
            path to configuration file
        """

        return os.path.normpath(self.get_docs_path() + "/config/" + cfg_name + ".json")

    def get_config(self):
        """ Read configuration

        Parameters
        ----------
        cfg_name : str
            name of configuration
        """

        ### read configuration file ###

        self.cfg_file = self.get_config_path(self.cfg_name)
        if os.path.isfile(self.cfg_file):
            return json.load(open(self.cfg_file))
        else:
            return {}


def run_in_executor(func, *args, executor=None):
    callback = partial(func, *args)
    return asyncio.get_event_loop().run_in_executor(executor, callback)


def serialize_numpy_array(ndarray):
    msg = {
        '__ndarray__': base64.b64encode(ndarray.tobytes()).decode('utf8'),
        'dtype': ndarray.dtype.name,
        'shape': ndarray.shape
    }
    return json.dumps(msg)


def deserialize_numpy_array(json_dump):
    msg = json.loads(json_dump)
    ndarray = (
        np.frombuffer(
            base64.b64decode(msg['__ndarray__']),
            dtype=msg['dtype']
        )
        .reshape(msg['shape'])
    )
    return ndarray


def set_poses_in_frame(frame, pose, options):
    
    if frame is not None:

        img = Image.fromarray(frame)
        if frame.ndim == 3:
            b, g, r = img.split()
            img = Image.merge("RGB", (r, g, b))

        im_size = (frame.shape[1], frame.shape[0])
        display_colors = set_display_colors(pose.shape[0], options['cmap'])
        img_draw = ImageDraw.Draw(img)

        for i in range(pose.shape[0]):
            if pose[i, 2] > options['lik_thresh']:
                try:
                    x0 = (
                        pose[i, 0] - options['radius']
                        if pose[i, 0] - options['radius'] > 0
                        else 0
                    )
                    x1 = (
                        pose[i, 0] + options['radius']
                        if pose[i, 0] + options['radius'] < im_size[1]
                        else im_size[1]
                    )
                    y0 = (
                        pose[i, 1] - options['radius']
                        if pose[i, 1] - options['radius'] > 0
                        else 0
                    )
                    y1 = (
                        pose[i, 1] + options['radius']
                        if pose[i, 1] + options['radius'] < im_size[0]
                        else im_size[0]
                    )
                    coords = [x0, y0, x1, y1]
                    img_draw.ellipse(
                        coords,
                        fill=display_colors[i],
                        outline=display_colors[i],
                    )
                except Exception as e:
                    print(e)
        newframe = np.asarray(img)
        return newframe
    else:
        return frame


def set_display_colors(bodyparts, cmap):
    all_colors = getattr(cc, cmap)
    return all_colors[:: int(len(all_colors) / bodyparts)]

       