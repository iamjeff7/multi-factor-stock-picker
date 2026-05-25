"""Framework exception hierarchy."""


class MFSPError(Exception):
    """Base exception for all framework errors."""


class ValidationError(MFSPError):
    """Raised when schema or data validation fails."""


class ConfigurationError(MFSPError):
    """Raised when configuration is invalid or missing."""


class MissingSignalDataError(MFSPError):
    """Raised when a signal cannot evaluate due to missing inputs."""
