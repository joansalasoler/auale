# -*- coding: utf-8 -*-

class App:
    
    NAME    = 'Aualé'
    VERSION = '1.0.0'
    ID      = 'com.joansala.auale'
    DOMAIN  = 'auale'
    ICON    = 'auale'
    ROLE    = 'game'

from gui.animator import Animator
from gui.canvas import Board
from gui.loop import GameLoop
from gui.mixer import Mixer
from gui.view import GTKView

__all__ = ['App', 'Animator', 'Board', 'GameLoop', 'GTKView', 'Mixer']

