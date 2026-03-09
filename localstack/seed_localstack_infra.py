from refiner.tests.integration.test_lambda import (
    configure_default_setup,
    setup_s3_client,
)

test_client = setup_s3_client()
configure_default_setup(test_client, auto_teardown_resources=False)
