from dataclasses import dataclass, field
from typing import Any, TypedDict

# NOTE:
# ADR 0016 rule 3 names three boundaries and gives two of them a home: `Db*` lives in
# `app/db` and `*Response`/`*Input` in `app/api`. the third -- `*Payload`/`*Metadata`,
# what crosses to the Lambda via S3 -- had no home, so `app/db` absorbed it by default.
# that is why `Dockerfile.lambda` used to `COPY app/db`: the Lambda cannot reach a
# database at all, and every name it imported from there was an S3 concern filed under
# the wrong layer.
#
# these shapes belong in `core` because both sides of the boundary need them and neither
# side is the other's dependency: `services/` writes them during activation, the Lambda
# reads them back on a cold start, and `ops/reactivations/` regenerates them. a home
# under `services/` or `db/` would make one reader import the other's layer

CURRENT_ACTIVE_CONFIG_SCHEMA_VERSION = 1


class ConditionMapValueDict(TypedDict):
    """
    Typed dictionary version of a ConditionMapValue.
    """

    canonical_url: str
    name: str
    tes_version: str


@dataclass(frozen=True)
class ConditionMapValue:
    """
    Condition data mapped to an RSG.
    """

    canonical_url: str
    name: str
    tes_version: str

    @classmethod
    def from_dict(cls, data: ConditionMapValueDict) -> "ConditionMapValue":
        """
        Converts a payload map value dictionary into an object.

        Args:
            data (ConditionMapValueDict): Payload map data as a dict

        Returns:
            ConditionMapValue: Payload value as an object.
        """
        return cls(
            canonical_url=data["canonical_url"],
            name=data["name"],
            tes_version=data["tes_version"],
        )


# Map an RSG to CG data
@dataclass
class ConditionMappingPayload:
    """
    Maps RSG code -> ConditionMapValue.
    """

    mappings: dict[str, ConditionMapValue] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls, data: dict[str, ConditionMapValueDict]
    ) -> "ConditionMappingPayload":
        """
        Converts a payload dictionary into an object.

        Args:
            data (dict[str, ConditionMapValueDict]): The payload as a dictionary.

        Returns:
            ConditionMappingPayload: The payload object.
        """
        return cls(
            mappings={
                rsg: ConditionMapValue.from_dict(value) for rsg, value in data.items()
            }
        )

    def to_dict(self) -> dict[str, ConditionMapValueDict]:
        """
        Converts the payload object back into a dictionary.
        """

        return {
            rsg: {
                "canonical_url": value.canonical_url,
                "name": value.name,
                "tes_version": value.tes_version,
            }
            for rsg, value in self.mappings.items()
        }


@dataclass(frozen=True)
class ConfigurationStoragePayload:
    """
    The model for a configuration that is being written to S3.

    Contains the enriched code_system_sets required for refinement,
    along with section processing and included condition RSG code, and
    the active payload schema version.
    """

    schema_version: int
    sections: list[dict[str, Any]]
    included_condition_rsg_codes: set[str]
    code_system_sets: dict[str, list[dict[str, str]]]

    def to_dict(self) -> dict:
        """
        Returns the ConfigurationStoragePayload represented as a dict.

        Returns:
            dict: ConfigurationStoragePayload represented as a dict
        """

        result = {
            "schema_version": self.schema_version,
            "code_system_sets": self.code_system_sets,
            "sections": self.sections,
            "included_condition_rsg_codes": sorted(self.included_condition_rsg_codes),
        }

        return result


@dataclass(frozen=True)
class ConfigurationStorageMetadata:
    """
    The model for configuration metadata that is being written to S3.
    """

    condition_name: str
    canonical_url: str
    tes_version: str
    jurisdiction_id: str
    configuration_version: int
    child_rsg_snomed_codes: list[str]

    def to_dict(self) -> dict:
        """
        Returns the ConfigurationStorageMetadata represented as a dict.

        Returns:
            dict: ConfigurationStorageMetadata represented as a dict
        """
        return {
            "condition_name": self.condition_name,
            "canonical_url": self.canonical_url,
            "tes_version": self.tes_version,
            "jurisdiction_id": self.jurisdiction_id,
            "configuration_version": self.configuration_version,
            "child_rsg_snomed_codes": sorted(self.child_rsg_snomed_codes),
        }
