# SAST Console API Tests

This directory contains test scripts to verify the functionality and performance of the SAST Console's API endpoints.

## Overview

Three test scripts are provided:

1. `test_console_api.py` - Functional testing script that tests the correctness of all API endpoints
2. `load_test_console_api.py` - Load testing script that tests the performance of the API under concurrent load
3. `run_tests.py` - Master script that runs all the tests and provides a summary of the results

All scripts test the API endpoints of the SAST Console at https://sast-console.vercel.app/.

## Endpoints Tested

The scripts test the following endpoint categories:

### Agent-related APIs
- GET /api/agents - Get all agents
- POST /api/agents/register - Register a new agent
- GET /api/agents/[id] - Get a specific agent
- PUT /api/agents/[id] - Update agent details
- POST /api/agents/[id]/heartbeat - Send agent heartbeat

### Task-related APIs
- GET /api/tasks - Get all tasks
- POST /api/tasks - Create a new task
- GET /api/tasks/[id] - Get a specific task
- PATCH /api/tasks/[id] - Update task status
- GET/POST /api/tasks/[id]/results - Get/Create task scan results

## Prerequisites

The scripts use the following Python packages:
- requests
- json
- uuid
- logging
- datetime
- statistics (for load testing)
- threading (for load testing)
- concurrent.futures (for load testing)

All these dependencies are already included in the `requirements.txt` file.

## How to Run - All Tests

The easiest way to run all tests is to use the master test script:

1. Make sure you're in the agent directory
2. Activate the virtual environment (if not already activated):
   ```
   source venv/bin/activate  # On Unix/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```
3. Run the master test script:
   ```
   python run_tests.py
   ```

### Master Test Script Options

The master script (`run_tests.py`) accepts several command line options:

- `--functional-only` - Run only the functional tests
- `--load-only` - Run only the load tests
- `--verbose` - Show more detailed output
- `--negative` - Run negative test cases (testing error conditions)
- `--load-agents <number>` - Number of agents for load test (default: 5)
- `--load-tasks <number>` - Tasks per agent for load test (default: 2)
- `--load-concurrent <number>` - Concurrent requests for load test (default: 3)

Example:
```
python run_tests.py --verbose --negative --load-agents 10
```

## How to Run - Functional Testing

To run only the functional tests:

1. Make sure you're in the agent directory and have activated the virtual environment
2. Run the test script:
   ```
   python test_console_api.py
   ```

### Functional Test Options

The functional test script accepts the following options:

- `--verbose` - Show detailed response bodies
- `--negative` - Run negative test cases (testing error handling)

Example:
```
python test_console_api.py --negative --verbose
```

## How to Run - Load Testing

To run only the load testing script:

1. Make sure you're in the agent directory and have activated the virtual environment
2. Run the load test script with optional parameters:
   ```
   python load_test_console_api.py --agents 10 --tasks-per-agent 3 --concurrent 5
   ```

### Load Test Parameters

- `--agents` - Number of test agents to create (default: 5)
- `--tasks-per-agent` - Number of tasks to create for each agent (default: 2)
- `--concurrent` - Maximum number of concurrent requests (default: 3)
- `--verbose` - Show more detailed output

## Test Output

All test scripts generate output logs in the `logs/` directory:

- `logs/api_tests.log` - Log file for functional tests
- `logs/load_test.log` - Log file for load tests
- `logs/all_tests.log` - Log file for the master test script

### Functional Tests

The functional test script will output logs to both the console and a log file (`logs/api_tests.log`). Each API request and response is logged with its status code.

Successful execution will show:
```
=== Starting SAST Console API Tests ===
Testing POST https://sast-console.vercel.app/api/agents/register
...
=== All SAST Console API Tests Completed Successfully ===
```

### Load Tests

The load test script will output logs to both the console and a log file (`logs/load_test.log`). It will show a detailed performance summary at the end:

```
=== Performance Summary ===
Total agents created: 5
Total tasks created: 10

Endpoint Performance (seconds):
Endpoint             Count    Min      Max      Avg      Median   95%     
----------------------------------------------------------------------
register_agent       5        0.543    0.982    0.731    0.687    0.982   
get_agents           15       0.213    0.438    0.301    0.287    0.412   
get_agent            5        0.198    0.312    0.241    0.232    0.312   
update_agent         5        0.227    0.392    0.298    0.287    0.392   
agent_heartbeat      5        0.201    0.354    0.267    0.254    0.354   
create_task          10       0.283    0.521    0.367    0.342    0.498   
get_tasks            15       0.232    0.478    0.324    0.312    0.453   
get_task             10       0.187    0.312    0.238    0.232    0.301   
update_task          10       0.223    0.387    0.289    0.276    0.365   
submit_result        10       0.312    0.543    0.412    0.398    0.521   
get_results          10       0.198    0.342    0.267    0.254    0.334   
----------------------------------------------------------------------
OVERALL              100      0.187    0.982    0.341    0.302    0.532   
```

### Master Test Runner Output

The master test runner provides a summary of all test runs:

```
=== Starting SAST Console API Test Suite ===
...
=== Test Run Summary ===
Total tests run: 2
Successful: 2
Failed: 0
Total duration: 45.23 seconds

=== Detailed Results ===
test_console_api.py: SUCCESS (32.15s)
load_test_console_api.py: SUCCESS (13.08s)
=== End of Test Run ===
```

## Test Coverage

### Functional Tests

The functional tests include:

1. **Positive Test Cases**:
   - Standard API operations for agents and tasks
   - Filtering tasks by agent
   - Multiple scanner results for tasks
   
2. **Negative Test Cases** (when `--negative` flag is used):
   - Invalid agent/task IDs
   - Missing required fields
   - Invalid data types

### Load Tests

Load tests measure API performance metrics including:
- Response time (min, max, average, median)
- 95th percentile response time
- Concurrency handling

## Test Flow

Both test scripts follow a similar test flow:

1. Register new agent(s)
2. Get all agents
3. Get specific agent(s)
4. Update agent(s)
5. Send heartbeat(s)
6. Create task(s)
7. Get all tasks
8. Get specific task(s)
9. Update task status(es)
10. Submit and retrieve task results

The functional test script runs these operations sequentially with detailed validation, while the load test script runs many of them concurrently to test performance under load.

## Error Handling

All scripts include robust error handling. If any test fails, an error will be logged with details about what went wrong. The exit code will be 1 in case of failure, making them suitable for integration in CI/CD pipelines.

## Customization

You can modify the test data in either script to test different scenarios. For the load test script, you can adjust the command line parameters to simulate different levels of concurrent load.

## Cleaning Up

The scripts don't delete the test data they create. If you want to clean up after tests, you would need to implement additional delete/cleanup functionality or do it manually through the console. 