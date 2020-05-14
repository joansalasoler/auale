# -*- coding: utf-8 -*-

# Aualé oware graphic user interface.
# Copyright (C) 2014-2020 Joan Sala Soler <contact@joansala.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .parser import Parser

# == Token types ==============================================================

INTEGER = r'[-+]?\d+'
MOVE = r'[a-fA-F]'
NUMBER = r'\d+'
OPTION_TYPE = r'check|spin|combo|button|string'
SCORE_TYPE = r'lowerbound|upperbound'
STRING = r'.+'
WORD = r'\S+'

# == Command rules ============================================================

RULES = (
    (rf'(?P<order>uciok)',),
    (rf'(?P<order>readyok)',),
    (rf'(?P<order>id)', (
        rf'name\s+(?P<name>{ STRING })',
        rf'author\s+(?P<author>{ STRING })',
    )),
    (rf'(?P<order>bestmove)\s+(?P<move>{ MOVE })', (
        rf'ponder\s+(?P<ponder>{ MOVE })',
    )),
    (rf'(?P<order>option)', (
        rf'name\s+(?P<name>{ WORD })',
        rf'type\s+(?P<type>{ OPTION_TYPE })',
        rf'min\s+(?P<min>{ INTEGER })',
        rf'max\s+(?P<max>{ INTEGER })',
        rf'var\s+(?P<var>{ WORD })',
        rf'default\s+(?P<default>{ WORD })',
    )),
    (rf'(?P<order>info)', (
        rf'string\s+(?P<string>{ STRING })',
        rf'depth\s+(?P<depth>{ NUMBER })',
        rf'seldepth\s+(?P<seldepth>{ NUMBER })',
        rf'time\s+(?P<time>{ NUMBER })',
        rf'nodes\s+(?P<nodes>{ NUMBER })',
        rf'pv\s+(?P<pv>{ MOVE }+)',
        rf'multipv\s+(?P<multipv>{ NUMBER })',
        rf'currmove\s+(?P<currmove>{ MOVE })',
        rf'currmovenumber\s+(?P<currmovenumber>{ NUMBER })',
        rf'hashfull\s+(?P<hashfull>{ NUMBER })',
        rf'nps\s+(?P<nps>{ NUMBER })',
        rf'tbhits\s+(?P<tbhits>{ NUMBER })',
        rf'sbhits\s+(?P<sbhits>{ NUMBER })',
        rf'cpuload\s+(?P<cpuload>{ NUMBER })',
        rf'refutation\s+(?P<refutation>{ MOVE }+)',
        rf'score(?:\s+(?:%s|%s|%s))+' % (
            rf'cp\s+(?P<cp>{ INTEGER })',
            rf'mate\s+(?P<mate>{ INTEGER })',
            rf'(?P<type>{ SCORE_TYPE })',
        ),
        rf'currline\s+(?:%s\s+)?%s' % (
            rf'(?P<cpu>{ NUMBER })',
            rf'(?P<moves>{ MOVE }+)',
        ),
    )),
)

# == Scanner instance =========================================================

parser = Parser(RULES)
