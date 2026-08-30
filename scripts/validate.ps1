$ErrorActionPreference = 'Stop'

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,
        [Parameter(Mandatory = $true)]
        [scriptblock] $Command
    )

    Write-Host "==> $Name"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Invoke-Step 'Markdown links' {
    python .\tools\check_markdown_links.py
}

$chartTargets = @(
    @('investory', 'prd'),
    @('investory', 'dev'),
    @('smartapp', 'prd'),
    @('smartapp', 'dev'),
    @('postgres', 'prd')
)

foreach ($target in $chartTargets) {
    $app = $target[0]
    $environment = $target[1]
    Invoke-Step "Helm lint: $app ($environment)" {
        helm lint "applications/$app" `
            -f "applications/$app/values.yaml" `
            -f "applications/$app/values-$environment.yaml"
    }
}

Invoke-Step 'Chart policy checks' {
    $chartNames = @('investory', 'smartapp', 'postgres')
    foreach ($chartName in $chartNames) {
        $schemaPath = "applications/$chartName/values.schema.json"
        if (-not (Test-Path -LiteralPath $schemaPath)) {
            throw "Missing Helm values schema: $schemaPath"
        }

        $productionValues = Get-Content -Raw -LiteralPath "applications/$chartName/values-prd.yaml"
        if ($productionValues -notmatch '(?m)^\s*digest:\s*sha256:[0-9a-f]{64}\s*$') {
            throw "Production image digest is not pinned in applications/$chartName/values-prd.yaml"
        }
        if ($productionValues -notmatch '(?m)^\s*pullPolicy:\s*IfNotPresent\s*$') {
            throw "Production image pullPolicy must be IfNotPresent in applications/$chartName/values-prd.yaml"
        }
    }
}

$renderRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'ops-autopilot-rendered'
$workloadRender = Join-Path $renderRoot 'workloads'
$upstreamRender = Join-Path $renderRoot 'upstream'
$kustomizeRender = Join-Path $renderRoot 'kustomize'
New-Item -ItemType Directory -Force -Path $workloadRender, $upstreamRender, $kustomizeRender | Out-Null

foreach ($target in $chartTargets) {
    $app = $target[0]
    $environment = $target[1]
    $output = Join-Path $workloadRender "$app-$environment.yaml"
    Invoke-Step "Helm render: $app ($environment)" {
        $rendered = helm template "$app-$environment" "applications/$app" `
            -f "applications/$app/values.yaml" `
            -f "applications/$app/values-$environment.yaml"
        if ($LASTEXITCODE -ne 0) { throw "Helm render failed for $app ($environment)" }
        $rendered | Set-Content -LiteralPath $output -Encoding utf8
    }
}

Invoke-Step 'Pinned upstream chart rendering' {
    python .\tools\render_upstream_charts.py --output-dir $upstreamRender
}

Invoke-Step 'Manifest policy and documentation checks' {
    python .\tools\check_manifest_policies.py --workload-dir $workloadRender
}

Invoke-Step 'Kustomize: production' {
    $rendered = kubectl kustomize clusters/prd
    if ($LASTEXITCODE -ne 0) { throw 'Production Kustomize rendering failed' }
    $rendered | Set-Content -LiteralPath (Join-Path $kustomizeRender 'clusters-prd.yaml') -Encoding utf8
}

Invoke-Step 'Kustomize: development' {
    $rendered = kubectl kustomize clusters/dev
    if ($LASTEXITCODE -ne 0) { throw 'Development Kustomize rendering failed' }
    $rendered | Set-Content -LiteralPath (Join-Path $kustomizeRender 'clusters-dev.yaml') -Encoding utf8
}

foreach ($target in @('infrastructure/platform', 'infrastructure/argocd', 'infrastructure/monitoring')) {
    $outputName = $target -replace '/', '-'
    Invoke-Step "Kustomize: $target" {
        $rendered = kubectl kustomize $target
        if ($LASTEXITCODE -ne 0) { throw "Kustomize rendering failed for $target" }
        $rendered | Set-Content -LiteralPath (Join-Path $kustomizeRender "${outputName}.yaml") -Encoding utf8
    }
}

if (-not (Get-Command kubeconform -ErrorAction SilentlyContinue)) {
    throw 'kubeconform is required. Install kubeconform v0.6.7 and put it on PATH.'
}

Invoke-Step 'Kubernetes schema validation' {
    $files = Get-ChildItem -LiteralPath $renderRoot -Recurse -File -Filter '*.yaml' | Select-Object -ExpandProperty FullName
    kubeconform -strict -summary -skip CustomResourceDefinition -kubernetes-version 1.32.0 `
        -schema-location default `
        -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' `
        $files
}

Write-Host 'Repository validation passed.'
