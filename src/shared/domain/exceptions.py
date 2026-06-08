class DomainError(Exception):
    def __init__(self, message: str, code: str = "DOMAIN_ERROR", status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class NotFoundError(DomainError):
    def __init__(self, message: str, code: str = "NOT_FOUND") -> None:
        super().__init__(message=message, code=code, status_code=404)


class ConflictError(DomainError):
    def __init__(self, message: str, code: str = "CONFLICT") -> None:
        super().__init__(message=message, code=code, status_code=409)
