'''
Omni Core Commands
'''

from omni.commands.chain import ChainCommand
from omni.commands.index import RefreshIndexCommand
from omni.commands.question import QuestionCommand
from omni.commands.create_archive import CreateArchiveCommand
from omni.commands.create_source_type import CreateSourceTypeCommand
from omni.commands.describe_archive import DescribeArchiveCommand

__all__ = {k.command_name: k for k in [ChainCommand, RefreshIndexCommand, QuestionCommand, CreateArchiveCommand, CreateSourceTypeCommand, DescribeArchiveCommand]}