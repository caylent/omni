import omni.utils.lakerequestutil as lakerequestutil

from argparse import ArgumentParser
from typing import Optional

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import SubmitLakeRequest
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

    def run(self, args):
        """
        Execute the command
        """
        print(f'Requesting information against the archive(s): {args.archive}')

        request = self._build_request(args)

        request_id = lakerequestutil.execute_and_wait(
            omnilake=self.omnilake,
            request=request,
            return_id_property='lake_request_id',
        )

        if not request_id:
            print('Request failed to complete, check logs for more information')
            return

        lakerequestutil.describe_result(
            omnilake=self.omnilake,
            lake_request_id=request_id
            )