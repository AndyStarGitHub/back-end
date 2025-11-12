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


class AppError(Exception):
    pass


class NotAuthenticated(AppError):
    pass


class InvalidCredentials(AppError):
    pass


class TokenInvalid(AppError):
    pass


class Forbidden(AppError):
    pass


class NotFound(AppError):
    pass


class Conflict(AppError):
    pass

