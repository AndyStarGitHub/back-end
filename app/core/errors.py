class DomainError(Exception):
    ...


class NotFound(DomainError):
    ...


class Conflict(DomainError):
    ...


class Forbidden:
    ...


class BadRequest:
    ...


class AuthError(Exception):
    ...


class InvalidCredentials(AuthError):
    ...


class InactiveUser(AuthError):
    ...


class AppError(Exception):
    ...


class NotAuthenticated(AppError):
    ...


class InvalidCredentials(AppError):
    ...


class TokenInvalid(AppError):
    ...


class Forbidden(AppError):
    ...


class NotFound(AppError):
    ...


class Conflict(AppError):
    ...


class TokenDecodeError(Exception):
    ...


class UnprocessableEntity(AppError):
    def __init__(self, detail):
        self.detail = detail
        super().__init__("Unprocessable Entity")
