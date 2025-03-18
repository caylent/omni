from logging import getLogger

from omnilake.client.client import OmniLake
from omnilake.client.request_definitions import CreateSourceType

logger = getLogger(__name__)

def create_source_type(omnilake: OmniLake, name: str, description: str, required_fields: List[str]):
    """
    Create the source type if it doesn't exist

    Keyword arguments:
    omnilake -- the OmniLake client
    name -- the name of the source type
    description -- the description of the source type
    required_fields -- the required fields for the source type
    """
    try:
        source_type = CreateSourceType(
            name=name,
            description=description,
            required_fields=required_fields,
        )

        omnilake.request(source_type)

        print(f'Source type "{name}" created')
    except Exception as e:
        if "Source type already exists" in str(e):
            logger.info(f'Source type "{name}" already exists')
        else:
            raise