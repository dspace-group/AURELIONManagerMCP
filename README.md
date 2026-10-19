# dSPACE AURELION Manager MCP Server

The **dSPACE AURELION Manager MCP server** enables AI assistants (e.g. GitHub Copilot) to configure and control
dSPACE AURELION simulations through natural language.


## Prerequisites

The following software must be installed and running on the same machine as the MCP server:

- dSPACE AURELION Manager 26.1 or newer

Optionally, for a developer-focused setup:
- Python 3.12 or newer
- `uv`, the Python package and project manager used to create the environment, install dependencies, and run the server from this checkout. Install `uv` from the official Astral documentation: https://docs.astral.sh/uv/getting-started/installation/


## Getting Started

You can either download the AURELION Manager MCP server from the latest GitHub Release (Windows only) or run it from this repository with a `uv`-based setup. You can easily verify the installation with a quick prompt, for example: "Which version of the AURELION Manager is currently running?".

To install the latest release (Windows only):

1. Download `aurelion-manager-mcp-v<version>-windows-x64.zip` from the latest GitHub Release. The archive contains the server executable `aurelion-manager-mcp.exe`.
2. Follow the MCP server installation instructions for your MCP client (see documentation for [Claude](https://code.claude.com/docs/en/mcp-quickstart), [Codex](https://developers.openai.com/codex/mcp), [GitHub Copilot](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp-in-your-ide/extend-copilot-chat-with-mcp), ... ). Here is an exemplary installation for GitHub Copilot as a `.vscode/mcp.json` entry that points to the extracted executable:

   ```json
   {
     "servers": {
       "aurelion_manager": {
            "type": "stdio",
            "command": "<PATH_TO_EXTRACTED_RELEASE>\\aurelion-manager-mcp.exe",
            "env": {
                "AURELION_MANAGER_API_URL": "http://localhost:8584"
            }
        }
     }
   }
   ```

Alternatively, for a developer-focused `uv`-based setup:

This setup works on both Windows and Linux, as long as `uv` is installed and the dSPACE AURELION Manager REST-API is reachable from that machine.

1. Clone this repository.
2. Create the project environment and install dependencies from `pyproject.toml`:

   ```shell
   uv sync   # minimal
   uv sync --extra dev   # full developer setup
   ```

3. Follow the MCP server installation instructions for your respective MCP client (see documentation for [Claude](https://code.claude.com/docs/en/mcp-quickstart), [Codex](https://developers.openai.com/codex/mcp), [GitHub Copilot](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp-in-your-ide/extend-copilot-chat-with-mcp), ... ). Use `uv run` to start the server. For reference see [AURELIONManagerMCP.cmd](AURELIONManagerMCP.cmd) for Windows or [AURELIONManagerMCP.sh](AURELIONManagerMCP.sh) for Linux. You can call these scripts directly from your MCP client installation, exemplary `.vscode/mcp.json` entry  (use `AURELIONManagerMCP.sh` instead of `AURELIONManagerMCP.cmd` on Linux):

   ```json
   {
     "servers": {
       "aurelion_manager": {
            "type": "stdio",
            "command": "<PATH_TO_REPOSITORY>\\AURELIONManagerMCP.cmd",
            "env": {
                "AURELION_MANAGER_API_URL": "http://localhost:8584"
            }
        }
     }
   }
   ```
    Useful development commands:

      ```shell
      uv run pytest	# run tests
      uv run ruff format src tests	# run formatter
      uv run ruff check src tests		# run linter
      uv build	# build a wheel
      ```


## Configuration

The server is configured via environment variables:

| Variable | Default | Description |
|---|---|---|
| `AURELION_MANAGER_API_URL` | `http://localhost:8584` | Base URL of the running AURELION Manager REST API |

Set the variable before starting the server or in your MCP host configuration (see below).


## Available Tools

### Vehicles

| Tool | Description |
|---|---|
| `list_vehicles` | List all vehicles in the open project |
| `get_vehicle` | Get a vehicle by ID |
| `create_vehicle` | Create a new vehicle with components and sensor instances |
| `update_vehicle` | Fully replace a vehicle configuration |
| `delete_vehicle` | Permanently delete a vehicle |

### Sensors

| Tool | Description |
|---|---|
| `list_sensors` | List all sensors in the open project |
| `get_sensor` | Get a sensor by ID |
| `create_sensor` | Create a new sensor (CAMERA/RADAR/LIDAR/ULTRASONIC/INFRARED) |
| `update_sensor` | Fully replace a sensor configuration |
| `delete_sensor` | Permanently delete a sensor |

### Scenarios

| Tool | Description |
|---|---|
| `list_scenarios` | List all scenarios in the open project |
| `get_scenario` | Get a scenario by ID |
| `create_scenario` | Create a ModelDesk or OpenScenario scenario |
| `update_scenario` | Fully replace a scenario configuration |
| `delete_scenario` | Permanently delete a scenario |
| `get_scenario_parameters` | Get OpenSCENARIO parameter declarations |
| `get_scenario_validation_result` | Validate an OpenSCENARIO .xosc file |

### Systems

| Tool | Description |
|---|---|
| `list_systems` | List all simulation systems in the open project |
| `get_system` | Get a system by ID |
| `create_system` | Create a simulation system (ASM or Replay) |
| `update_system` | Fully replace a system configuration |
| `delete_system` | Permanently delete a system |

### Simulation Control

| Tool | Description |
|---|---|
| `get_simulation_state` | Get the current simulation state and loaded config |
| `get_simulation_diagnostics` | Get connectivity status of all simulation components |
| `check_simulation_preconditions` | Check if system+scenario are ready to synchronize |
| `synchronize_simulation` | Push configuration to all AURELION instances |
| `reset_simulation` | Reset the synchronization state |
| `cancel_synchronization` | Cancel an in-progress synchronization |
| `get_scenario_state` | Get current scenario playback state and time |
| `control_scenario_state` | Start (`Running`), stop (`Stopped`), or reset (`Reset`) the scenario |

### Projects & General

| Tool | Description |
|---|---|
| `get_current_project` | Get information about the currently open project |
| `open_project` | Open an AURELION Manager project by folder path |
| `get_version` | Get the AURELION Manager version |
| `get_log_file_path` | Get the path to the toolchain log file |


## Available Resources

Resources provide read-only access to project data as MCP resources (URI-addressable):

| URI | Description |
|---|---|
| `aurelionmgr://vehicles` | All vehicles in the open project |
| `aurelionmgr://vehicles/{vehicle_id}` | A specific vehicle |
| `aurelionmgr://sensors` | All sensors in the open project |
| `aurelionmgr://sensors/{sensor_id}` | A specific sensor |
| `aurelionmgr://scenarios` | All scenarios in the open project |
| `aurelionmgr://scenarios/{scenario_id}` | A specific scenario |
| `aurelionmgr://systems` | All simulation systems |
| `aurelionmgr://systems/{system_id}` | A specific simulation system |
| `aurelionmgr://simulation/state` | Current simulation state |


## Available Prompts

| Prompt | Description |
|---|---|
| `configure_simulation` | Step-by-step guide to configure and start a simulation |
| `create_sensor_workflow` | Guide to create a sensor and integrate it into a vehicle and system |


## Example Prompts

The following example prompts show how you can interact with the AURELION Manager MCP server to perform typical tasks:

- `Open the AURELION Manager project located in "C:/Projects/MyAURELIONProject".`
- `Configure my selected system to use the VEOS simulator running on 127.0.0.1.`
- `Synchronize the current configuration.`
- `What is the state of the current simulation?`


## Typical Workflow

```
1. open_project(project_folder="C:/Projects/MyAURELIONProject")
2. list_systems()            → note system ID
3. list_scenarios()          → note scenario ID
4. check_simulation_preconditions(system_id, scenario_id)
5. synchronize_simulation(system_id, scenario_id)
6. control_scenario_state(state="Running")
7. get_scenario_state()      → monitor progress
8. control_scenario_state(state="Stopped")
```


## Error Handling

All tools return JSON. On failure, the response contains an `error` object:

```json
{
  "error": {
    "code": "NO_OPEN_PROJECT",
    "message": "No project is currently open ...",
    "type": "permanent"
  }
}
```

| `type` | Meaning | Action |
|---|---|---|
| `permanent` | 4xx — bad input or resource not found | Fix the request; do not retry |
| `transient` | 5xx or network error | Retry with backoff |

Common error codes:

| Code | HTTP | Cause |
|---|---|---|
| `NO_OPEN_PROJECT` | 412 | No project open — call `open_project` first |
| `HTTP_404` | 404 | Resource with given ID not found |
| `HTTP_400` | 400 | Invalid request body |
| `CONNECTION_ERROR` | — | AURELION Manager not reachable |
| `TIMEOUT` | — | Request exceeded 30 s timeout |

---

## Running Tests

```bash
pytest
```

Tests use `pytest-httpx` to mock all HTTP calls — no running AURELION Manager is needed.

To run a specific test file:

```bash
pytest tests/test_vehicles.py -v
```


## Project Structure

```
src/
└── aurelion_manager_mcp/
├── __init__.py          # Package version
├── client.py            # Async HTTP client wrapper with error classification
├── server.py            # FastMCP entry point, resources, and prompts
└── tools/
    ├── vehicles.py      # Vehicle CRUD tools
    ├── sensors.py       # Sensor CRUD tools
    ├── scenarios.py     # Scenario CRUD + validation tools
    ├── systems.py       # System CRUD tools
    ├── simulation.py    # Simulation control tools
    ├── projects.py      # Project management tools
    └── general.py       # Version and log file tools
tests/
├── conftest.py
├── test_vehicles.py
├── test_sensors.py
├── test_scenarios.py
├── test_systems.py
└── test_simulation.py
```

## Extending the Server

### Adding a new tool

1. **Define an input model** (Pydantic `BaseModel`) in the relevant tool file under `aurelion_manager_mcp/tools/`.
   Every `Field` must include a `description` with a concrete example.

2. **Write an async tool function** that calls `client.api_request(...)` and returns `json.dumps(result, indent=2)`.

3. **Set all four annotations** in the `register_tools` call:
   - `readOnlyHint` — `True` for GET-only operations
   - `destructiveHint` — `False` for additive/non-destructive operations
   - `idempotentHint` — `True` if calling multiple times is safe
   - `openWorldHint` — `False` (the AURELION Manager is a closed local domain)

4. **Register the tool** inside `register_tools(mcp)`:
   ```python
   mcp.tool(annotations=ToolAnnotations(...))(my_new_tool)
   ```

5. **Write unit tests** in `tests/` using `httpx_mock` to mock the HTTP responses.


## API Reference

The underlying REST API is documented via OpenAPI at:

```
http://<aurelion-manager-host>:8584/api/aurelionmanager/v1.0/swagger
```

## Support

For technical questions and issues related to the dSPACE MCP Servers and related GitHub repositories, please [open a GitHub issue](https://github.com/dspace-group/AURELIONManagerMCP/issues).
As a valued dSPACE customer, you are always welcome to [contact dSPACE Support directly](https://www.dspace.com/go/supportrequest).

