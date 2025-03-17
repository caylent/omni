'''
OmniShell is the extendable class for running commands to OmniLake
'''
import logging
import os

from argparse import ArgumentParser
from dotenv import load_dotenv
from omni.commands import __all__ as core_commands

class OmniShell:
    def __init__(self, more_commands: dict = None):
        self.available_commands = core_commands
        if more_commands:
            self.available_commands.update(more_commands)

    def _prepare_arguments(self) -> ArgumentParser:
        """
        Prepare the base arguments for the CLI
        """
        parser = ArgumentParser(description='OmniLake CLI')

        parser.add_argument('--env', '-e', help='Optional .env file')
        parser.add_argument('--app-name', '--app', help='The name of the OmniLake app. Defaults to "omnilake"', default="omnilake")
        parser.add_argument('--deployment-id', '--dep-id', help='The OmniLake deployment ID. Defaults to "dev"', default="dev")
        parser.add_argument('--base-dir', '-D', help='Base Directory to work off index', default=os.getcwd())

        verbose = parser.add_mutually_exclusive_group()

        verbose.add_argument('-V', dest='loglevel', action='store_const',
                             const=logging.INFO,
                             help='Set log-level to INFO.')

        verbose.add_argument('-VV', dest='loglevel', action='store_const',
                             const=logging.DEBUG,
                             help='Set log-level to DEBUG.')
        
        subparsers = parser.add_subparsers(dest='command', help='The command to execute')

        for _, command_class in self.available_commands.items():
            command_class.configure_parser(subparsers)

        return parser.parse_args()
    
    def _prepare_environment(self, args) -> None:
        """
        Read the environment variables from the .env file provided.
        Adjust some of the variables for internal use.
        """
        if args.env:
            load_dotenv(dotenv_path=args.env)
        
        os.environ['DA_VINCI_APP_NAME'] = os.getenv('APP_NAME', args.app_name)
        os.environ['DA_VINCI_DEPLOYMENT_ID'] = os.getenv('DEPLOYMENT_ID', args.deployment_id)
        os.environ['OMNILAKE_APP_NAME'] = os.getenv('APP_NAME', args.app_name)
        os.environ['OMNILAKE_DEPLOYMENT_ID'] = os.getenv('DEPLOYMENT_ID', args.deployment_id)

    def _execute_command(self, args) -> None:
        """
        Execute the command requested by the user.
        """
        command_name = args.command

        if not command_name:
            print('No command provided')
            return

        if command_name not in self.available_commands:
            raise ValueError(f'Command {command_name} not found')
        
        command = self.available_commands[command_name]()

        command.run(args)

    def run(self) -> None:
        """
        Run the CLI
        """
        parser = self._prepare_arguments()

        args = self._prepare_command_arguments(parser)

        self._prepare_environment(args)

        logging.basicConfig(level=args.loglevel)

        self._execute_command(args)
