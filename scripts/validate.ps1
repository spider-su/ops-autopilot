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

Invoke-Step 'Kustomize: production' {
    kubectl kustomize clusters/prd --load-restrictor LoadRestrictionsNone | Out-Null
}

Invoke-Step 'Kustomize: development' {
    kubectl kustomize clusters/dev --load-restrictor LoadRestrictionsNone | Out-Null
}

Write-Host 'Repository validation passed.'
