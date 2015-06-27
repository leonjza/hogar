#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2015 Leon Jacobs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import imp
import os
import sys
from hogar.static import values as static_values

import logging
logger = logging.getLogger(__name__)

# Plugins will typically live in hogar/Plugins/
plugin_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/Plugins'

# A plugin will have its entypoint defined by the main.py file.
plugin_enty = 'main'

def get_plugins():

    '''
        Get Plugins

        Scans a directory and attempts to find possible
        plugins to load.

        --
        @return list
    '''

    logger.debug('Searching for plugins in: {path}'.format(path = plugin_path))

    plugins = []
    possibleplugins = os.listdir(plugin_path)

    for i in possibleplugins:

        logger.debug('Inspecting possible plugin: {plugin}'.format(plugin = i))
        location = os.path.join(plugin_path, i)

        if not os.path.isdir(location) or not plugin_enty + '.py' in os.listdir(location):
            logger.debug('{plugin} is not a .py or not a valid entry point'.format(plugin = i))
            continue

        logger.debug('{plugin} seems valid. Adding to available plugins'.format(plugin = i))
        info = imp.find_module(plugin_enty, [location])
        plugins.append({ 'name': i, 'info': info })

    return plugins

def load_plugin(plugin):

    '''
        Load a Plugin

        Loads a plugin and returns an instance of it.

        --
        @param  plugin:tuple    A plugin discovered using imp.find_module

        @return mixed
    '''

    try:
        return imp.load_module(plugin['name'], *plugin['info'])

    # Cleanup the open file caused by imp
    finally:
        fp = plugin['info'][0]
        if fp:
            fp.close()

def prepare_plugins():

    '''
        Prepare Plugins

        Orchestrates the search, prepare and error checking
        of plugins for Hogar.

        --
        @return dict
    '''

    # Prepare a dictionary of possible message
    # types that will have lists of plugins
    command_map = { message_type: [] for message_type in static_values.possible_message_types }

    # Read all of the plugins out of the plugins directory
    plugins = get_plugins()

    for plugin in plugins:

        # Load up the plugin
        plugin_test = load_plugin(plugin)
        plugin_commands = plugin_test.commands()
        plugin_applicable_types = plugin_test.applicable_types()

        # Check the command list
        if not isinstance(plugin_commands, list):
            logger.error('Skipping plugin {name}. Commands should be returned as a list in commands()'.format(
                name = plugin['name']
            ))
            continue

        # Check the applicable types list
        if not isinstance(plugin_applicable_types, list) or len(plugin_applicable_types) < 1:
            logger.error('Skipping plugin {name}. Applicable Types should be returned as a list in applicable_types()'.format(
                name = plugin['name']
            ))
            continue

        # check that the defined message types that
        # the plugin wants to subscribe to are
        # valid
        for message_type in plugin_applicable_types:

            if message_type not in command_map.keys():
                logger.error('Skipping plugin {name}. {message_type} is not valid'.format(
                    name = plugin['name'],
                    message_type = message_type
                ))
                continue

        logger.debug('Loading plugin: {name}'.format(name = plugin['name']))

        # load the commands into the command_map
        for message_type in plugin_applicable_types:
            command_map[message_type].append({
                'plugin' : plugin_test,
                'name' : plugin['name'],
                'commands' : plugin_commands

            })

    return command_map
