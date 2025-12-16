from http import HTTPStatus

from rest_framework.exceptions import ValidationError


class RaceConditionException(Exception):
    pass


class NotEnoughMineralsException(Exception):
    pass


class AdminWalletException(Exception):
    pass


class ConflictError(ValidationError):
    status_code = HTTPStatus.CONFLICT
