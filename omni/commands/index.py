import os
import time
import pypdf

import omni.utils.archiveutil as archiveutil
import omni.utils.sourcetypeutil as sourcetypeutil

from pathlib import Path
from logging import getLogger
from typing import List, Optional
from argparse import ArgumentParser
from datetime import timedelta

from omni.commands.base import Command
from omni.utils.fileutil import collect_files
from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import (
    AddEntry,
    AddSource,
    CreateArchive,
    VectorArchiveConfiguration,
)

logger = getLogger(__name__)

class RefreshIndexCommand(Command):
    command_name='index'
    description='Create or update the index based on the files in the directory'

    ignore_patterns=['.git*', '*__pycache__*', '*.pyc', 'poetry.lock', 'cdk.out*', '.DS_Store']

    def __init__(self, omnilake_app_name: Optional[str] = None,
                 omnilake_deployment_id: Optional[str] = None):
        super().__init__()
        self.omnilake = OmniLake(
            app_name=omnilake_app_name,
            deployment_id=omnilake_deployment_id,
        )

    @classmethod
    def configure_parser(cls, parser: ArgumentParser):
        parser.add_argument('--archive', '-a', help='The archive to create or update the index. Defaults to the "directory" name')
        parser.add_argument('--directory', '-D', help='The directory to index files from. Defaults to the working directory', default=os.getcwd())
        parser.add_argument('--shallow', '-s', help='Only index files in the root directory', action='store_true')
        parser.add_argument('--ignore', '-i', help=f'Ignore files matching the pattern. Already ignores {cls.ignore_patterns}', action='append')

    def _create_archive(self, directory: str, archive_id: str):
        """
        Create an archive if it doesn't exist

        Keyword arguments:
        directory -- the directory being indexed
        archive_name -- the archive ID
        """
        archive = CreateArchive(
            archive_id=archive_id,
            configuration=VectorArchiveConfiguration(),
            description=f'Archive for local file directory {directory} from someone\'s computer :shrug:',
        )

        archiveutil.create_archive_and_wait(self.omnilake, archive)

    def _process_file_list(self, archive_name, directory, file_list: List[Path]):
        """
        Process the list of files to index

        Keyword arguments:
        archive_name -- the archive ID
        directory -- the base directory that holds the files
        file_list -- the list of files to index
        """
        for collected_file in file_list:
            relative_to_base = str(collected_file.relative_to(directory))

            file_contents = collected_file.read_bytes()

            if len(file_contents) == 0:
                print(f'Skipped {relative_to_base} ... empty file')
                continue

            if collected_file.name.endswith('.pdf'):
                print('Detected PDF file, extracting text...')

                pdf_reader = pypdf.PdfReader(stream=collected_file)

                print('Splitting PDF into pages...')

                for page_number, page in enumerate(pdf_reader.pages):
                    self._index_file(
                        archive_name=archive_name,
                        file_contents=page.extract_text(),
                        file_name=collected_file.name,
                        file_path=relative_to_base,
                        page_number=page_number,
                    )

                    print(f'Added {relative_to_base} page {page_number}')
                continue

            decoded_contents = file_contents.decode(encoding='utf-8', errors='ignore')

            self._index_file(
                archive_name=archive_name,
                file_contents=decoded_contents,
                file_name=collected_file.name,
                file_path=relative_to_base,
            )

            print(f'Added {relative_to_base}')

    def _index_file(self, archive_name: str, file_contents: str, file_name: str, file_path: str,
                    page_number: Optional[int] = None):
        """
        Index a file

        Keyword arguments:
        archive_name -- the name of the archive
        file_contents -- the contents of the file
        file_name -- the name of the file
        file_path -- the path of the file
        page_number -- the page number of the file (default None)
        """
        full_file_name = file_name

        if page_number:
            full_file_name = f'{file_name}.{page_number}'

        source = AddSource(
            source_type='local_file',
            source_arguments={
                'file_name': full_file_name,
                'file_extension': file_name.split('.')[-1],
                'full_file_path': file_path,
            },
        )

        source_result = self.omnilake.request(source)

        source_rn = source_result.response_body['resource_name']

        entry = AddEntry(
            content=file_contents,
            sources=[source_rn],
            destination_archive_id=archive_name,
            original_of_source=source_rn,
        )

        self.omnilake.request(entry)

    def run(self, args):
        directory_path = Path(args.directory).resolve(strict=True)
        archive_id = args.archive or directory_path.name

        if not directory_path.is_dir():
            raise ValueError(f'{args.directory} is not a directory')

        if not directory_path.exists():
            raise ValueError(f'{args.directory} does not exist')
            
        directory_abspath = directory_path.absolute()
        start = time.time()

        print(f'Index files in {directory_abspath} to archive {archive_id}')

        # Create the archive if it doesn't exist
        # archive should enforce latest version
        self._create_archive(directory=directory_abspath, archive_id=archive_id)

        # Create the source type if it doesn't exist
        sourcetypeutil.create_source_type(
            omnilake=self.omnilake, 
            name='local_file', 
            description='A file uploaded from a local system', 
            required_fields=['file_name', 'full_file_path', 'file_extension']
        )
        
        if args.ignore:
            self.ignore_patterns.extend(args.ignore)
        
        collected_files = collect_files(directory=directory_path, recursive=not args.shallow, ignore_patterns=self.ignore_patterns)

        print(f'{len(collected_files)} file(s) found. Processing...')

        # Iterate over the files in the base directory and load them into the archive        
        self._process_file_list(archive_name=archive_id, directory=directory_abspath, file_list=collected_files)

        end = time.time()
        
        print(f'Processed {len(collected_files)} file(s) in', timedelta(seconds=end-start))
        print('Indexing complete')
