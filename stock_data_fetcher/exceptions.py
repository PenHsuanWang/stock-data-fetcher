class FetcherError(Exception):
    """Base exception for fetcher related errors."""


class ValidationError(FetcherError):
    """Raised when user input (symbols or dates) is invalid."""


class DownloadError(FetcherError):
    """Raised when yfinance download returns empty or fails."""


class OutputError(FetcherError):
    """Raised when writing output files fails."""
