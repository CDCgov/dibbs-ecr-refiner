from typing import Literal, get_args

# NOTE:
# FILE SIZE LIMITS
# =============================================================================
# every layer enforces or reports these, which is why they live in `core`:
# * `api/validation/file_validation.py` rejects oversized uploads
# * `services/file_io.py` checks a ZIP's uncompressed total before extracting
# * `api/v1/simulator/model.py` reports the ceiling back to the client
#
# they were defined in `api/validation/` and reached for from the other two.
# that made `api` import `services.file_io` while `file_io` imported back, so
# the two reads in `file_io` had to be function-local to break the cycle
#
# the type literals exist so that Orval picks the values up and codegens them
# to the frontend -- the user-facing limit strings are driven from here

MEGABYTES = 1024 * 1024

DiffMax = Literal[2]
UncompressedMax = Literal[15]

DIFF_RENDERING_MAX_MB = get_args(DiffMax)[0]
UNCOMPRESSED_MAX_MB = get_args(UncompressedMax)[0]

DIFF_RENDERING_MAX_BYTES = DIFF_RENDERING_MAX_MB * MEGABYTES
UNCOMPRESSED_MAX_BYTES = UNCOMPRESSED_MAX_MB * MEGABYTES
