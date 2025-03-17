import json
import time

from datetime import datetime
from typing import Optional

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import (
    DescribeChainRequest,
    DescribeJob,
    DescribeLakeRequest,
    GetEntry,
    SubmitChainRequest,
)

from omni.commands.base import Command

class ChainCommand(Command):
    command_name='chain'

    description='Execute a chain against OmniLake'

    def __init__(self, omnilake_app_name: Optional[str] = None,
                 omnilake_deployment_id: Optional[str] = None):
        self.omnilake = OmniLake(
            app_name=omnilake_app_name,
            deployment_id=omnilake_deployment_id,
        )

    @classmethod
    def configure_parser(cls, parser):
        parser.add_argument('chain_definition', help='The chain definition file to execute')

    def _execute_request_and_wait(self, request: SubmitChainRequest) -> str:
        """
        Execute a request and wait for it to complete

        Keyword arguments:
        request -- The request to execute
        """
        resp = self.omnilake.request(request=request)

        job_type = resp.response_body["job_type"]
        job_id = resp.response_body["job_id"]
        chain_id = resp.response_body["chain_request_id"]

        job_describe = DescribeJob(
            job_id=job_id,
            job_type=job_type,
        )

        job_resp = self.omnilake.request(job_describe)

        job_status = job_resp.response_body['status']

        job_failed = False

        while job_status != 'COMPLETED':
            time.sleep(10)

            job_resp = self.omnilake.request(job_describe)

            if job_resp.response_body['status'] != job_status:
                job_status = job_resp.response_body['status']

                if job_status == 'FAILED':
                    print(f'Job failed: {job_resp.response_body["status_message"]}')

                    job_failed = True
                    break

                print(f'Job status updated: {job_status}')
        
        print(f'Final job status: {job_status}') if not job_failed else None

        started = datetime.fromisoformat(job_resp.response_body['started'])
        ended = datetime.fromisoformat(job_resp.response_body['ended'])

        total_run_time = ended - started

        print(f'Total run time: {total_run_time}')

        return chain_id if not job_failed else None

    def _output_lake_response(self, request_id: str, request_name: str):
        """
        Output the response of a lake request

        Keyword arguments:
        request_id -- The ID of the request.
        request_name -- The name of the
        """
        request_request_obj = DescribeLakeRequest(lake_request_id=request_id)

        resp = self.omnilake.request(request_request_obj)

        entry_id = resp.response_body['response_entry_id']

        content_resp = self.omnilake.request(GetEntry(entry_id=entry_id))

        entry_content = content_resp.response_body['content']

        print(f"Request \"{request_name}\" Response\n=================\n\n{entry_content}")

    def run(self, args):
        """
        Execute the command
        """
        with open(args.chain_definition, 'r') as chain_file:
            loaded_chain_file = json.load(chain_file)
        
        print('Loaded Chain Definition:')

        print(json.dumps(loaded_chain_file, indent=4))

        print('Executing chain...')

        chain_id = self._execute_request_and_wait(request=SubmitChainRequest(chain=loaded_chain_file))

        if not chain_id:
            print('Request failed to complete, check logs for more information')
            return

        chain_resp = self.omnilake.request(DescribeChainRequest(chain_request_id=chain_id))

        executed_requests = chain_resp.response_body["executed_requests"]

        for request_name in executed_requests:
            self._output_lake_response(request_id=executed_requests[request_name], request_name=request_name)
