from abc import ABC, abstractmethod
from argparse import ArgumentParser

class Command(ABC):
    command_name = None
    description = None

    @classmethod
    def configure_parser(cls, parser: ArgumentParser):
        # Override this to add arguments to the command
        pass

    @abstractmethod
    def run(self, args):
        raise NotImplementedError