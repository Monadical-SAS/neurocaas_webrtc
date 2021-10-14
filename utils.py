import asyncio
import json
import os
from functools import partial

import base64
import numpy as np

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
