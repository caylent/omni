# Omni The OmniLake CLI

This repo contains the CLI to interact with an OmniLake instance.

If you're looking for the OmniLake repository and documentation, you can find it in the [caylent/omnilake](https://github.com/caylent/omnilake) repository.

## Getting started

Omni can be used as is or extended with custom commands.
For a list of pre-built custom commands, refer to the [caylent/omnilake-extensions](https://github.com/caylent/omnilake-extensions) repository.

### Prerequisites

- Python 3.12 or higher
- Poetry (Python package manager)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- Access to the AWS account where the OmniLake instance is live

### Installation

1. Clone the repository:
```bash
git clone https://github.com/caylent/omni.git
cd omni
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create an `.env` file based on the [.env.example](.env.example) file:
```bash
cp .env.example .env
```

4. Edit the `.env` file with your information:
```bash
APP_NAME='omnilake' # The name of the OmniLake app instance
DEPLOYMENT_ID='dev' # The deployment ID of the OmniLake instance

AWS_DEFAULT_REGION='us-east-1' # The default AWS region to connect
AWS_PROFILE='my-profile' # The configured profile to use for AWS CLI commands
```

## Usage

Here's how to get the Omni manual:

```bash
poetry run omni -h
```

This will show the available commands and options:
```
usage: omni.cmd [-h] [--env ENV] [--app-name APP_NAME] [--deployment-id DEPLOYMENT_ID] [--verbosity] {chain,index,question} ...

OmniLake CLI

options:
  -h, --help            show this help message and exit
  --env ENV, -e ENV     Optional .env file
  --app-name APP_NAME, --app APP_NAME
                        The name of the OmniLake app. Defaults to "omnilake"
  --deployment-id DEPLOYMENT_ID, --dep-id DEPLOYMENT_ID
                        The OmniLake deployment ID. Defaults to "dev"
  --verbosity, -v       Set the verbosity level

Command:
  {chain,index,question}
                        The command to execute
    chain               Execute a chain against OmniLake
    index               Create or update the index based on the files in the directory
    question            Perform a summarization over an archive to answer a question or goal from the user
```

### Optional Parameters

* `--env ENV, -e ENV`: allows you to load an `.env` file into the CLI, if you terminal doesn't load it automatically:

```bash
poetry run omni -e ".env" command ...
```

* `--app-name APP_NAME, --app APP_NAME`: specify the name of the OmniLake app instance if not specified in the `.env` file.
* `--deployment-id DEPLOYMENT_ID, --dep-id DEPLOYMENT_ID`: specify the deployment ID of the OmniLake instance if not specified in the `.env` file.
* `--verbosity, -v`: can be set multiple times to increase the log level:
  * `-v`: INFO
  * `-vv`: DEBUG

## Commands

Omni contains multiple commands to help you manage your OmniLake instance, archives, entries, jobs, etc.

### Index

The index command allow you to specify a directory to index all its files into a single vector archive.

Here's how to get the index command manual:

```bash
poetry run omni index -h
```

This will show the available options:

```
usage: omni.cmd index [-h] [--archive ARCHIVE] [--directory DIRECTORY] [--shallow] [--ignore IGNORE]

options:
  -h, --help            show this help message and exit
  --archive ARCHIVE, -a ARCHIVE
                        The archive to create or update the index. Defaults to the "directory" name
  --directory DIRECTORY, -D DIRECTORY
                        The directory to index files from. Defaults to the working directory
  --shallow, -s         Only index files in the root directory
  --ignore IGNORE, -i IGNORE
                        Ignore files matching the pattern. Already ignores ['.git*', '*__pycache__*', '*.pyc', 'poetry.lock', 'cdk.out*', '.DS_Store']
```

#### Optional Parameters

* `--archive ARCHIVE, -a ARCHIVE`: specify the name of the archive to create or update. If not provided, the name of the DIRECTORY will be used.
* `--directory DIRECTORY, -D DIRECTORY`: specify the root directory to load the files to index.
* `--shallow, -s`: if specified, will only load files in the root of the DIRECTORY.
* `--ignore IGNORE, -i IGNORE`: specify multiple times to ignore different file patterns.

### Question

The question command allow you to perform a recursive summarization over the data in one or more archives.

Here's how to get the question command manual:

```bash
poetry run omni question -h
```

This will show the available options:

```
usage: omni.cmd question [-h] --archive ARCHIVE [--max-entries MAX_ENTRIES] [--lookup-query LOOKUP_QUERY] [--tag TAG] [--goal GOAL] [--response-config {direct,simple}] [--simple-response-prompt SIMPLE_RESPONSE_PROMPT]
                         question

options:
  -h, --help            show this help message and exit

lookup:
  Archive lookup instructions

  --archive ARCHIVE, -a ARCHIVE
                        An archive ID to query
  --max-entries MAX_ENTRIES
                        The maximum number of entries to return from the lookup. Defaults to 10
  --lookup-query LOOKUP_QUERY
                        The query to send to the lookup. Defaults to the "question" argument
  --tag TAG             Prioritized tags for the lookup

processing:
  Processing instructions

  question              The question to be answered
  --goal GOAL           Goal to be achieved. Defaults to "Answer the following question: <question>"

response:
  Response instructions

  --response-config {direct,simple}
                        The response configuration to use. Defaults to "direct"
  --simple-response-prompt SIMPLE_RESPONSE_PROMPT
                        When the "--response-config" option is set to "simple", specifies the prompt that will process the response. Defaults to "Answer the following question: <question>"
```

#### Parameters

The parameters for the question command, are split into the three phases of a lake request:

* Lookup
  * `--archive ARCHIVE, -a ARCHIVE`: allow you to specify one or more archives to lookup entries from. At least one archive is required.
  * `--max-entries MAX_ENTRIES`: specify the maximum number of entries to load from an archive.
  * `--lookup-query LOOKUP_QUERY`: a specific query for the lookup.
  * `--tag TAG`: specify a tag to help the lookup find more precise entries.
* Processing
  * `question`: specify the question to be asked to the LLM.
  * `--goal GOAL`: your goal can be more than a simple question.
* Response
  * `--response-config {direct,simple}`: specify the responder after all the processing is done. The simple responder takes a prompt to manipulate the result.
  * `--simple-response-prompt SIMPLE_RESPONSE_PROMPT`: This is required when `--response-config simple` is used. This is the prompt to modify the contents of the resulting summarization.

### Chain

One of the most powerful tools of OmniLake is the capacity of running chains of commands.

Here's how to get the chain command manual:

```bash
poetry run omni chain -h
```

This will show the available options:

```
usage: omni.cmd chain [-h] chain_definition

positional arguments:
  chain_definition  The chain definition file to execute

options:
  -h, --help        show this help message and exit
```

#### Parameters

The chain command only take one parameter: the chain definition file.

The basic structure of a chain file is as follows:

```json
[
    {
        "conditional": false, // indicate if this lake request is conditional to previous validation
        "lake_request": {
            "lookup_instructions": [], // can contain any lookup instructions
            "processing_instructions": {}, // any processor instruction
            "response_config": {} // any response configuration
        },
        "name": "request_name_for_reference", // used to reference this request down the chain
        "validation": {} // add a validation step to the chain node
    }
]
```

You can find a complete example of a [chain file](https://github.com/caylent/omnilake/blob/main/examples/chain_file.json) in the OmniLake repository.

For more information on chain requests, refer to the OmniLake documentation.

## Extending the Available Commands

If you want to add your own commands or use the pre-built ones from the [caylent/omnilake-extensions](https://github.com/caylent/omnilake-extensions) repository, you'll need to create your own poetry project and add Omni as a dependency.

You can then add the imported commands to the `Shell` class:

```python
from omni.shell import Shell

from myshell.commands import __all__ as custom_commands
from omnilake.shell.confluence import __all__ as confluence_commands

def main():
    extra_commands = {**custom_commands, **confluence_commands}

    Shell(more_commands=extra_commands).run()
```

All commands need to inherit from the `CommandClass`:

```python
from argparse import ArgumentParser
from omni.commands.base import Command

class MyCommand(Command):
    command_name = 'my-command'
    description = 'A cool description of my command'

    def __init__():
        super().__init__()
        # Initialize stuff

    @classmethod
    def configure_parser(cls, parser: ArgumentParser):
        parser.add_argument('--foo', help='A super useful argument')

    def run(self, args):
        # Do your thing ;)
```

## Util Functions

Omni exposes a few utility scripts for common tasks in OmniLake. You can find them under the `/omni/utils` directory.

### fileutil.py

```python
def collect_files(directory: Union[str, Path], ignore_patterns: List[str] = [], recursive: bool = True) -> List[Path]:
    """
    Collect all files in a directory, respecting ignore patterns.
    
    Args:
    directory -- the directory to collect files from
    ignore_patterns -- a list of patterns to ignore (gitignore-style)
    recursive -- whether to search recursively or not
    """    
```

### lakerequestutil.py

```python
def execute_and_wait(omnilake: OmniLake, request: LakeRequest, return_id_property: str) -> str:
    """
    Execute a lake request and wait for it to complete

    Keyword arguments:
    omnilake -- the OmniLake client
    request -- the request to execute
    """

def describe_result(omnilake: OmniLake, lake_request_id: str, request_name: str = None):
    """
    Describe the resulting content of a lake request

    Keyword arguments:
    omnilake -- the OmniLake client
    lake_request_id -- the ID of the lake request
    """
```

## Contributing

We welcome contributions!

If you found a bug or want to submit a PR, this repository follows the same [contributing rules](https://github.com/caylent/omnilake/blob/main/CONTRIBUTING) as OmniLake's.