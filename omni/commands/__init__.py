'''
Omnitizer Commands

- Index: Indexes the omnilake database by crawling the given directory
- Question: Takes a question about the project and returns the answer
- Create Archive: Creates an archive
- Describe Archive: Describes an archive
'''

from omni.commands.chain import ChainCommand
from omni.commands.index import RefreshIndexCommand
from omni.commands.question import QuestionCommand
from omni.commands.create_archive import CreateArchiveCommand
from omni.commands.create_source_type import CreateSourceTypeCommand
from omni.commands.describe_archive import DescribeArchiveCommand

__all__ = {k.command_name: k for k in [ChainCommand, RefreshIndexCommand, QuestionCommand,CreateArchiveCommand]}