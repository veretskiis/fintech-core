import random
import uuid
import json
from decimal import Decimal

import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

IDEMPOTENCY_KEY = str(uuid.uuid4())


def do_request(i: int, url: str, token: str, from_wallet: str, to_wallet: str, amount: str, unique: bool):
    if unique:
        idempotency_key = str(uuid.uuid4())
    else:
        idempotency_key = IDEMPOTENCY_KEY
        amount = str(Decimal(amount) + Decimal(random.randint(1, 100)))

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }

    payload = {
        "from_wallet": from_wallet,
        "to_wallet": to_wallet,
        "amount": amount,
    }

    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return i, r.status_code, r.text
    except Exception as e:
        return i, "ERR", str(e)


def main():
    parser = argparse.ArgumentParser(description="Параллельные запросы")
    parser.add_argument("--url", default="http://web/api/transfer/")
    parser.add_argument("--token", default="Bearer no_auth_now")
    parser.add_argument("--from-wallet", type=str)
    parser.add_argument("--to-wallet", type=str)
    parser.add_argument("--amount", default="1001.00")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--unique", type=int, default=1)

    args = parser.parse_args()
    workers = args.workers or args.requests
    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                do_request,
                i,
                args.url,
                args.token,
                args.from_wallet,
                args.to_wallet,
                args.amount,
                bool(args.unique),
            )
            for i in range(args.requests)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    for i, status, body in sorted(results):
        print(f"[{i:02}] status={status} body={body}")


if __name__ == "__main__":
    main()
