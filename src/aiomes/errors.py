class ErrorHandler(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f'{self.__class__.__name__}: {self.message}'


class InvalidCredentialsError(ErrorHandler):
    def __init__(self, message: str = "Неверный логин / пароль"):
        super().__init__(message)


class Invalid2FACode(ErrorHandler):
    def __init__(self, message: str = "Неверный 2FA код"):
        super().__init__(message)


class RequestError(ErrorHandler):
    def __init__(self, error_code, message: str = "Ошибка запроса"):
        self.error_code = error_code
        super().__init__(f'{message} ({error_code})')


class UnknownError(ErrorHandler):
    def __init__(self, message: str = "Неизвестная ошибка!"):
        super().__init__(message)
