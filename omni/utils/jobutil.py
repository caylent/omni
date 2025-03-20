import time

from datetime import datetime

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import DescribeJob

def wait_for_completion(omnilake: OmniLake, job_id: str, job_type: str):
    """
    Wait for a job to complete and return if it was successful

    Keyword arguments:
    omnilake -- the OmniLake client
    job_id -- the ID of the job
    job_type -- the type of the job
    """
    job_describe = DescribeJob(
        job_id=job_id,
        job_type=job_type,
    )

    job_resp = omnilake.request(job_describe)

    job_status = job_resp.response_body['status']

    job_failed = job_status == 'FAILED'

    while job_status != 'COMPLETED':
        time.sleep(10)

        job_resp = omnilake.request(job_describe)

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

    print(f'Total job run time: {total_run_time}')

    return not job_failed
