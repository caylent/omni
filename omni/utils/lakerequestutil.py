import omni.utils.jobutil as jobutil

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import (
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

    job_completed = jobutil.wait_for_completion(omnilake, job_id, job_type)

    return return_id if job_completed else None

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
