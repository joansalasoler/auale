# -*- coding: utf-8 -*-

class App:
    
    NAME    = 'Aualé'
    VERSION = '1.1.2'
    ID      = 'com.joansala.auale'
    DOMAIN  = 'auale'
    ICON    = 'auale'
    ROLE    = 'game'
    
    HOME_URL  = 'http://www.joansala.com/auale/'
    HELP_URL  = 'http://www.joansala.com/auale/help/'
    RULES_URL = 'http://www.joansala.com/auale/rules/'

from gui.animator import Animator
from gui.canvas import Board
from gui.loop import GameLoop
from gui.mixer import Mixer
from gui.view import GTKView
from gui.application import GTKApplication

__all__ = [
    'App', 'Animator', 'Board', 'GameLoop',
    'GTKApplication', 'GTKView', 'Mixer'
]

