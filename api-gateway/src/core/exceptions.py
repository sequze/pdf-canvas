from shared import AppError


class AuthError(AppError):
    message = "Authentication error"


class InvalidTokenError(AuthError):
    message = "Invalid token"


class TokenExpiredError(AuthError):
    message = "Token expired"


class ForbiddenError(AppError):
    message = "Forbidden"


class NoAccessError(ForbiddenError):
    message = "You do not have access to this resource"


class EmailNotExistsError(AuthError):
    message = "Email does not exist"


class InvalidPasswordError(AuthError):
    message = "Invalid password"


class EmailAlreadyExistsError(AuthError):
    message = "Email already exists"


class NotFoundError(AppError):
    message = "Resource not found"


class ConflictError(AppError):
    message = "Conflict"


class EntityTooLargeError(AuthError):
    """413 status code error"""

    message = "Entity is too large"
