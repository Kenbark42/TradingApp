# PowerShell script to launch the AlgoTrade Simulator using the correct virtual environment

Write-Host "Attempting to launch AlgoTrade Simulator..."

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Construct the expected path to the python executable within the .venv
$PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"

# Construct the expected path to the app script
$AppScript = Join-Path $ScriptDir "app.py"

# Check if the Python executable exists
if (-not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found at '$PythonExe'. Please ensure the .venv exists and is correctly structured."
    Read-Host -Prompt "Press Enter to exit"
    exit 1
}

# Check if the app script exists
if (-not (Test-Path $AppScript)) {
    Write-Error "Application script not found at '$AppScript'."
    Read-Host -Prompt "Press Enter to exit"
    exit 1
}

# Execute the application script using the virtual environment's Python
Write-Host "Executing: $PythonExe $AppScript"
& $PythonExe $AppScript $args

# Keep the window open after the app closes to see output
Write-Host "Application finished."
Read-Host -Prompt "Press Enter to exit" 