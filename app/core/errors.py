class DomainError(Exception):
    ...


class NotFound(DomainError):
    ...


class Conflict(DomainError):
    ...


class Forbidden:
    pass


class BadRequest:
    pass


class AuthError(Exception):
    pass


class InvalidCredentials(AuthError):
    pass


class InactiveUser(AuthError):
    pass
