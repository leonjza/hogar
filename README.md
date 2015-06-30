# HOGAR

![logo](http://i.imgur.com/7aCuc2S.png)

A pluggable Telegram Bot based on the official Telegram [Bot API](https://core.telegram.org/bots/api)

## introduction
Hogar is a pure python Telegram Bot, fully extensible via plugins. Telegram recently announced official support for a [Bot API](https://telegram.org/blog/bot-revolution) allowing integrators of all sorts to bring automated interactions to the mobile platform. Hogar aims to provide a platform where one could simply write a plugin and have interactions in a matter of minutes.

## installation
Essentially, all you really need for Hogar is a python 2.x interpreter. If you use plugins that need database access, then you will need that too. I will also always suggest you run projects such as this in a python [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) so that the dependencies you install for Hogar don’t interfere with the system provided ones. It also makes it easy to restart in case you messed up :)

So here goes:

##### clone
The first thing to do is clone the repository:

```bash
$ git clone https://github.com/leonjza/hogar.git
```

Hogar should now be in the `hogar` directory.

##### dependencies
Next, we need to satisfy the dependencies for Hogar. We will use pip to get this done quickly (remember to activate your virtual environment if you are going that route):

```bash
$ pip install -r requirements.txt
```

You should see a whole bunch of lines where pip installs the dependencies (some of which may require compilation of modules). Once you see the line `Successfully installed [snip]` you are done with the dependencies.

##### setup
Hogar comes with a `settings.ini.sample` file. This should be copied to `settings.ini` with:

```bash
$ cp settings.ini.sample settings.ini
```

###### bot token
You will notice that the `settings.ini` wants a value for `bot_access_token`. This token may be obtained via a telegram client for your bot. See [this](https://core.telegram.org/bots#botfather) link if you are unsure of how to so this.

The rest of the settings should be ok. If you want to use MySQL instead of the SQLite database, then update the required fields.

##### database
Hogar has a sample plugin that allows you to store and retrieve simple key value pairs. Storage of these reside within the database you have chosen. In order for this plugin to work, you need to setup the database first. To do this, type:

```bash
$ python start.py setupdb
[snip]
 * Setup of database `var/data.sqlite.db` complete
```

Depending on your database setup, the last message may differ.

#### start
Thats it. Start the bot with:

```bash
python start.py

.__
|  |__   ____   _________ _______
|  |  \ /  _ \ / ___\__  \\_  __ \
|   Y  (  <_> ) /_/  > __ \|  | \/
|___|  /\____/\___  (____  /__|
     \/      /_____/     \/
                   v0.1 - @leonjza

 * Loading plugins...
 * Loaded plugins for 8 message types: document; text; sticker; contact; video; location; photo; audio
 * Starting long poller
```

## plugins
Hogar as it is does not do much. Almost all of the functionality is added via plugins. Writing a plugin for Hogar is also very easy. The smallest of plugin should provide roughly 4 functions, one of which is a `run()` method. Samples may be found in the [hogar/Plugins](https://github.com/leonjza/hogar/tree/master/hogar/Plugins) directory.

##### plugin basics
As previously mentioned, all a plugin really is, is a set of functions defining a few characteristics of the plugin. The [sample plugin](https://github.com/leonjza/hogar/blob/master/hogar/Plugins/sample.py) is heavily documented and may also referred to if needed.

##### how plugins are added
Hogar has some features built in that will discover your plugin when it boots up. The following list describes the logic of the plugin loader found [here](https://github.com/leonjza/hogar/blob/master/hogar/Utils/PluginLoader.py):

 * The plugin loaders searches for files and folders in `hogar/Plugins`
 * The plugin entry should have the name `main.py`
 * The entry should not be a directory
 * The plugin should implement the functions: `applicable_types()`, `commands()`, `should_reply()` and `run()`.

If all of these conditions are met, the plugin loader will register the `commands` and message `types` that your plugin applies to and make it available to all messages that come in.

##### plugin writing tips
- To write your first plugin, I would suggest you start off with making a new unique directory name in the `Plugins` directory and copy the `sample.py` to your plugin directory as `main.py`.  
- Ensure that you obey the return types as specified in the sample comments. Hogar expects to interpret your plugin based on these.  
- The `run()` method will receive the message as an argument for you to interpret/manipulate as needed.  
- Don't let the fact the required functions are needed hold you back from importing others and structuring the plugin as needed. :)

##### plugin sample
A plugin could be seen as below. This plugin will respond with the string `This is a sample` for every text message received by your bot prefixed by the command `sample`. For example, the commands `/sample` and `@MrBot sample` or a direct message will all trigger your plugin.

```python
def applicable_types():
    return ['text']

def commands():
    return ['sample']

def should_reply():
    return True

def run(message):
    return 'This is a sample'
```
