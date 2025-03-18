import time

from argparse import ArgumentParser
from datetime import datetime
from typing import Optional

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import (
    DescribeJob,
    GetEntry,
    DescribeLakeRequest,
    SubmitLakeRequest
)
from omnilake.client.construct_request_definitions  import (
    DirectResponseConfig,
    SimpleResponseConfig,
    SummarizationProcessor,
    VectorLookup,
)

from omni.commands.base import Command

class QuestionCommand(Command):
    command_name='question'
    description='Perform a summarization over an archive to answer a question or goal from the user'

    def __init__(self, omnilake_app_name: Optional[str] = None,
                 omnilake_deployment_id: Optional[str] = None):
        super().__init__()
        self.omnilake = OmniLake(
            app_name=omnilake_app_name,
            deployment_id=omnilake_deployment_id,
        )

    @classmethod
    def configure_parser(cls, parser: ArgumentParser):
        lookup_group = parser.add_argument_group('lookup', 'Archive lookup instructions')
        lookup_group.add_argument('--archive', '-a', help='An archive ID to query', action='append', required=True)
        lookup_group.add_argument('--max-entries', help='The maximum number of entries to return from the lookup. Defaults to 10', default=10, type=int)
        lookup_group.add_argument('--lookup-query', help='The query to send to the lookup. Defaults to the "question" argument')
        lookup_group.add_argument('--tag', help='Prioritized tags for the lookup', action='append')
                
        processing_group = parser.add_argument_group('processing', 'Processing instructions')
        processing_group.add_argument('question', help='The question to be answered')
        processing_group.add_argument('--goal', help='Goal to be achieved. Defaults to "Answer the following question: <question>"')

        response_group = parser.add_argument_group('response', 'Response instructions')
        response_group.add_argument('--response-config', help='The response configuration to use. Defaults to "direct"', default='direct', choices=['direct', 'simple'])
        response_group.add_argument('--simple-response-prompt', help='When the "--response-config" option is set to "simple", specifies the prompt that will process the response. Defaults to "Answer the following question: <question>"')

    def _build_request(self, args) -> SubmitLakeRequest:
        """
        Build the request to send to OmniLake
        """
        goal = args.goal or f"Answer the following question: {args.question}"
        
        lookup_instructions = []

        for archive in args.archive:
            lookup_instructions.append(
                VectorLookup(
                    archive_id=archive,
                    max_entries=args.max_entries,
                    query_string=args.lookup_query or args.question,
                    prioritize_tags=args.tag,
                ))

        request = SubmitLakeRequest(
            lookup_instructions=lookup_instructions,
            processing_instructions=SummarizationProcessor(
                goal=goal,
                include_source_metadata=True,
            ),
            response_config=DirectResponseConfig() if args.response_config == 'direct' else SimpleResponseConfig(prompt=args.simple_response_prompt or goal)
        )

        return request

    def _execute_request_and_wait(self, request: SubmitLakeRequest):
        """
        Execute the request against OmniLake and wait for a response

        Keyword Arguments:
        request -- the request to execute
        """
        resp = self.omnilake.request(request)

        current_job_id = resp.response_body['job_id']
        current_job_type = resp.response_body['job_type']
        request_id = resp.response_body['lake_request_id']

        job_describe = DescribeJob(
            job_id=current_job_id,
            job_type=current_job_type,
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

        print(f'Final job status: {job_status}')

        started = datetime.fromisoformat(job_resp.response_body['started'])
        ended = datetime.fromisoformat(job_resp.response_body['ended'])

        total_run_time = ended - started

        print(f'Total run time: {total_run_time}')

        return request_id if not job_failed else None

    def _describe_result(self, request_id: str):
        """
        Describe the request result

        Keyword Arguments:
        request_id -- the request ID to describe
        """
        response = self.omnilake.request(DescribeLakeRequest(lake_request_id=request_id))

        entry_id = response.response_body['response_entry_id']

        content_resp = self.omnilake.request(GetEntry(entry_id=entry_id))

        entry_content = content_resp.response_body['content']

        print(f"Response from server\n=================\n\n{entry_content}")

    def run(self, args):
        """
        Execute the command
        """
        print(f'Requesting information against the archive(s): {args.archive}')

        request = self._build_request(args)

        request_id = self._execute_request_and_wait(request=request)

        if not request_id:
            print('Request failed to complete, check logs for more information')
            return

        self._describe_result(request_id=request_id)