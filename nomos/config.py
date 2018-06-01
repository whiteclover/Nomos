#!/usr/bin/env python
#
# Copyright 2017 Nomos
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Select dict configuration tool"""


class SelectConfig(object):
    """Select dict configuration tool
      Example:
        >>> conf = SelectConfig()
        >>> conf.set("db.host", "localhost")
        >>> conf.get("db")
        >>> ... "host": "localhost"}
        >>> conf.get("db.host")
        >>> ... "localhost"
    :param config: the default dict namnesapce for config, defaults to None
    :type config: dict, optional
    """

    def __init__(self, config=None):
        self._config = config or dict()

    def __len__(self):
        return len(self._config)

    __nonzero__ = __len__

    def set(self, key, value):
        """Set a chain key  value
        :param key: the config chain key with dot split, like "db.host", "host"
        :type key: string
        :param value: the value for key store
        """
        keys = self._keys(key)
        config = self._config
        i = 0
        for k in keys:
            if isinstance(config, dict) and k in config:
                if i == len(keys) - 1:
                    config[k] = value
                    return
                config = config[k]
                i += 1

        keys = keys[i:]
        last_key = keys.pop()
        for k in keys:
            config[k] = {}
            config = config[k]
        config[last_key] = value

    def get(self, key=None, default=None):
        """Get the chain key value, if not fond returns the default value
        :param key: the key. defaults to None, returns the root config.
        :type key: string, optional
        :param default: the default value when not found the key, defaults to None
        :returns: the value for the chain key
        """
        keys = self._keys(key)
        config = self._config
        for k in keys:
            if k in config:
                config = config[k]
            else:
                config = default
                break

        return config

    def delete(self, key):
        """Remove the key config from the current config"""
        keys = self._keys(key)
        if len(keys) == 2:
            v = self.get(keys[0])
            if isinstance(v, dict):
                del v[keys[1]]
        else:
            del self._config[keys[0]]

    def update(self, config):
        """Update the settings in the current config"""
        if isinstance(config, SelectConfig):
            config = config.config()
        for k, v in config.items():
            self.set(k, v)

    def config(self):
        """Return real dict config """
        return self._config

    def __str__(self):
        return str(self._config)

    def __contains__(self, key):
        """Check a key in the config"""
        keys = self._keys(key)
        contains = True
        config = self._config
        for k in keys:
            if k in config:
                config = config[k]
            else:
                contains = False
                break

        return contains

    def _keys(self, key):
        """Split the dot chain key to list"""
        return key.split('.')

    def __json__(self):
        return self._config
