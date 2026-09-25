param(
  [string]$Python = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
  [switch]$SkipQ1Export
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
$env:PYTHONPATH = ((Resolve-Path '.venv/cyj-deps').Path + ';' + (Resolve-Path 'src/cyj').Path)
if (-not $SkipQ1Export) {
  Write-Host 'Q1 upstream export stage: reads source A4, publishes derived 512 x 17 bundle.'
  & $Python -B src/chm/export_q1_q2_bundle.py
  if ($LASTEXITCODE -ne 0) { throw 'Q1 export failed' }
}
Write-Host 'Q2 consumer stage: reads Q1 derived bundle and frozen B-side results.'
& $Python -B src/cyj/build_q2_final.py
if ($LASTEXITCODE -ne 0) { throw 'Q2 build failed' }
& $Python -B src/cyj/build_v6_fixtures.py
if ($LASTEXITCODE -ne 0) { throw 'v6 fixture generation failed' }
& $Python -B -m unittest discover -s src/cyj/tests -p test_q2_final_v6.py -v
if ($LASTEXITCODE -ne 0) { throw 'v6 acceptance tests failed' }
& $Python -B src/cyj/finalize_q2_acceptance.py
if ($LASTEXITCODE -ne 0) { throw 'acceptance finalization failed' }
