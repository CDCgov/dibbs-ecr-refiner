from dataclasses import dataclass
from typing import Any


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

    async def build_and_activate(self, scenario: Scenario, jurisdiction_id: str):
        """
        Builds the configuration via the API and activates it.
        """
        # 1. Get condition ID
        resp = await self.client.get(f"/conditions?name={scenario.condition_name}")
        condition_id = resp.json()[0]["id"]

        # 2. Create config
        resp = await self.client.post(
            "/configurations", json={"condition_id": condition_id}
        )
        config_id = resp.json()["id"]

        # 3. Associate conditions
        for cond_name in scenario.associated_conditions:
            resp = await self.client.get(f"/conditions?name={cond_name}")
            assoc_id = resp.json()[0]["id"]
            await self.client.post(
                f"/configurations/{config_id}/associations",
                json={"condition_id": assoc_id},
            )

        # 4. Add custom codes
        for cc in scenario.custom_codes:
            await self.client.post(
                f"/configurations/{config_id}/custom-codes",
                json={"code": cc.code, "system": cc.system, "name": cc.name},
            )

        # 5. Update section processing
        for ov in scenario.section_overrides:
            payload = {"current_code": ov.current_code}
            if ov.include is not None:
                payload["include"] = ov.include
            if ov.narrative is not None:
                payload["narrative"] = ov.narrative
            if ov.action is not None:
                payload["action"] = ov.action
            await self.client.patch(
                f"/configurations/{config_id}/sections", json=payload
            )

        # 6. Activate
        await self.client.post(f"/configurations/{config_id}/activate")

        return config_id
