param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$repoPath = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$repoPrefix = $repoPath.TrimEnd([char[]]'\/') + [System.IO.Path]::DirectorySeparatorChar
$manifestPath = Join-Path $repoPath 'data/raw/F_MANIFEST.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding utf8 | ConvertFrom-Json
if ($manifest.schema_version -ne 1 -or $manifest.hash_algorithm -ne 'SHA256') {
    throw 'Unsupported manifest version or hash algorithm.'
}
if (@($manifest.files).Count -ne $manifest.file_count) {
    throw 'Manifest file count is inconsistent.'
}

$expected = @{}
$failures = [System.Collections.Generic.List[string]]::new()
[long]$verifiedBytes = 0
foreach ($entry in $manifest.files) {
    $absolutePath = [System.IO.Path]::GetFullPath((Join-Path $repoPath $entry.path))
    if (-not $absolutePath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Manifest path outside repository: $($entry.path)"
    }
    if ($expected.ContainsKey($entry.path)) { throw "Duplicate manifest path: $($entry.path)" }
    $expected[$entry.path] = $true
    if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
        $failures.Add("Missing: $($entry.path)")
        continue
    }
    $actualFile = Get-Item -LiteralPath $absolutePath
    if ($actualFile.Length -ne $entry.bytes) {
        $failures.Add("Size mismatch: $($entry.path)")
        continue
    }
    $actualHash = (Get-FileHash -LiteralPath $absolutePath -Algorithm SHA256).Hash
    if ($actualHash -ne $entry.sha256) {
        $failures.Add("SHA256 mismatch: $($entry.path)")
        continue
    }
    $verifiedBytes += $actualFile.Length
}
foreach ($assetDirectory in @('problem/F', 'data/raw/real_attachments')) {
    $directoryPath = Join-Path $repoPath $assetDirectory
    foreach ($actualFile in @(Get-ChildItem -LiteralPath $directoryPath -Recurse -File)) {
        $relativePath = $actualFile.FullName.Substring($repoPrefix.Length).Replace('\', '/')
        if (-not $expected.ContainsKey($relativePath)) {
            $failures.Add("Unlisted file: $relativePath")
        }
    }
}
if ($failures.Count -gt 0) {
    $failures | Select-Object -First 20 | Write-Output
    throw "$($failures.Count) data verification failures. For missing or pointer-only LFS files, run git lfs pull first."
}
if ($verifiedBytes -ne $manifest.total_bytes) { throw 'Total byte count is inconsistent.' }
[pscustomobject]@{
    Status = 'PASS'
    Files = $manifest.file_count
    Bytes = $verifiedBytes
    Algorithm = 'SHA256'
}
