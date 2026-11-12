"""Simulate the Spring Boot backend making real HTTP requests to the ML service."""

import sys
import time
from urllib.error import URLError

import httpx


EXPECTED_RESPONSE = {
    "product_name": "AirPods Pro",
    "brand": "Apple",
    "price": 24999.0,
    "verdict": "SUSPICIOUS",
    "confidence": 0.5,
    "reasons": ["Dummy response: real analysis is not implemented yet"],
    "analysis_mode": "dummy",
}
TIMEOUT_SECONDS = 5.0


def request(client, method, url, **kwargs):
    start = time.perf_counter()
    response = client.request(method, url, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return response, elapsed_ms


def report(name, passed, elapsed_ms):
    result = "PASS" if passed else "FAIL"
    print(f"{result}: {name} ({elapsed_ms:.1f} ms)")
    return passed


def main():
    base_url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    passed_all = True

    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            # Check that the health endpoint returns its expected status and body.
            response, elapsed = request(client, "GET", f"{base_url}/health")
            passed_all &= report(
                "GET /health returns 200 and {\"status\":\"ok\"}",
                response.status_code == 200 and response.json() == {"status": "ok"},
                elapsed,
            )

            # Check the valid analyze request's status, exact keys, and dummy values.
            response, elapsed = request(
                client,
                "POST",
                f"{base_url}/analyze",
                json={"product_name": "AirPods Pro", "brand": "Apple", "price": 24999},
            )
            body = response.json()
            passed_all &= report(
                "POST /analyze valid request returns exact dummy response",
                response.status_code == 200
                and set(body) == set(EXPECTED_RESPONSE)
                and body == EXPECTED_RESPONSE,
                elapsed,
            )

            # Check that a negative price is rejected with HTTP 422.
            response, elapsed = request(
                client,
                "POST",
                f"{base_url}/analyze",
                json={"product_name": "AirPods Pro", "brand": "Apple", "price": -5},
            )
            passed_all &= report("POST /analyze negative price returns 422", response.status_code == 422, elapsed)

            # Check that omitting a required field is rejected with HTTP 422.
            response, elapsed = request(
                client,
                "POST",
                f"{base_url}/analyze",
                json={"product_name": "AirPods Pro", "price": 24999},
            )
            passed_all &= report("POST /analyze missing field returns 422", response.status_code == 422, elapsed)

    except (httpx.ConnectError, httpx.TimeoutException, URLError) as exc:
        print(f"FAIL: Could not reach the ML service at {base_url}: {exc}")
        print(f"Is the ML service running on {base_url}?")
        return 1

    return 0 if passed_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
