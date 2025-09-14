#create archive
from logging import getLogger
from argparse import ArgumentParser

from omnilake.client.construct_request_definitions import (
    WebSiteArchiveConfiguration,
    BasicArchiveConfiguration,
    VectorArchiveConfiguration)

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import CreateArchive
from omnilake.client.commands.base import Command

from omni.utils.archiveutil import create_archive_and_wait
from omni.utils.dictutil import keyvalue

logger = getLogger(__name__)

class CreateArchiveCommand(Command):
    command_name='create-archive'
    description='Create a new archive'

    def __init__(self):
        self.omnilake = OmniLake()

    @classmethod
    def configure_parser(cls, parser: ArgumentParser):
        parser.add_argument('archive_id', help='The new archive ID')
        parser.add_argument('--description', '-d', help='Description of the new archive')
        parser.add_argument('--configuration-type', '-t',
                            help='The archive configuration type. Defaults to BasicArchiveConfiguration',
                            choices=['VectorStoreConfiguration', 'WebSiteArchiveConfiguration', 'BasicArchiveConfiguration'],
                            default='BasicArchiveConfiguration')
        parser.add_argument('--configuration-params', '-p', help='Collection of configuration parameter key value pairs', action=keyvalue)

    def _get_configuration_type(self, configuration_type: str, configuration_params: dict):
        if(configuration_type == 'VectorArchiveConfiguration'):
            return VectorArchiveConfiguration(
                tag_model_id=configuration_params.get('tag_model_id', None),
                chunk_body_overlap_percentage=configuration_params.get('chunk_body_overlap_percentage'),
                max_chunk_length=configuration_params.get('max_chunk_length'),
                retain_latest_originals_only=configuration_params.get('retain_latest_originals_only'),
                tag_hint_instructions=configuration_params.get('tag_hint_instructions'))

        if(configuration_type == 'WebSiteArchiveConfiguration'):
            return WebSiteArchiveConfiguration(
                base_url=configuration_params.get("base_url"),
                test_path=configuration_params.get("test_path"))

        if(configuration_type != 'BasicArchiveConfiguration'):
            logger.info(f'Configuration type "{configuration_type}" not found. Defaulting to BasicArchiveConfiguration')
        
        return BasicArchiveConfiguration()

    def _create_archive(self, archive_id: str, description:str, configuration_type: str, configuration_params: dict):
        """
        Create an archive if it doesn't exist
        """
        archive = CreateArchive(
            archive_id=archive_id,
            description=description,
            configuration=self._get_configuration_type(configuration_type, configuration_params)
        )

        create_archive_and_wait(omnilake=self.omnilake,
                                archive=archive)

    def run(self, args):
        print(f'Creating archive "{args.archive_id}"...')
        
        self._create_archive(args.archive_id, args.description, args.configuration_type, args.configuration_params)

