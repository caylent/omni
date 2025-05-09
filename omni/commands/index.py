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
from omni.utils.strutil import chunk_string_by_bytes
from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import (
    AddEntry,
    AddSource,
    CreateArchive,
    VectorArchiveConfiguration,
)


CHUNK_SIZE = 131072  # 128 kB

logger = getLogger(__name__)

class IndexCommand(Command):
    command_name='index'
    description='Create or update the index based on the files in the directory'

    ignore_patterns=['.git*', '*__pycache__*', '*.pyc', 'poetry.lock', 'cdk.out*', '.DS_Store']

    def __init__(self):
        self.omnilake = OmniLake()

    @classmethod
    def configure_parser(cls, parser: ArgumentParser):
        parser.add_argument('--archive', '-a', help='The archive to create or update the index. Defaults to the "directory" name')
        parser.add_argument('--directory', '-D', help='The directory to index files from. Defaults to the working directory', default=os.getcwd())
        parser.add_argument('--shallow', '-s', help='Only index files in the root directory', action='store_true')
        parser.add_argument('--ignore', '-i', help=f'Ignore files matching the pattern. Already ignores {cls.ignore_patterns}', action='append')
        parser.add_argument('--skip', '-S', help='Skip the first X files in the directory', type=int, default=0)
        parser.add_argument('--pattern', '-p', help='Only index files matching the pattern', action='append')
        parser.add_argument('--file', '-f', help='Only index these specific files', action='append')

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

    def _process_file_list(self, archive_name, directory, file_list: List[Path], skip: int = 0) -> List[Path]:
        """
        Process the list of files to index and return a list of failed files

        Keyword arguments:
        archive_name -- the archive ID
        directory -- the base directory that holds the files
        file_list -- the list of files to index
        """
        total_files = len(file_list)
        failed_files = []

        for file_number, collected_file in enumerate(iterable=file_list, start=1):
            relative_to_base = str(collected_file.relative_to(directory))

            if file_number <= skip:
                print(f'[{file_number}/{total_files}] Skipping {relative_to_base} by user choice')
                continue

            file_contents = collected_file.read_bytes()

            if len(file_contents) == 0:
                print(f'[{file_number}/{total_files}] Skipped {relative_to_base} ... empty file')
                continue

            if collected_file.name.endswith('.pdf'):
                print(f'[{file_number}/{total_files}] Detected PDF file, extracting text...')

                success = self._index_pdf_file(collected_file, relative_to_base, archive_name, file_number, total_files)
                
                failed_files.append(collected_file) if not success else None
                continue

            decoded_contents = file_contents.decode(encoding='utf-8', errors='ignore')

            # Split the file into chunks
            chunks = chunk_string_by_bytes(decoded_contents, CHUNK_SIZE)

            if len(chunks) == 0:
                print(f'[{file_number}/{total_files}] Skipped {relative_to_base} ... empty file')
                continue

            if len(chunks) > 1:
                success = self._index_chunks(chunks, archive_name, collected_file.name, relative_to_base, file_number, total_files)
                
                failed_files.append(collected_file) if not success else None
                continue

            # index single chunk file
            success = self._index_file(
                archive_name=archive_name,
                file_contents=decoded_contents,
                file_name=collected_file.name,
                file_path=relative_to_base,
            )

            if success:
                print(f'[{file_number}/{total_files}] Added {relative_to_base}')
            else:
                print(f'[{file_number}/{total_files}] Failed to add {relative_to_base}')
                failed_files.append(collected_file)

        return failed_files

    def _index_pdf_file(self, collected_file: Path, relative_to_base: str, archive_name: str, file_number: int, total_files: int) -> bool:
        pdf_reader = pypdf.PdfReader(stream=collected_file)

        success = True

        for page_number, page in enumerate(iterable=pdf_reader.pages, start=1):
            success = self._index_file(
                archive_name=archive_name,
                file_contents=page.extract_text(),
                file_name=collected_file.name,
                file_path=relative_to_base,
                page_number=page_number,
            )

            if success:
                print(f'[{file_number}/{total_files}] Added {relative_to_base} page {page_number}')
            else:
                print(f'[{file_number}/{total_files}] Failed to add {relative_to_base} page {page_number}')
                break

        return success
    
    def _index_chunks(self, chunks: List[str], archive_name: str, file_name: str, file_path: str, file_number: int, total_files: int) -> bool:
        success = True

        for chunk_number, chunk in enumerate(iterable=chunks, start=1):
            success = self._index_file(
                archive_name=archive_name,
                file_contents=chunk,
                file_name=file_name,
                file_path=file_path,
                page_number=chunk_number,
            )

            if success:
                print(f'[{file_number}/{total_files}] Added {file_path} chunk {chunk_number}')
            else:
                print(f'[{file_number}/{total_files}] Failed to add {file_path} chunk {chunk_number}')
                break

        return success

    def _index_file(self, archive_name: str, file_contents: str, file_name: str, file_path: str,
                    page_number: Optional[int] = None) -> bool:
        """
        Index a file and return if it was successful

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

        try:
            source_result = self.omnilake.request(source)

            source_rn = source_result.response_body['resource_name']

            entry = AddEntry(
                content=file_contents,
                sources=[source_rn],
                destination_archive_id=archive_name,
                original_of_source=source_rn,
            )

            self.omnilake.request(entry)
            return True
        except Exception as e:
            logger.error(f'Failed to index {file_name} ({file_path}). Error: {e}')
            return False

    def _recursive_process(self, archive_name: str, directory: str, file_list: List[Path], skip: int = 0) -> List[Path]:
        start = time.time()

        print(f'{len(file_list)} file(s) found. Processing...')
        
        failed_files = self._process_file_list(archive_name=archive_name, directory=directory, file_list=file_list, skip=skip)

        end = time.time()
        
        print(f'Processed {len(file_list)-len(failed_files)} file(s) in', timedelta(seconds=end-start))

        failed = len(failed_files)

        if failed > 0:
            print(f'Failed to index {failed} file(s)')
            response = input('Do you want to try again? (y/n)')

            if response.lower() == 'y':
                self._recursive_process(archive_name=archive_name, directory=directory, file_list=failed_files, skip=0)
            else:
                print('Listing failed files. Add to the command line with -f option to retry')
                for i, failed_file in enumerate(iterable=failed_files,start=1):
                    print(f'-f "{failed_file.absolute()}"')

    def run(self, args):
        directory_path = Path(args.directory).resolve(strict=True)
        archive_id = args.archive or directory_path.name

        if not directory_path.is_dir():
            raise ValueError(f'{args.directory} is not a directory')

        if not directory_path.exists():
            raise ValueError(f'{args.directory} does not exist')
        
        directory_abspath = directory_path.absolute()

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
        
        if args.file:
            collected_files = [Path(file).resolve(strict=True) for file in args.file]
            collected_files = [file for file in collected_files if file.exists() and file.is_file()]
        else:
            collected_files = collect_files(directory=directory_path, patterns=args.pattern if args.pattern else ['*'], recursive=not args.shallow, ignore_patterns=self.ignore_patterns)

        self._recursive_process(archive_name=archive_id, directory=directory_abspath, file_list=collected_files, skip=args.skip)
        
        print('Indexing complete')
