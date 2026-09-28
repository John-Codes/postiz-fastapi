class PostizError(Exception):
    """A call to the Postiz API did not succeed.

    Carries the status code Postiz returned, or 503 when Postiz could not be
    reached at all. `detail` is safe to show a caller: it is Postiz's own
    message, never our API key or internal addresses.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail

    @property
    def http_status(self) -> int:
        """Status to return to our own caller.

        Upstream failures are reported as 502 so clients can tell "Postiz is
        unhappy" apart from "this service is broken". 503 means Postiz was
        unreachable, which is a different operational problem.
        """
        if self.status_code == 503:
            return 503
        return 502
