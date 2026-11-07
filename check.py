import time
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


def check_url(url):
    started = time.perf_counter()
    try:
        with urlopen(url, timeout=5) as response:

            return {
                "url": url,
                "status_code": response.status,
                "duration_ms": round((time.perf_counter() - started) * 1000),
                "error": None,
            }
    except HTTPError as exc:
        return {
            "url": url,
            "status_code": exc.code,
            "duration_ms": round((time.perf_counter() - started) * 1000),
            "error": str(exc),
         }
    except URLError as exc:
        return {
            "url": url,
            "status_code": None,
            "duration_ms": round((time.perf_counter() - started) * 1000),
            "error": str(exc.reason),
        }
    except TimeoutError as exc:
        return {
            "url": url,
            "status_code": None,
            "duration_ms": round((time.perf_counter() - started) * 1000),
            "error": str(exc),
        }


if __name__ == "__main__":
    urls = [
        "https://example.com",
        "https://example.com/missing",
        "https://test.invalid",
    ]

    for url in urls:
        print(check_url(url))
