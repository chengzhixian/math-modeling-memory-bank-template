param(
  [string]$Python = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
$env:PYTHONPATH = ((Resolve-Path '.venv/cyj-deps').Path + ';' + (Resolve-Path 'src/cyj').Path)

Write-Host 'Q1 upstream: versioned 512-recipe export and fixed interaction candidate reproduction.'
& $Python -B src/chm/export_q1_q2_bundle.py
if ($LASTEXITCODE -ne 0) { throw 'Q1 recipe export failed' }
& $Python -B src/chm/export_q1_interaction_bundle.py
if ($LASTEXITCODE -ne 0) { throw 'Q1 interaction export failed' }

Write-Host 'Q2 consumer: rebuild prior V3 results without reopening source A.'
& (Join-Path $PSScriptRoot 'run_cyj_q2_final.ps1') -Python $Python -SkipQ1Export
if ($LASTEXITCODE -ne 0) { throw 'Q2 V3 regression failed' }

Write-Host 'Q2 closure: derived interaction analysis, facts packet and independent assertions.'
& $Python -B src/cyj/analyze_domain_interactions_q2.py
if ($LASTEXITCODE -ne 0) { throw 'Q2 interaction consumer failed' }
& $Python -B src/cyj/build_q2_final_facts.py
if ($LASTEXITCODE -ne 0) { throw 'Q2 facts generation failed' }
& $Python -B src/cyj/final_q2_closure_check.py
if ($LASTEXITCODE -ne 0) { throw 'Q2 final closure checks failed' }
& $Python -B -m unittest discover -s src/cyj/tests -q
if ($LASTEXITCODE -ne 0) { throw 'CYJ full regression suite failed' }
