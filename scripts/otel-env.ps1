param(
    [Parameter(Mandatory = $true)]
    [string]$ServiceName
)

$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path Env:OTEL_ENABLED)) {
    $otelMarker = Join-Path $projectRoot ".otel/enabled"
    $env:OTEL_ENABLED = if (Test-Path $otelMarker) { "true" } else { "false" }
}
if (-not $env:OTEL_SERVICE_NAME) { $env:OTEL_SERVICE_NAME = $ServiceName }
if (-not $env:OTEL_TRACES_SAMPLER) { $env:OTEL_TRACES_SAMPLER = "always_on" }

if ($ServiceName -eq "gateway") {
    $env:APISIX_OTEL_ENABLED = $env:OTEL_ENABLED
}

if ($ServiceName -eq "gozero") {
    $env:OTEL_DISABLED = if ($env:OTEL_ENABLED -eq "true") { "false" } else { "true" }
    if (-not $env:OTEL_EXPORTER_OTLP_ENDPOINT) {
        $env:OTEL_EXPORTER_OTLP_ENDPOINT = "127.0.0.1:4318"
    }
    if (-not $env:OTEL_TRACES_SAMPLER_RATIO) { $env:OTEL_TRACES_SAMPLER_RATIO = "1.0" }
    return
}

if (-not $env:OTEL_EXPORTER_OTLP_ENDPOINT) {
    $env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://127.0.0.1:4318"
}
if (-not $env:OTEL_EXPORTER_OTLP_TRACES_ENDPOINT) {
    $env:OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = "$($env:OTEL_EXPORTER_OTLP_ENDPOINT.TrimEnd('/'))/v1/traces"
}

if ($ServiceName -eq "spring" -and $env:OTEL_ENABLED -eq "true") {
    $agentVersion = if ($env:OTEL_JAVA_AGENT_VERSION) { $env:OTEL_JAVA_AGENT_VERSION } else { "2.31.1" }
    $agentDir = Join-Path $projectRoot ".otel"
    $agentPath = Join-Path $agentDir "opentelemetry-javaagent.jar"
    if (-not (Test-Path $agentPath)) {
        New-Item -ItemType Directory -Force -Path $agentDir | Out-Null
        Invoke-WebRequest -UseBasicParsing -Uri "https://maven.aliyun.com/repository/public/io/opentelemetry/javaagent/opentelemetry-javaagent/$agentVersion/opentelemetry-javaagent-$agentVersion.jar" -OutFile $agentPath
    }
    if ($env:JAVA_TOOL_OPTIONS -notlike "*-javaagent:$agentPath*") {
        $env:JAVA_TOOL_OPTIONS = "$($env:JAVA_TOOL_OPTIONS) -javaagent:$agentPath".Trim()
    }
}
