from pydantic import BaseModel, validator


class CacheUpdateInRequest(BaseModel):
    entity: str
    query: dict
    data: dict

    @validator('entity')
    def entity_validator(cls, value):
        if value not in ('guilds', 'users'):
            raise ValueError('Invalid entity')

        return value