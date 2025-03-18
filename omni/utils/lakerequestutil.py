import time

from datetime import datetime

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import (
    DescribeJob, 
    LakeRequest, 
    DescribeLakeRequest, 
    GetEntry
)

def execute_and_wait(omnilake: OmniLake, request: LakeRequest, return_id_property: str) -> str:
    """
    Execute a lake request and wait for it to complete

    Keyword arguments:
    omnilake -- the OmniLake client
    request -- the request to execute
    """
    resp = omnilake.request(request)

    job_id = resp.response_body['job_id']
    job_type = resp.response_body['job_type']
    return_id = resp.response_body[return_id_property]

    job_describe = DescribeJob(
        job_id=job_id,
        job_type=job_type,
    )

    job_resp = omnilake.request(job_describe)

    job_status = job_resp.response_body['status']

    job_failed = False

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

    print(f'Total run time: {total_run_time}')

    return return_id if not job_failed else None

def describe_result(omnilake: OmniLake, lake_request_id: str, request_name: str = None):
    """
    Describe the resulting content of a lake request

    Keyword arguments:
    omnilake -- the OmniLake client
    lake_request_id -- the ID of the lake request
    """
    response = omnilake.request(DescribeLakeRequest(lake_request_id=lake_request_id))

    entry_id = response.response_body['response_entry_id']

    content_resp = omnilake.request(GetEntry(entry_id=entry_id))

    entry_content = content_resp.response_body['content']

    if request_name:
        print(f"Request \"{request_name}\" Response\n=================\n\n{entry_content}")
    else:
        print(f"Response from server\n=================\n\n{entry_content}")
