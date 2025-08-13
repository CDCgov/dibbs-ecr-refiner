from fastapi import APIRouter

from ...db.configurations.model import Configuration

router = APIRouter(prefix="/configurations")


@router.get(
    "/",
    response_model=list[Configuration],
    tags=["configurations"],
    operation_id="getConfigurations",
)
def get_configurations() -> list[Configuration]:
    """
    Returns a list of configurations based on the logged-in user.

    Returns:
        List of configuration objects.
    """
    sample_configs = [
        Configuration(id="1", name="Chlamydia trachomatis infection", is_active=True),
        Configuration(id="2", name="Disease caused by Enterovirus", is_active=False),
        Configuration(
            id="3", name="Human immunodeficiency virus infection (HIV)", is_active=False
        ),
        Configuration(id="4", name="Syphilis", is_active=True),
        Configuration(id="5", name="Viral hepatitis, type A", is_active=True),
    ]
    return sample_configs
