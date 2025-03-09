# SAST Agent

This agent is part of the SAST (Static Application Security Testing) system. It connects to the central console, receives scanning tasks, executes security scans on code repositories, and reports results back to the console.

## Features

- Automatic registration with the console
- Heartbeat mechanism to maintain connection
- Support for multiple security scanners (Bandit, Semgrep)
- Git repository cloning and scan execution
- Result reporting back to the console

## Requirements

- Python 3.7+
- The following Python packages (see requirements.txt):
  - requests
  - flask
  - pyyaml
  - gitpython
  - bandit
  - semgrep

## Installation

1. Clone this repository or download the agent code
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure that the security scanners (Bandit, Semgrep) are properly installed and available in your PATH.

## Usage

Run the agent with the following command:

```bash
python agent.py --console http://your-console-url --name optional-agent-name
```

Arguments:
- `--console`: (Required) URL of the SAST console
- `--name`: (Optional) Custom name for this agent

The agent will:
1. Register with the console (or use existing registration if available)
2. Send regular heartbeats to the console
3. Poll for pending tasks
4. Execute security scans when tasks are received
5. Report results back to the console

## Configuration

The agent stores its configuration in a `config.yaml` file in the same directory. This includes:
- Agent ID (generated on first run)
- Agent name
- Console URL
- Registration status

You can delete this file to force the agent to re-register with the console.

## Security Scanners

The agent currently supports:

1. **Bandit**: A tool designed to find common security issues in Python code
2. **Semgrep**: A lightweight static analysis tool for multiple languages

You can extend the agent to support additional scanners by implementing appropriate methods similar to `run_bandit_scan()` and `run_semgrep_scan()`.

## Troubleshooting

- Ensure the console URL is correct and accessible
- Check that the security scanners are properly installed
- Review the agent logs for error messages
- Verify that Git is installed and working correctly

## License

This software is provided under the MIT License. 