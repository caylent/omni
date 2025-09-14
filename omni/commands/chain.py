import json
import omni.utils.lakerequestutil as lakerequestutil

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import (
    DescribeChainRequest,
    SubmitChainRequest,
)

from omni.commands.base import Command

class ChainCommand(Command):
    command_name='chain'
    description='Execute a chain against OmniLake'

    def __init__(self):
        self.omnilake = OmniLake()

    @classmethod
    def configure_parser(cls, parser):
        parser.add_argument('chain_definition', help='The chain definition file to execute')

    def run(self, args):
        """
        Execute the command
        """
        with open(args.chain_definition, 'r') as chain_file:
            loaded_chain_file = json.load(chain_file)
        
        print('Loaded Chain Definition:')

        print(json.dumps(loaded_chain_file, indent=4))

        print('Executing chain...')

        chain_id = lakerequestutil.execute_and_wait(
            omnilake=self.omnilake,
            request=SubmitChainRequest(chain=loaded_chain_file),
            return_id_property='chain_request_id',
        )

        if not chain_id:
            print('Request failed to complete, check logs for more information')
            return

        chain_resp = self.omnilake.request(DescribeChainRequest(chain_request_id=chain_id))

        executed_requests = chain_resp.response_body["executed_requests"]

        for request_name in executed_requests:
            lakerequestutil.describe_result(
                omnilake=self.omnilake,
                lake_request_id=executed_requests[request_name],
                request_name=request_name
            )
