class AppError(Exception):
    message = "App error"

    def __init__(self, detail: str | None = None):
        super().__init__(detail or self.message)
        self.detail = detail or self.message


class RabbitError(AppError):
    message = "Error with RabbitMQ"
