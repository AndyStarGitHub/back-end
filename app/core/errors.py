class DomainError(Exception):
    ...


class NotFound(DomainError):
    ...


class Conflict(DomainError):
    ...
