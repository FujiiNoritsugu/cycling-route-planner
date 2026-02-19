"""API performance benchmarking tool.

This module measures response times for the route planning API,
including time to first byte (TTFB) and total completion time.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import numpy as np


# Type aliases
TestCase = dict[str, Any]
BenchmarkResult = dict[str, Any]


class PerformanceMetrics:
    """Container for performance measurement data."""

    def __init__(self) -> None:
        self.ttfb_times: list[float] = []
        self.total_times: list[float] = []
        self.successes: int = 0
        self.failures: int = 0


async def benchmark_single_request(
    client: httpx.AsyncClient,
    test_case: TestCase,
    api_url: str,
) -> tuple[float | None, float | None, bool]:
    """Benchmark a single API request.

    Args:
        client: HTTP client
        test_case: Test case to send
        api_url: API endpoint URL

    Returns:
        Tuple of (ttfb_ms, total_time_ms, success)
    """
    # Build request payload
    payload = {
        "origin": test_case["origin"],
        "destination": test_case["destination"],
        "preferences": test_case["preferences"],
        "departure_time": test_case["departure_time"],
    }

    start_time = time.perf_counter()
    ttfb_time = None
    first_byte_received = False

    try:
        async with client.stream("POST", api_url, json=payload, timeout=120.0) as response:
            if response.status_code != 200:
                return None, None, False

            # Measure TTFB - time until first byte received
            async for chunk in response.aiter_bytes():
                if not first_byte_received:
                    ttfb_time = (time.perf_counter() - start_time) * 1000
                    first_byte_received = True

                # Continue consuming the stream
                if len(chunk) > 0:
                    pass

        total_time = (time.perf_counter() - start_time) * 1000
        return ttfb_time, total_time, True

    except Exception as e:
        print(f"    Error: {e}")
        return None, None, False


async def benchmark_test_case(
    test_case: TestCase,
    num_iterations: int = 10,
    api_url: str = "http://localhost:8000/api/plan",
) -> BenchmarkResult:
    """Benchmark a test case multiple times.

    Args:
        test_case: Test case to benchmark
        num_iterations: Number of iterations to run
        api_url: API endpoint URL

    Returns:
        Benchmark results with percentile statistics
    """
    print(f"  Running {num_iterations} iterations...")

    metrics = PerformanceMetrics()

    async with httpx.AsyncClient() as client:
        for i in range(num_iterations):
            ttfb, total, success = await benchmark_single_request(
                client, test_case, api_url
            )

            if success and ttfb is not None and total is not None:
                metrics.ttfb_times.append(ttfb)
                metrics.total_times.append(total)
                metrics.successes += 1
                print(f"    [{i+1}/{num_iterations}] TTFB: {ttfb:.0f}ms, Total: {total:.0f}ms")
            else:
                metrics.failures += 1
                print(f"    [{i+1}/{num_iterations}] FAILED")

            # Small delay between requests
            await asyncio.sleep(0.5)

    # Calculate percentiles
    if metrics.ttfb_times:
        ttfb_p50 = float(np.percentile(metrics.ttfb_times, 50))
        ttfb_p95 = float(np.percentile(metrics.ttfb_times, 95))
        ttfb_p99 = float(np.percentile(metrics.ttfb_times, 99))
    else:
        ttfb_p50 = ttfb_p95 = ttfb_p99 = None

    if metrics.total_times:
        total_p50 = float(np.percentile(metrics.total_times, 50))
        total_p95 = float(np.percentile(metrics.total_times, 95))
        total_p99 = float(np.percentile(metrics.total_times, 99))
    else:
        total_p50 = total_p95 = total_p99 = None

    success_rate = metrics.successes / num_iterations if num_iterations > 0 else 0.0

    return {
        "test_case": test_case["name"],
        "num_iterations": num_iterations,
        "successes": metrics.successes,
        "failures": metrics.failures,
        "success_rate": success_rate,
        "ttfb_ms": {
            "p50": ttfb_p50,
            "p95": ttfb_p95,
            "p99": ttfb_p99,
            "min": float(min(metrics.ttfb_times)) if metrics.ttfb_times else None,
            "max": float(max(metrics.ttfb_times)) if metrics.ttfb_times else None,
            "mean": float(np.mean(metrics.ttfb_times)) if metrics.ttfb_times else None,
        },
        "total_time_ms": {
            "p50": total_p50,
            "p95": total_p95,
            "p99": total_p99,
            "min": float(min(metrics.total_times)) if metrics.total_times else None,
            "max": float(max(metrics.total_times)) if metrics.total_times else None,
            "mean": float(np.mean(metrics.total_times)) if metrics.total_times else None,
        },
        "benchmarked_at": datetime.now().isoformat(),
    }


async def run_benchmark(
    num_iterations: int = 10,
    api_url: str = "http://localhost:8000/api/plan",
) -> None:
    """Run benchmark on all test cases and save results.

    Args:
        num_iterations: Number of iterations per test case
        api_url: API endpoint URL
    """
    print("=== Cycling Route API Performance Benchmark ===\n")
    print(f"Target API: {api_url}")
    print(f"Iterations per test case: {num_iterations}\n")

    # Load test cases
    eval_dir = Path(__file__).parent
    test_routes_path = eval_dir / "test_routes.json"

    with open(test_routes_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"Loaded {len(test_cases)} test cases\n")

    # Check if API is available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                api_url.replace("/api/plan", "/health"), timeout=5.0
            )
            if response.status_code != 200:
                print(f"WARNING: API health check failed (status {response.status_code})")
                print("Continuing anyway...\n")
    except Exception as e:
        print(f"WARNING: Cannot reach API at {api_url}")
        print(f"Error: {e}")
        print("\nThis benchmark requires a running backend server.")
        print("Start the server with: make dev\n")
        return

    # Benchmark each test case
    all_results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] Benchmarking: {test_case['name']}")

        try:
            result = await benchmark_test_case(test_case, num_iterations, api_url)
            all_results.append(result)

            # Print summary for this test case
            if result["success_rate"] > 0:
                print(f"  ✓ Success rate: {result['success_rate']:.1%}")
                print(f"  ✓ TTFB p50/p95/p99: "
                      f"{result['ttfb_ms']['p50']:.0f}ms / "
                      f"{result['ttfb_ms']['p95']:.0f}ms / "
                      f"{result['ttfb_ms']['p99']:.0f}ms")
                print(f"  ✓ Total p50/p95/p99: "
                      f"{result['total_time_ms']['p50']:.0f}ms / "
                      f"{result['total_time_ms']['p95']:.0f}ms / "
                      f"{result['total_time_ms']['p99']:.0f}ms")
            else:
                print(f"  ✗ All requests failed")
            print()

        except Exception as e:
            print(f"  ERROR: {e}\n")
            all_results.append(
                {
                    "test_case": test_case["name"],
                    "error": str(e),
                    "benchmarked_at": datetime.now().isoformat(),
                }
            )

    # Save results
    results_dir = eval_dir / "results"
    results_dir.mkdir(exist_ok=True)
    results_path = results_dir / "benchmark_results.json"

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "benchmarked_at": datetime.now().isoformat(),
                "api_url": api_url,
                "num_iterations": num_iterations,
                "total_cases": len(test_cases),
                "results": all_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n=== Benchmark Complete ===")
    print(f"Results saved to: {results_path}")

    # Print summary table
    print("\n=== Summary Table ===")
    print(f"{'Test Case':<50} {'Success%':<10} {'TTFB p50':<12} {'TTFB p95':<12} {'Total p50':<12} {'Total p95':<12}")
    print("-" * 120)

    for result in all_results:
        if "error" in result:
            print(f"{result['test_case']:<50} ERROR: {result['error']}")
        else:
            ttfb_p50 = result['ttfb_ms']['p50']
            ttfb_p95 = result['ttfb_ms']['p95']
            total_p50 = result['total_time_ms']['p50']
            total_p95 = result['total_time_ms']['p95']

            ttfb_p50_str = f"{ttfb_p50:.0f}ms" if ttfb_p50 else "N/A"
            ttfb_p95_str = f"{ttfb_p95:.0f}ms" if ttfb_p95 else "N/A"
            total_p50_str = f"{total_p50:.0f}ms" if total_p50 else "N/A"
            total_p95_str = f"{total_p95:.0f}ms" if total_p95 else "N/A"

            print(
                f"{result['test_case']:<50} "
                f"{result['success_rate']:.1%}      "
                f"{ttfb_p50_str:<12} "
                f"{ttfb_p95_str:<12} "
                f"{total_p50_str:<12} "
                f"{total_p95_str:<12}"
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark cycling route API")
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of iterations per test case (default: 10)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000/api/plan",
        help="API endpoint URL (default: http://localhost:8000/api/plan)",
    )

    args = parser.parse_args()

    asyncio.run(run_benchmark(args.iterations, args.api_url))
