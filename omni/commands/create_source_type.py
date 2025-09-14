#create source type
from logging import getLogger
from argparse import ArgumentParser

from omnilake.client.client import OmniLake
from omnilake.client.commands.base import Command

from omni.utils.sourcetypeutil import create_source_type

logger = getLogger(__name__)

class CreateSourceTypeCommand(Command):
    command_name='create-source-type'
    description='Create a new source type'

    def __init__(self):
        self.omnilake = OmniLake()

    @classmethod
    def configure_parser(cls, parser: ArgumentParser):
        parser.add_argument('name', help='Name of the new source type')
        parser.add_argument('--description', '-d', help='Version of the new source type')
        parser.add_argument('--required-fields', '-r', help='Required field to be included', action='append')

    def run(self, args):
        print(f'Creating source type "{args.name}"...')

        # Create the source type if it doesn't exist
        create_source_type(omnilake=self.omnilake,
                           name=args.name,
                           description=args.description,
                           required_fields=args.required_fields)
