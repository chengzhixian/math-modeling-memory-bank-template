const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

execFileSync(process.execPath, [path.join(__dirname, 'q4_analysis.js')], { stdio: 'ignore' });
const result = JSON.parse(fs.readFileSync(path.join(__dirname, '../../outputs/zhh/legacy_baseline/q4_results.json'), 'utf8'));

assert.equal(result.audit.explicitClosedRowsIncluded, 0, 'explicit Epoch no must not be treated as open');
assert.equal(result.audit.explicitClosedLicenseConflicts, 6);
assert.equal(result.audit.leaderboardUsableOpenRows, 2672);
assert.equal(result.openFilterSensitivity.strictEpochYes.n, 424);
assert.ok(result.openFilterSensitivity.strictEpochYes.n > 0);
assert.ok(result.openFilterSensitivity.licenseProxyExpanded.n > result.openFilterSensitivity.strictEpochYes.n);
assert.ok(Number.isFinite(result.typeSensitivity.pretrained.coefficients.month));
assert.ok(Number.isFinite(result.typeSensitivity.nonPretrained.coefficients.month));
assert.ok(Math.abs(result.typeSensitivity.pretrained.coefficients.month - result.typeSensitivity.nonPretrained.coefficients.month) > 0.1);
assert.equal(result.forecast.predictions.length, 0);
const forecastCsv = fs.readFileSync(path.join(__dirname, '../../outputs/zhh/legacy_baseline/frontier_forecast.csv'), 'utf8');
assert.match(forecastCsv, /not_identified_for_compute_slowdown/);
assert.ok(!forecastCsv.includes('47.86') && !forecastCsv.includes('49.33'));
