from typing import Literal

# NOTE:
# these spell the exact strings we persist for a configuration -- what lands in
# `configurations.status`, `configurations_sections.action` and friends. they live in
# `core` because every layer reads them: `api/` validates request bodies against them,
# `db/` types the rows they come back on, and `services/ecr/` branches on them while
# refining a document with no database in reach. a home under `db/` would make the
# refinement core import from `app.db` just to spell a literal

type SectionAction = Literal["retain", "refine"]

type NarrativeAction = Literal["retain", "remove", "reconstruct", "keep_on_match"]

type ConfigurationStatus = Literal["draft", "inactive", "active"]

type SectionType = Literal["standard", "custom"]

# `ConfigurationCodeStatus` is what we persist and accept on the wire;
# `ConfigurationCodeStatusLabel` is how the client renders it in a filter chip
type ConfigurationCodeStatus = Literal["included", "excluded"]
type ConfigurationCodeStatusLabel = Literal["Included", "Excluded"]
