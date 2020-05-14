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
    CREATE_ICON = './res/image/create.svg'
    ERROR_ICON = './res/image/error.svg'
    FOLDER_ICON = './res/image/folder.svg'
    HELP_ICON = './res/image/help.svg'
    INFORMATION_ICON = './res/image/information.svg'


from .animator import Animator
from .canvas import Board
from .loop import GameLoop
from .mixer import Mixer
from .view import GTKView
from .application import GTKApplication


__all__ = [
    'App',
    'Animator',
    'Board',
    'GameLoop',
    'GTKApplication',
    'GTKView',
    'Mixer'
]
