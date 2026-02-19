# Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
cd /home/fujii/cycling-route-planner
pip install -r eval/requirements.txt

# Or using uv (recommended)
uv pip install -r eval/requirements.txt
```

### 2. Set Environment Variables

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify it's set
echo $ANTHROPIC_API_KEY
```

### 3. Run Quality Evaluation

```bash
# Run evaluation with mock data (works without backend)
python eval/evaluate.py
```

Expected output:
```
=== Cycling Route Quality Evaluation ===

Loaded 5 test cases

[1/5] Evaluating: 堺市上野芝 → 吉野山（ロングライド、山岳）
  - Using mock route plan (backend not available)
  - Safety: 8/10
  - Weather: 7/10
  - Practicality: 9/10
  - User Satisfaction: 8/10
  - Overall: 8/10

[2/5] Evaluating: 堺 → 六甲山（ヒルクライム）
...

=== Evaluation Complete ===
Results saved to: /home/fujii/cycling-route-planner/eval/results/evaluation_results.json
```

### 4. Run Performance Benchmark

```bash
# Start the backend server first (in another terminal)
make dev

# Then run the benchmark
python eval/bench_api.py --iterations 5

# Or with custom API URL
python eval/bench_api.py --api-url http://localhost:8000/api/plan --iterations 10
```

Expected output:
```
=== Cycling Route API Performance Benchmark ===

Target API: http://localhost:8000/api/plan
Iterations per test case: 5

[1/5] Benchmarking: 堺市上野芝 → 吉野山（ロングライド、山岳）
  Running 5 iterations...
    [1/5] TTFB: 250ms, Total: 3000ms
    [2/5] TTFB: 240ms, Total: 2950ms
    ...

=== Benchmark Complete ===
Results saved to: /home/fujii/cycling-route-planner/eval/results/benchmark_results.json
```

## Viewing Results

### Evaluation Results

```bash
# Pretty print evaluation results
python -m json.tool eval/results/evaluation_results.json

# Or use jq if installed
jq '.' eval/results/evaluation_results.json
```

### Benchmark Results

```bash
# Pretty print benchmark results
python -m json.tool eval/results/benchmark_results.json

# Extract just the summary
jq '.results[] | {test_case, success_rate, ttfb_p50: .ttfb_ms.p50, total_p50: .total_time_ms.p50}' eval/results/benchmark_results.json
```

## Integration with Makefile

The evaluation system can be integrated into the project Makefile:

```makefile
# Add to Makefile
.PHONY: eval bench

eval:
	@echo "Running route quality evaluation..."
	python eval/evaluate.py

bench:
	@echo "Running API performance benchmark..."
	@echo "Make sure backend is running (make dev)"
	python eval/bench_api.py --iterations 10
```

Then run:
```bash
make eval   # Run quality evaluation
make bench  # Run performance benchmark
```

## Troubleshooting

### Missing ANTHROPIC_API_KEY

**Error:**
```
ValueError: ANTHROPIC_API_KEY environment variable not set
```

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Or add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

### Backend Not Available (bench_api.py)

**Error:**
```
WARNING: Cannot reach API at http://localhost:8000/api/plan
```

**Solution:**
```bash
# Start the backend in another terminal
make dev

# Or manually
cd /home/fujii/cycling-route-planner
uvicorn backend.app.main:app --reload
```

### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution:**
```bash
# Install dependencies
pip install -r eval/requirements.txt
```

## Advanced Usage

### Custom Test Cases

Edit `eval/test_routes.json` to add your own test cases:

```json
{
  "name": "Custom Route Name",
  "origin": {
    "lat": 34.5,
    "lng": 135.5,
    "name": "Start Point"
  },
  "destination": {
    "lat": 34.6,
    "lng": 135.6,
    "name": "End Point"
  },
  "preferences": {
    "difficulty": "moderate",
    "avoid_traffic": true,
    "prefer_scenic": true,
    "max_distance_km": 80,
    "max_elevation_gain_m": 1000
  },
  "departure_time": "2025-03-20T08:00:00"
}
```

### Programmatic Usage

```python
import asyncio
import json
from eval.evaluate import evaluate_route_plan, mock_plan_route
from anthropic import AsyncAnthropic

async def custom_evaluation():
    # Load test case
    with open('eval/test_routes.json') as f:
        test_cases = json.load(f)

    test_case = test_cases[0]

    # Generate mock route plan
    route_plan = await mock_plan_route(test_case)

    # Evaluate
    client = AsyncAnthropic(api_key="sk-ant-...")
    result = await evaluate_route_plan(test_case, route_plan, client)

    print(json.dumps(result, indent=2, ensure_ascii=False))

asyncio.run(custom_evaluation())
```

## Tips

1. **Save API costs**: Use mock mode for development and testing
2. **Parallel execution**: Run evaluation and benchmark in parallel terminals
3. **Version control**: Results are gitignored by default (`.gitignore` in `results/`)
4. **Custom metrics**: Extend `bench_api.py` to track custom performance metrics
5. **CI/CD integration**: Add evaluation to your continuous integration pipeline
