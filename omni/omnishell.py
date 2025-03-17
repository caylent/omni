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
        
        parser.add_argument('--verbosity, -v', help='Set the verbosity level', default=0, action='count')
        parser.add_argument('--base-dir', '-D', help='Base Directory to work off index', default=os.getcwd())

        subparsers_action = parser.add_subparsers(dest='command', help='The command to execute', required=True)

        for _, command_class in self.available_commands.items():
            subparser = subparsers_action.add_parser(command_class.command_name, help=command_class.description)
            command_class.configure_parser(subparser)

        return parser.parse_args()
    
    def _prepare_environment(self, args) -> None:
        """
        Read the environment variables from the .env file provided.
        Adjust some of the variables for internal use.
        Prepare the environment for execution.
        """
        if args.env:
            load_dotenv(dotenv_path=args.env)
        
        os.environ['DA_VINCI_APP_NAME'] = os.getenv('APP_NAME', args.app_name)
        os.environ['DA_VINCI_DEPLOYMENT_ID'] = os.getenv('DEPLOYMENT_ID', args.deployment_id)
        os.environ['OMNILAKE_APP_NAME'] = os.getenv('APP_NAME', args.app_name)
        os.environ['OMNILAKE_DEPLOYMENT_ID'] = os.getenv('DEPLOYMENT_ID', args.deployment_id)

        if(args.verbosity >= 2):
            args.loglevel = logging.DEBUG
        elif(args.verbosity >= 1):
            args.loglevel = logging.INFO
        else:
            args.loglevel = logging.NOTSET

        logging.basicConfig(level=args.loglevel)

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
        args = self._prepare_arguments()

        self._prepare_environment(args)

        self._execute_command(args)
