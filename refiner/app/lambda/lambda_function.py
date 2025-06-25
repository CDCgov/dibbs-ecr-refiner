# Based on sample code: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-example

# This file uses the default `lambda_function.py` and `lambda_handler` naming conventions. If either
# of these were to change, we'd need to modify this in AWS.
# See here: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-naming

import logging

from ..services import file_io

# Initialize the logger
logger = logging.getLogger()
logger.setLevel("INFO")


def lambda_handler(event, context):
    """
    Main Lambda handler function.

    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    try:
        # Parse the input event
        order_id = event.get("Order_id", "test-id")
        amount = event.get("Amount", "test-amt")
        item = event.get("Item", "test-item")

        # Create the receipt content and key destination
        receipt_content = f"OrderID: {order_id}\nAmount: ${amount}\nItem: {item}"
        key = f"receipts/{order_id}.txt"

        # Do something with the data
        print(receipt_content, key)

        logger.info(
            f"Successfully processed order {order_id} and stored receipt in S3 bucket"
        )

        # Test using custom module's code
        REFINER_DETAILS = file_io.read_json_asset("refiner_details.json")
        print(REFINER_DETAILS["sections"]["11369-6"])

        return {"statusCode": 200, "message": "Receipt processed successfully"}

    except Exception as e:
        logger.error(f"Error processing order: {str(e)}")
        raise
