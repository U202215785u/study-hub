function Test-StudyHubBackendProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandLine,
        [Parameter(Mandatory = $true)]
        [string]$ProjectDir
    )

    return $CommandLine -match '(?i)(?:^|\s)-m\s+uvicorn\s+main:app(?:\s|$)' -and
        $CommandLine -match '(?i)(?:^|\s)--port\s+8741(?:\s|$)'
}
