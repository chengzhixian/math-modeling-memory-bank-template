$ErrorActionPreference = 'Stop'
$paperRoot = Split-Path $PSScriptRoot
$buildRoot = Join-Path $PSScriptRoot 'build'
$engineRoot = 'C:\Users\Administrator\AppData\Local\Programs\MiKTeX\miktex\bin\x64'
Get-ChildItem -LiteralPath $paperRoot -File | Where-Object {$_.Extension -in '.tex','.cls','.bib','.bst'} | Copy-Item -Destination $buildRoot -Force
Copy-Item -LiteralPath (Join-Path $paperRoot 'figures') -Destination $buildRoot -Recurse -Force
Push-Location $buildRoot
try {
    $arguments = @('--disable-installer','--interaction=nonstopmode','--halt-on-error','--file-line-error','--recorder','--jobname=paper-r2','example.tex')
    & (Join-Path $engineRoot 'xelatex.exe') @arguments *> 'pass1.txt'
    if ($LASTEXITCODE -ne 0) {Get-Content 'pass1.txt' -Tail 35; throw 'First XeLaTeX pass failed'}
    & (Join-Path $engineRoot 'bibtex.exe') '--disable-installer' 'paper-r2' *> 'bibtex.txt'
    if ($LASTEXITCODE -ne 0) {Get-Content 'bibtex.txt' -Tail 35; throw 'BibTeX failed'}
    foreach ($pass in 2..4) {
        & (Join-Path $engineRoot 'xelatex.exe') @arguments *> "pass$pass.txt"
        if ($LASTEXITCODE -ne 0) {Get-Content "pass$pass.txt" -Tail 35; throw "XeLaTeX pass $pass failed"}
    }
    Copy-Item -LiteralPath 'paper-r2.pdf' -Destination (Join-Path $paperRoot 'output/pdf/论文_R2补充版.pdf') -Force
    Select-String -Path 'paper-r2.log' -Pattern 'Overfull|undefined|Missing character|Label\(s\)|Output written' | Select-Object -Last 25
} finally {Pop-Location}
