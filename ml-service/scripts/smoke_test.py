"""Simulate the backend sending an image to the ML service over real HTTP."""

from io import BytesIO
import sys
import time

import httpx
from PIL import Image


EXPECTED_RESPONSE = {
    "brand": "MAGGI",
    "product": "2-Minute Noodles",
    "status": "ANALYSIS_PENDING",
}
TIMEOUT_SECONDS = 5.0


def make_png():
    """Build a small valid PNG in memory without writing an image file."""
    stream = BytesIO()
    Image.new("RGB", (2, 2), color="red").save(stream, format="PNG")
    return stream.getvalue()


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
            # Check that the health endpoint responds with the expected body.
            response, elapsed = request(client, "GET", f"{base_url}/health")
            passed_all &= report(
                "GET /health returns 200 and {\"status\":\"ok\"}",
                response.status_code == 200 and response.json() == {"status": "ok"},
                elapsed,
            )

            # Check that a valid in-memory PNG upload returns the exact dummy body.
            response, elapsed = request(
                client,
                "POST",
                f"{base_url}/analyze",
                files={"image": ("smoke.png", make_png(), "image/png")},
            )
            passed_all &= report(
                "POST /analyze PNG upload returns exact dummy response",
                response.status_code == 200 and response.json() == EXPECTED_RESPONSE,
                elapsed,
            )

            # Check that a text file is rejected as an unsupported upload.
            response, elapsed = request(
                client,
                "POST",
                f"{base_url}/analyze",
                files={"image": ("notes.txt", b"hello", "text/plain")},
            )
            passed_all &= report("POST /analyze text upload returns 400", response.status_code == 400, elapsed)

            # Check that omitting the required image part returns HTTP 422.
            response, elapsed = request(client, "POST", f"{base_url}/analyze")
            passed_all &= report("POST /analyze without image returns 422", response.status_code == 422, elapsed)

    except httpx.RequestError as exc:
        print(f"FAIL: Could not reach the ML service at {base_url}: {exc}")
        print(f"Is the ML service running on {base_url}?")
        return 1

    return 0 if passed_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
