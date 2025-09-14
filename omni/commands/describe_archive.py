from logging import getLogger
from argparse import ArgumentParser

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import DescribeArchive
from omnilake.client.commands.base import Command

logger = getLogger(__name__)

class DescribeArchiveCommand(Command):
    command_name='describe-archive'
    description='Describe an archive'

    def __init__(self):
        self.omnilake = OmniLake()

    @classmethod
    def configure_parser(cls, parser: ArgumentParser):
        parser.add_argument('archive_id', help='The archive to be described')

    def _describe_archive(self, archive_id: str):
        """
        Describe an archive
        """
        try:
            archive = DescribeArchive(archive_id)

            response = self.omnilake.request(archive)

            response_body = response.response_body

            print(f"""ArchiveId: {response_body['archive_id']}
                  Description: {response_body['description']}
                  Status: {response_body['status']}
                  Archive Type: {response_body['archive_type']}
                  Configuration Parameters: {response_body['configuration']}""")

        except Exception as error:
            logger.error(f'Error describing archive {archive_id}:', error)
            raise

    def run(self, args):
        print(f'Describing archive "{args.archive_id}"...')
                
        self._describe_archive(args.archive_id)
