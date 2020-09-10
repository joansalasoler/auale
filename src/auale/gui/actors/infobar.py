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

from gi.repository import GLib
from game import Match
from i18n import gettext as _

from .actor import Actor


class Infobar(Actor):
    """Shows information about a match"""

    __gtype_name__ = 'Infobar'

    def __init__(self):
        super(Infobar, self).__init__()

    def has_message(self):
        """Checks if a message is shown"""

        if canvas := self.get_content():
            return bool(canvas.get_markup())

        return False

    def show_match_information(self, match):
        """Show information about a match file"""

        if not isinstance(match, Match):
            return self.clear_message()

        if comment := match.get_comment():
            return self.show_match_comment(match)

        if self._is_first_position(match):
            markup = self._get_match_start_message(match)
            return self.show_info_message(markup)

        if self._is_endgame_position(match):
            markup = self._get_match_end_message(match)
            return self.show_info_message(markup)

        self.clear_message()

    def show_match_comment(self, match):
        """Show the comment for the current match position"""

        comment = match.get_comment() or ''
        text = GLib.markup_escape_text(comment)

        self.show_info_message(text)

    def show_principal_variation(self, report):
        """Show a principal variation given a player report"""

        style = 'foreground="#feebc4"'
        score = self._get_variation_score(report)
        variation = self._get_principal_variation(report)
        text = ' '.join((variation, f'<span { style }>{ score }</span>'))

        self.show_info_message(text)

    def show_error_message(self, message):
        """Shows an error message"""

        if canvas := self.get_content():
            style = 'foreground="#feebc4"'
            markup = f'<span { style }>{ message }</span>'
            canvas.set_markup(markup)

    def show_info_message(self, markup):
        """Shows an informative message"""

        if canvas := self.get_content():
            canvas.set_markup(markup)

    def clear_message(self):
        """Clears the current message"""

        if canvas := self.get_content():
            canvas.set_markup('')

    def _is_first_position(self, match):
        """Checks if the match position is the first of the game"""

        return not match.can_undo()

    def _is_endgame_position(self, match):
        """Checks if the match position is the endgame position"""

        return match.has_ended() and not match.can_redo()

    def _escape_match_tag(self, match, tag_name):
        """Returns an escaped tag markup or none if the tag is empty"""

        tag = match.get_tag(tag_name)
        value = tag and GLib.markup_escape_text(tag)

        return value

    def _get_match_start_message(self, match):
        """Message to show when a match starts"""

        event = self._escape_match_tag(match, 'Event')
        south = self._escape_match_tag(match, 'South')
        north = self._escape_match_tag(match, 'North')
        result = self._escape_match_tag(match, 'Result')

        has_result = result != '*'
        has_players = south and north
        has_event = event is not None

        style = 'foreground="#feebc4"'
        title = f'<span { style }>{ event }:</span> ' if has_event else ''
        players = f'{ south } vs. { north }' if has_players else ''
        scores = f' ({ result })' if has_players and has_result else ''
        markup = f'{ title }{ players }{ scores }'

        return markup

    def _get_match_end_message(self, match):
        """Message to show when a match ends"""

        game = match.get_game()
        winner = match.get_winner()
        is_repetition = match.is_repetition()

        title = _('This match was drawn')
        description = _('Players gathered an equal number of seeds')

        if winner == game.SOUTH:
            title = _('South has won')
        elif winner == game.NORTH:
            title = _('North has won')

        if is_repetition is True:
            description = _('Same position was repeated twice')
        elif winner != game.DRAW:
            description = _('The player gathered more than 24 seeds')

        style = 'foreground="#feebc4"'
        markup = f'<span {style}>{ title }:</span> { description }'

        return markup

    def _get_principal_variation(self, report):
        """Extracts the principal variation from an engine report"""

        move = report.get('ponder') or ''
        variation = report.get('pv') or ''
        n = int(report.get('number'))

        moves = '{:s}{:s}'.format(move, variation)
        moves = '…{:s}'.format(moves) if moves[0:1].islower() else moves
        groups = [moves[i:i + 2] for i in range(0, len(moves), 2)]
        result = ' '.join([f'{ n + i }. { m }' for i, m in enumerate(groups)])

        return result

    def _get_variation_score(self, report):
        """Extracts the score from an engine report"""

        score = report.get('cp') or '0'
        value = int(score) / 100
        result = '{:+.2f} {:s}'.format(value, _('seeds'))

        return result
