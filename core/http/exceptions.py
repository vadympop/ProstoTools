class HTTPException(BaseException):
    def __init__(self, json):
        self.json = json


class ClientException(BaseException):
    pass


class Unauthorized(HTTPException):
    pass


class NotFound(HTTPException):
    pass


class Forbidden(HTTPException):
    pass


class BadRequest(HTTPException):
    pass


class ServerError(HTTPException):
    pass


class RateLimited(HTTPException):
    pass