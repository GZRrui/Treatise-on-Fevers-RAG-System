class ApplicationNotReadyError(RuntimeError):
    """Raised when a use case is called before its dependencies are ready."""


class IndexBuildError(RuntimeError):
    """Raised when an index build cannot be completed."""
