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

''' A random insult plugin '''

import random

def enabled ():
    '''
        Enabled

        Is this plugin enabled. Returning false here
        will cause this plugin to be ignored by the
        framework entirely.

        --
        @return bool
    '''

    return True

def applicable_types ():
    '''
        Applicable Types

        Returns the type of messages this plugin is for.
        See: hogar.static.values

        --
        @return list
    '''

    return ['text']

def commands ():
    '''
        Commands

        In the case of text plugins, returns the commands
        that this plugin should trigger for. For other
        message types, a empty list should be returned.

        --
        @return list
    '''

    return ['insult']

def should_reply ():
    '''
        Should Reply

        Specifies wether a reply should be sent to the original
        sender of the message that triggered this plugin.

        --
        @return bool
    '''

    return True

def reply_type ():
    '''
        Reply Type

        Specifies the type of reply that should be sent to the
        sender. This is an optional function. See hogar.static.values
        for available types.

        --
        @return str
    '''

    return 'text'

def run (message):
    '''
        Run

        Run the custom plugin specific code. A returned
        string is the message that will be sent back
        to the user.

        --
        @param  message:dict    The message sent by the user

        @return str
    '''

    # The list of insults
    insults = [

        # src: http://www.sudo.ws/repos/sudo/file/bc44b0fbc03b/plugins/sudoers/ins_2001.h
        "Just what do you think you're doing Dave?",
        "It can only be attributed to human error.",
        "That's something I cannot allow to happen.",
        "My mind is going. I can feel it.",
        "Sorry about this, I know it's a bit silly.",
        "Take a stress pill and think things over.",
        "This mission is too important for me to allow you to jeopardize it.",
        "I feel much better now.",

        # src: http://www.sudo.ws/repos/sudo/file/bc44b0fbc03b/plugins/sudoers/ins_classic.h
        "Wrong!  You cheating scum!",
        "And you call yourself a Rocket Scientist!",
        "No soap, honkie-lips.",
        "Where did you learn to type?",
        "Are you on drugs?",
        "My pet ferret can type better than you!",
        "You type like i drive.",
        "Do you think like you type?",
        "Your mind just hasn't been the same since the electro-shock, has it?",

        # src: http://www.sudo.ws/repos/sudo/file/bc44b0fbc03b/plugins/sudoers/ins_csops.h
        "Maybe if you used more than just two fingers...",
        "BOB says:  You seem to have forgotten your passwd, enter another!",
        "stty: unknown mode: doofus",
        "I can't hear you -- I'm using the scrambler.",
        "The more you drive -- the dumber you get.",
        "Listen, broccoli brains, I don't have time to listen to this trash.",
        "Listen, burrito brains, I don't have time to listen to this trash.",
        "I've seen penguins that can type better than that.",
        "Have you considered trying to match wits with a rutabaga?",
        "You speak an infinite deal of nothing",

        # src: http://www.sudo.ws/repos/sudo/file/bc44b0fbc03b/plugins/sudoers/ins_goons.h
        "You silly, twisted boy you.",
        "He has fallen in the water!",
        "We'll all be murdered in our beds!",
        "You can't come in. Our tiger has got flu",
        "I don't wish to know that.",
        "What, what, what, what, what, what, what, what, what, what?",
        "You can't get the wood, you know.",
        "You'll starve!",
        "... and it used to be so popular...",
        "Pauses for audience applause, not a sausage",
        "Hold it up to the light --- not a brain in sight!",
        "Have a gorilla...",
        "There must be cure for it!",
        "There's a lot of it about, you know.",
        "You do that again and see what happens...",
        "Ying Tong Iddle I Po",
        "Harm can come to a young lad like that!",
        "And with that remarks folks, the case of the Crown vs yourself was proven.",
        "Speak English you fool --- there are no subtitles in this scene.",
        "You gotta go owwwww!",
        "I have been called worse.",
        "It's only your word against mine.",
        "I think ... err ... I think ... I think I'll go home",
    ]

    return random.choice(insults)
