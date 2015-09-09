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
from hogar.static import values as static_values
import logging

logger = logging.getLogger(__name__)

# Plugins will typically live in hogar/Plugins/
plugin_path = os.path.abspath(
    os.path.dirname(os.path.dirname(__file__))) + '/Plugins'

# A plugin will have its entypoint defined by the main.py file.
plugin_enty = 'main'

def get_plugins ():
    '''
        Get Plugins

        Scans a directory and attempts to find possible
        plugins to load.

        --
        @return list
    '''

    logger.debug('Searching for plugins in: {path}'.format(path = plugin_path))

    plugins = []

    for i in os.listdir(plugin_path):

        logger.debug('Inspecting possible plugin: {plugin}'.format(plugin = i))
        location = os.path.join(plugin_path, i)

        if not os.path.isdir(location) or not plugin_enty + '.py' in os.listdir(location):
            logger.debug('{plugin} is not a .py or not a valid entry point'.format(plugin = i))
            continue

        logger.debug('{plugin} seems valid. Adding to available plugins'.format(plugin = i))
        info = imp.find_module(plugin_enty, [location])
        plugins.append({'name': i, 'info': info})

    return plugins

def find_plugin (name):
    '''
        Find Plugin

        Scans a directory and attempts to find a
        specific plugin

        --
        @param name:str     The name of the plugin to find

        @return dict
    '''

    logger.debug('Finding plugin {plugin}'.format(
        plugin = name))

    for i in os.listdir(plugin_path):

        if i == name:
            location = os.path.join(plugin_path, i)
            info = imp.find_module(plugin_enty, [location])
            return {'name': i, 'info': info}

    return

def load_plugin (plugin):
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

def prepare_plugins ():
    '''
        Prepare Plugins

        Orchestrates the search, prepare and error checking
        of plugins for Hogar.

        --
        @return dict
    '''

    # Prepare a dictionary of possible message
    # types that will have lists of plugins
    command_map = {message_type: [] for message_type in static_values.possible_message_types}

    # Read all of the plugins out of the plugins directory
    plugins = get_plugins()

    for plugin in plugins:

        # Attempt to load the plugins
        try:

            # Load up the plugin
            plugin_test = load_plugin(plugin)
            plugin_commands = plugin_test.commands()
            plugin_applicable_types = plugin_test.applicable_types()
            plugin_should_reply = plugin_test.should_reply()

        except AttributeError, e:
            error = 'Failed to load plugin {plugin}. Error: {error}'.format(
                plugin = plugin['name'], error = str(e))
            logger.error(error)
            print ' * {error}'.format(error = error)

            continue

        # Check if the plugin is set to enabled
        if hasattr(plugin_test, 'enabled'):
            if not plugin_test.enabled():
                logger.error('Skipping plugin {name}. enabled() is \'false\''.format(
                    name = plugin['name']))
                continue
        else:
            logger.warning('Plugin {plugin} does not specify a status. Defaulting to \'enabled\''.format(
                plugin = plugin['name']))

        # Check the command list
        if not isinstance(plugin_commands, list):
            logger.error('Skipping plugin {name}. Commands should be returned as a list in commands()'.format(
                name = plugin['name']
            ))
            continue

        # Check the applicable types list
        if not isinstance(plugin_applicable_types, list) or len(plugin_applicable_types) < 1:
            logger.error(
                'Skipping plugin {name}. Applicable Types should be returned as a list in applicable_types()'.format(
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

        # Check that should_reply() returned a boolean
        if not isinstance(plugin_should_reply, bool):
            logger.error('Skipping plugin {name}. applicable_types() should return a Boolean'.format(
                name = plugin['name']
            ))
            continue

        # Check if the plugin has a reply type set. If it does,
        # the type should be one of the known types.
        if hasattr(plugin_test, 'reply_type'):
            if plugin_test.reply_type() not in static_values.possible_message_types:
                logger.error('Skipping plugin {name}. reply_type() should be valid'.format(
                    name = plugin['name']
                ))
                continue
        else:
            logger.warning('Plugin {plugin} does not specify a reply type. Defaulting to \'text\''.format(
                plugin = plugin['name']
            ))

        # Load up the plugin
        logger.debug('Loading plugin: {name}'.format(name = plugin['name']))

        # load the commands into the command_map
        for message_type in plugin_applicable_types:
            command_map[message_type].append({
                'name': plugin['name'],
                'commands': plugin_commands
            })

    return command_map
