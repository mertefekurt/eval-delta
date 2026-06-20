"""domain-specific exceptions for predictable CLI failures."""


class EvalDeltaError(Exception):
    """base exception for expected eval-delta failures."""


class InputError(EvalDeltaError):
    """raised when evaluation input cannot be loaded or validated."""


class ConfigurationError(EvalDeltaError):
    """raised when comparison settings are invalid."""
