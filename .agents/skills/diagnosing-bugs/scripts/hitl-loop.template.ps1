# Human-in-the-loop reproduction loop for PowerShell on Windows.
# Copy this file, edit the steps below, and run it:
#   powershell -File .\hitl-loop.template.ps1

function Step-Instruction {
    param([string]$Instruction)
    Write-Host "`n>>> $Instruction" -ForegroundColor Cyan
    Read-Host "    [Press Enter when done]"
}

function Capture-Input {
    param(
        [string]$Question
    )
    Write-Host "`n>>> $Question" -ForegroundColor Yellow
    $ans = Read-Host "    >"
    return $ans
}

# --- edit below ---------------------------------------------------------

Step-Instruction "Open the API docs at http://localhost:8000/docs or trigger the endpoint."

$errored = Capture-Input "Did the request return an error? (y/n)"
$errorMsg = Capture-Input "Paste the error message or status code (or 'none'):"

# --- edit above ---------------------------------------------------------

Write-Host "`n--- Captured ---" -ForegroundColor Green
Write-Host "ERRORED=$errored"
Write-Host "ERROR_MSG=$errorMsg"
