param(
    [string]$TexBin = '',
    [string]$OutputName = 'chm-q1-all22-latest',
    [string]$SourceName = 'main.tex'
)

$ErrorActionPreference = 'Stop'
if ($OutputName -notmatch '^[A-Za-z0-9_-]+$') {
    throw 'OutputName must be a simple filename without an extension.'
}
if ($SourceName -notmatch '^[A-Za-z0-9_-]+\.tex$') {
    throw 'SourceName must be a TeX filename in paper/latex.'
}
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$paperRoot = Join-Path $repoRoot 'paper/latex'
$buildRoot = Join-Path $paperRoot ".build/$OutputName"
$outputRoot = Join-Path $paperRoot 'output'

# Resolve an installed engine even when a new terminal has an incomplete PATH.
if (-not $TexBin) {
    $engine = Get-Command xelatex -ErrorAction SilentlyContinue
    if ($engine) {
        $TexBin = Split-Path $engine.Source
    } else {
        foreach ($candidate in @(
            (Join-Path $env:LOCALAPPDATA 'Programs/MiKTeX/miktex/bin/x64'),
            (Join-Path $env:ProgramFiles 'MiKTeX/miktex/bin/x64')
        )) {
            if (Test-Path -LiteralPath (Join-Path $candidate 'xelatex.exe')) {
                $TexBin = $candidate
                break
            }
        }
    }
}
if (-not $TexBin) { throw 'XeLaTeX not found. Supply -TexBin with the installed TeX binary directory.' }
$xelatex = Join-Path $TexBin 'xelatex.exe'
$bibtex = Join-Path $TexBin 'bibtex.exe'
foreach ($tool in @($xelatex, $bibtex)) {
    if (-not (Test-Path -LiteralPath $tool)) { throw "Required executable missing: $tool" }
}

New-Item -ItemType Directory -Force -Path $buildRoot, $outputRoot | Out-Null
$sourcePaths = @($SourceName, 'gmcmthesis.cls', 'gmcm.bst', 'references.bib')
if ($SourceName -eq 'q1_final.tex') {
    $sourcePaths += 'sections/chm/q1.tex'
    $sourcePaths += Get-ChildItem -LiteralPath (Join-Path $paperRoot 'figures/chm') -File -Filter 'q1_*.png' |
        ForEach-Object { [IO.Path]::GetRelativePath($paperRoot, $_.FullName) }
} else {
    foreach ($folder in @('sections', 'figures')) {
        $sourcePaths += Get-ChildItem -LiteralPath (Join-Path $paperRoot $folder) -Recurse -File |
            ForEach-Object { [IO.Path]::GetRelativePath($paperRoot, $_.FullName) }
    }
}
$sourceManifest = @()
foreach ($relative in $sourcePaths) {
    $source = Join-Path $paperRoot $relative
    $target = Join-Path $buildRoot $relative
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
    $sourceManifest += [ordered]@{
        path = ('paper/latex/' + $relative.Replace('\', '/'))
        sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
if ($SourceName -ne 'main.tex') {
    Copy-Item -LiteralPath (Join-Path $buildRoot $SourceName) -Destination (Join-Path $buildRoot 'main.tex') -Force
}

function Invoke-TexStep([string]$Executable, [string[]]$Arguments, [string]$LogName) {
    $step = Start-Process -FilePath $Executable -ArgumentList $Arguments -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $LogName -RedirectStandardError "$LogName.stderr"
    if ($step.ExitCode -ne 0) {
        Get-Content -LiteralPath $LogName -Tail 35
        Get-Content -LiteralPath "$LogName.stderr" -Tail 15
        throw "Compilation failed; inspect $buildRoot/$LogName"
    }
}

Push-Location $buildRoot
try {
    $texArgs = @('--interaction=nonstopmode', '--halt-on-error', '--file-line-error', '--recorder', 'main.tex')
    Invoke-TexStep $xelatex $texArgs 'pass1.txt'
    Invoke-TexStep $bibtex @('main') 'bibtex.txt'
    Invoke-TexStep $xelatex $texArgs 'pass2.txt'
    Invoke-TexStep $xelatex $texArgs 'pass3.txt'
    $log = Get-Content -LiteralPath 'main.log' -Raw
    if ($log -match 'Rerun to get cross-references right|Label\(s\) may have changed') {
        Invoke-TexStep $xelatex $texArgs 'pass4.txt'
        $log = Get-Content -LiteralPath 'main.log' -Raw
    }
    $bad = 'There were undefined references|(?:Reference|Citation) .+ undefined|Missing character:|Overfull \\[hv]box|Label\(s\) may have changed'
    if ($log -match $bad) {
        throw 'The PDF was built but failed the reference/glyph/overflow gate. Inspect main.log before delivery.'
    }
    if ($log -notmatch 'Output written on .+?\((\d+) pages?\)') {
        throw 'Could not confirm the generated PDF page count.'
    }
    $pageCount = [int]$Matches[1]
    $pdfPath = Join-Path $outputRoot "$OutputName.pdf"
    Copy-Item -LiteralPath 'main.pdf' -Destination $pdfPath -Force
    $report = [ordered]@{
        built_at = [DateTimeOffset]::Now.ToString('o')
        source_mode = 'snapshot_of_current_working_tree'
        engine = 'XeLaTeX + BibTeX + XeLaTeX passes until references stabilize'
        page_count = $pageCount
        reference_glyph_overflow_gate = 'passed'
        visual_review = 'separate_review_required'
        pdf_sha256 = (Get-FileHash -LiteralPath $pdfPath -Algorithm SHA256).Hash.ToLowerInvariant()
        source_files = $sourceManifest
    }
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $outputRoot "$OutputName-build.json") -Encoding utf8
    Write-Output "Built $pdfPath ($pageCount pages); references, glyphs and overflow checks passed."
} finally {
    Pop-Location
}
