'''
CLI Entry Point
'''
import argparse
import logging
import os

from dotenv import load_dotenv
from omni.commands import __all__ as available_commands

def _execute_command(args):
    """
    Execute the command requested by the user.
    """
    command_name = args.command

    if not command_name:
        print('no command provided')

        return

    if command_name not in available_commands:
        raise ValueError(f'Command {command_name} not found')
    
    command = available_commands[command_name]()

    command.run(args)

def _prepare_environment(args):
    """
    Read the environment variables from the .env file if it exists.
    Adjust some of the variables for internal use
    """
    if args.env:
        load_dotenv(dotenv_path=args.env)
    elif os.path.exists('.env'):
        load_dotenv()
    
    os.environ['DA_VINCI_APP_NAME'] = os.getenv('APP_NAME', args.app_name)
    os.environ['DA_VINCI_DEPLOYMENT_ID'] = os.getenv('DEPLOYMENT_ID', args.deployment_id)

def main():
    parser = argparse.ArgumentParser(description='OmniLake CLI')

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

    parser.set_defaults(loglevel=logging.WARNING)

    subparsers = parser.add_subparsers(dest='command')

    for _, command_class in available_commands.items():
        command_class.configure_parser(subparsers)

    args = parser.parse_args()

    _prepare_environment(args)

    logging.basicConfig(level=args.loglevel)

    _execute_command(args)