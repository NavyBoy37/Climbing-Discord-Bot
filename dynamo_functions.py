import boto3
from dotenv import load_dotenv
import os
from botocore.exceptions import ClientError
from datetime import datetime
import re

load_dotenv()

aws_access = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")


def test_aws_connection():
    # None / Returns "RockData" Dynamo.db table
    try:
        session = boto3.Session(
            aws_access_key_id=aws_access,
            aws_secret_access_key=aws_secret,
            region_name=aws_region,
        )

        ddb = session.resource("dynamodb")
        test_table = ddb.Table("RockData")

        print("AWS Test Connection Successful!")
        return test_table
    except Exception as e:
        print(f"AWS Test Connection Failed: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        raise


def check_user_exists(id, table) -> bool:
    print("... checking if user exists w/ check_user_exists")
    # discord user id / boolean
    """intakes discord.py user_id (THIS IS "id" IN DYNAMO.  Very important)
    input id: int / return boolean
    """
    id = str(id)
    try:

        response = table.get_item(Key={"id": id})
        return "Item" in response

    except ClientError:
        return False


def check_and_create_user(id, table):
    print("... checking if user exists / creating user w/ check_and_create_user")
    # Discord id, Dynamo table / boolean, dictionary item (existing or new)
    try:
        response = table.get_item(Key={"id": str(id)})

        if "Item" in response:
            return True, response["Item"]
        else:
            new_user = {
                "id": str(id),
                "climbing_data": {},
                "created_at": str(datetime.now()),
            }

            table.put_item(Item=new_user)
            print("New user created")
            return False, new_user

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        print(f"DynamoDB Error Code: {error_code}")
        print(f"Full error: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise


def is_emoji_free(text: str) -> tuple[bool, str]:
    """
    Check if the input text contains any emojis.
    Returns (is_valid, error_message).

    Args:
        text (str): The text to check for emojis

    Returns:
        tuple[bool, str]: (True, "") if no emojis found, (False, error_message) if emojis found
    """
    # Regex pattern to match emoji characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"  # additional emoticons
        "\U00010000-\U0010ffff"  # additional symbols
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\u3030"
        "\ufe0f"
        "]+",
        flags=re.UNICODE,
    )

    if emoji_pattern.search(text):
        return False, "No fun allowed >:("
    return True, ""
