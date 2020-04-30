# -*- coding: utf-8 -*-


class App:
    """Application constants"""

    NAME = 'Aualé'
    VERSION = '1.1.2'
    ID = 'com.joansala.auale'
    DOMAIN = 'auale'
    ICON = 'auale'
    ROLE = 'game'

    HOME_URL = 'http://www.joansala.com/auale/'
    HELP_URL = 'http://www.joansala.com/auale/help/'
    RULES_URL = 'http://www.joansala.com/auale/rules/'

    COMMENT_ICON = './res/image/comment.svg'
    ERROR_ICON = './res/image/error.svg'
    FOLDER_ICON = './res/image/folder.svg'
    HELP_ICON = './res/image/help.svg'
    INFORMATION_ICON = './res/image/information.svg'


from gui.animator import Animator
from gui.canvas import Board
from gui.loop import GameLoop
from gui.mixer import Mixer
from gui.view import GTKView
from gui.application import GTKApplication


__all__ = [
    'App',
    'Animator',
    'Board',
    'GameLoop',
    'GTKApplication',
    'GTKView',
    'Mixer'
]
