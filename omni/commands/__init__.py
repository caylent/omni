'''
Omni Core Commands
'''

from omni.commands.chain import ChainCommand
from omni.commands.index import RefreshIndexCommand
from omni.commands.question import QuestionCommand

__all__ = {k.command_name: k for k in [ChainCommand, RefreshIndexCommand, QuestionCommand]}