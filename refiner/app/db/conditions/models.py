from dataclasses import dataclass, field
from typing import TypedDict


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
