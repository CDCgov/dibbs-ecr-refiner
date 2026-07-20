from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class SectionOverride:
    """
    One section-processing change applied via update_section_processing.
    """

    current_code: str
    include: bool | None = None
    narrative: str | None = None
    action: str | None = None


@dataclass(frozen=True)
class CustomCode:
    """
    One custom code added via add_custom_code.
    """

    code: str
    system: str
    name: str


@dataclass(frozen=True)
class Scenario:
    """
    One refinement scenario: the condition to configure for plus the
    customizations layered on top of the default configuration.
    """

    name: str
    fixture_dir: str
    condition_name: str
    rsg_code: str
    canonical_url: str
    configuration_version: int
    custom_codes: tuple[CustomCode, ...] = ()
    section_overrides: tuple[SectionOverride, ...] = ()
    associated_conditions: tuple[str, ...] = ()


class ScenarioBuilder:
    """
    Orchestrates the building and activation of a configuration scenario.
    """

    def __init__(self, api_client: Any):
        self.client = api_client

    def _validate_response(self, response):
        """
        Validates that the response was successful.
        """
        response.raise_for_status()

    async def build_and_activate(self, scenario: Scenario, jurisdiction_id: str):
        """
        Builds the configuration via the API and activates it.
        """
        # 1. Get condition ID
        resp = await self.client.get("/conditions/")
        self._validate_response(resp)
        conditions = resp.json()

        condition = next(
            (c for c in conditions if c["display_name"] == scenario.condition_name),
            None,
        )
        if not condition:
            raise ValueError(
                f"Condition '{scenario.condition_name}' not found in database"
            )

        condition_id = condition["id"]

        # 2. Create config
        resp = await self.client.post(
            "/configurations/", json={"condition_id": condition_id}
        )
        self._validate_response(resp)
        config_id = resp.json()["id"]

        # 3. Associate conditions
        for cond_name in scenario.associated_conditions:
            resp = await self.client.get("/conditions")
            self._validate_response(resp)
            conditions = resp.json()
            condition = next(
                (c for c in conditions if c["display_name"] == cond_name),
                None,
            )
            if not condition:
                raise ValueError(f"Condition '{cond_name}' not found in database")
            assoc_id = condition["id"]
            resp = await self.client.put(
                f"/configurations/{config_id}/code-sets",
                json={"condition_id": assoc_id},
            )
            self._validate_response(resp)

        resp = await self.client.get("/code-systems")
        self._validate_response(resp)
        systems = resp.json()

        def _get_system_id(system_key: str) -> UUID:
            matching_system = next(
                (s for s in systems if s["key"] == system_key),
                None,
            )
            if matching_system is None:
                raise ValueError(f"Could not find system matching key: {system_key}")
            return matching_system["id"]

        # 4. Add custom codes
        for cc in scenario.custom_codes:
            resp = await self.client.post(
                f"/configurations/{config_id}/custom-codes",
                json={
                    "code": cc.code,
                    "system_id": _get_system_id(cc.system),
                    "display": cc.name,
                },
            )
            self._validate_response(resp)

        # 5. Update section processing
        for ov in scenario.section_overrides:
            payload = {"current_code": ov.current_code}
            if ov.include is not None:
                payload["include"] = ov.include
            if ov.narrative is not None:
                payload["narrative"] = ov.narrative
            if ov.action is not None:
                payload["action"] = ov.action
            resp = await self.client.patch(
                f"/configurations/{config_id}/sections", json=payload
            )
            self._validate_response(resp)

        # 6. Activate
        resp = await self.client.patch(f"/configurations/{config_id}/activate")
        self._validate_response(resp)

        return config_id
