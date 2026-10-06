"""
Shared result reporting for the verify checks.

Checks return results rather than printing as they go, so a run reports every
failure instead of stopping at the first one. Exit status is what CI reads.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Result:
    """
    The outcome of a single check.

    Attributes:
        title: What was checked, phrased as the property being asserted.
        passed: Whether the property held.
        detail: One line of evidence, shown whether it passed or failed.
        failures: Specific offending items, shown only on failure and capped
            when rendered so a systemic problem does not bury the summary.
    """

    title: str
    passed: bool
    detail: str
    failures: list[str] = field(default_factory=list)


def render(results: list[Result], *, max_failures: int = 10) -> int:
    """
    Print a report and return the exit code CI should use.

    Args:
        results: Every check that ran.
        max_failures: How many offending items to list per failed check.

    Returns:
        0 if every check passed, 1 otherwise.
    """

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}  {result.title}")
        print(f"      {result.detail}")
        for item in result.failures[:max_failures]:
            print(f"        - {item}")
        if len(result.failures) > max_failures:
            print(f"        ... and {len(result.failures) - max_failures:,} more")
        print()

    failed = [result for result in results if not result.passed]
    if failed:
        print(f"{len(failed)} of {len(results)} checks failed.")
        return 1

    print(f"All {len(results)} checks passed.")
    return 0
