import boto3
from dotenv import load_dotenv
import os
from botocore.exceptions import ClientError
from datetime import datetime

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
