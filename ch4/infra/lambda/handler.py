"""AWS Lambda 진입점: Function URL 이벤트를 labapi/core.py로 넘깁니다.

배포 패키지(infra/build/)에는 이 파일과 ch4/kit/labapi/ 가 함께 들어갑니다(deploy.sh).
횟수 제한과 신청 저장소만 DynamoDB로 구현하고, 나머지는 로컬 서버와 같은 코드입니다.
"""

import base64
import json
import os
import time

import boto3

from labapi import core

TABLE = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
SECRET = os.environ["LAB_TOKEN_SECRET"]
RATE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", core.DEFAULT_RATE_LIMIT))
REQ_TTL_DAYS = 14


class DynamoLimiter:
    def __init__(self, limit):
        self.limit = limit

    def hit(self, tid, now=None):
        now = now or time.time()
        minute = int(now // 60)
        resp = TABLE.update_item(
            Key={"pk": "rate#%s" % tid, "sk": str(minute)},
            UpdateExpression="ADD cnt :one SET expires_at = :exp",
            ExpressionAttributeValues={":one": 1, ":exp": minute * 60 + 180},
            ReturnValues="UPDATED_NEW",
        )
        if int(resp["Attributes"]["cnt"]) > self.limit:
            return False, 60 - int(now % 60)
        return True, 0


class DynamoStore:
    def list_requests(self, tid):
        resp = TABLE.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": "req#%s" % tid},
        )
        items = [json.loads(i["item"]) for i in resp.get("Items", [])]
        return sorted(items, key=lambda x: x["request_id"])

    def add_request(self, tid, item):
        TABLE.put_item(Item={
            "pk": "req#%s" % tid, "sk": item["request_id"], "item": json.dumps(item, ensure_ascii=False),
            "expires_at": int(time.time()) + REQ_TTL_DAYS * 86400,
        })


LIMITER = DynamoLimiter(RATE)
STORE = DynamoStore()


def log(entry):
    print(json.dumps(entry, ensure_ascii=False))


def lambda_handler(event, context):
    http = (event.get("requestContext") or {}).get("http") or {}
    body = event.get("body") or ""
    if event.get("isBase64Encoded") and body:
        body = base64.b64decode(body)
    elif isinstance(body, str):
        body = body.encode("utf-8")
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    status, out_headers, out = core.handle(
        http.get("method", "GET"), event.get("rawPath", "/"), event.get("rawQueryString", ""),
        headers, body, SECRET, LIMITER, STORE, log=log,
    )
    return {"statusCode": status, "headers": out_headers, "body": out.decode("utf-8")}
