import omni.utils.jobutil as jobutil

from logging import getLogger
from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import CreateArchive

logger = getLogger(__name__)

def create_archive_and_wait(omnilake: OmniLake, archive: CreateArchive):
    """
    Create an archive and wait for it to finish provisioning

    Keyword arguments:
    omnilake -- the OmniLake client
    archive -- the archive to create
    """
    archive_id = archive.attributes['archive_id']
    
    try:
        response = omnilake.request(archive)

        job_id = response.response_body['job_id']
        job_type = response.response_body['job_type']

        print('Provisioning archive...')

        job_completed = jobutil.wait_for_completion(omnilake, job_id, job_type)
        if(job_completed):
            print(f'Archive "{archive_id}" ready')
    except Exception as e:
        if "Archive already exists" in str(e):
            logger.info(f'Archive "{archive_id}"already exists')
        else:
            raise