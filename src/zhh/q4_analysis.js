const fs = require('fs');
const path = require('path');
const repositoryRoot = path.resolve(__dirname, '..', '..');
const dataRoot = path.join(repositoryRoot, 'data', 'raw', 'real_attachments', 'C_efficiency_evolution');
// v1 is a historical diagnostic. Current publication is q4_complete.py (v2).
const outputRoot = path.join(repositoryRoot, 'outputs', 'zhh', 'legacy_baseline');
fs.mkdirSync(outputRoot, { recursive: true });

const benchmarkColumns = ['IFEval', 'BBH', 'MATH Lvl 5', 'GPQA', 'MUSR', 'MMLU-PRO'];
const bridgeColumns = ['LB_IFEval', 'LB_BBH', 'LB_MATH', 'LB_GPQA', 'LB_MUSR', 'LB_MMLU_PRO'];

function readCsv(fileName) {
  const text = fs.readFileSync(path.join(dataRoot, fileName), 'utf8').replace(/^\uFEFF/, '');
  const records = [];
  let record = [];
  let field = '';
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        field += character;
      }
    } else if (character === '"') {
      quoted = true;
    } else if (character === ',') {
      record.push(field);
      field = '';
    } else if (character === '\n') {
      record.push(field.replace(/\r$/, ''));
      if (record.some(value => value.length)) records.push(record);
      record = [];
      field = '';
    } else {
      field += character;
    }
  }
  if (field.length || record.length) {
    record.push(field.replace(/\r$/, ''));
    records.push(record);
  }
  const [headers, ...rows] = records;
  return rows.map(row => Object.fromEntries(headers.map((header, index) => [header, row[index] ?? ''])));
}

function number(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function mean(values) {
  const valid = values.filter(Number.isFinite);
  return valid.length ? valid.reduce((sum, value) => sum + value, 0) / valid.length : null;
}

function quantile(values, probability) {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const index = (sorted.length - 1) * probability;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (index - lower);
}

function rmse(actual, predicted) {
  return Math.sqrt(mean(actual.map((value, index) => (value - predicted[index]) ** 2)));
}

function mae(actual, predicted) {
  return mean(actual.map((value, index) => Math.abs(value - predicted[index])));
}

function rSquared(actual, predicted) {
  const average = mean(actual);
  const residual = actual.reduce((sum, value, index) => sum + (value - predicted[index]) ** 2, 0);
  const total = actual.reduce((sum, value) => sum + (value - average) ** 2, 0);
  return total > 0 ? 1 - residual / total : null;
}

function fitOls(rows, featureNames, targetName, weights = null) {
  const design = rows.map(row => [1, ...featureNames.map(name => row[name])]);
  const target = rows.map(row => row[targetName]);
  const columnCount = design[0].length;
  const normalMatrix = Array.from({ length: columnCount }, () => Array(columnCount).fill(0));
  const normalVector = Array(columnCount).fill(0);
  for (let rowIndex = 0; rowIndex < design.length; rowIndex += 1) {
    const weight = weights ? weights[rowIndex] : 1;
    for (let left = 0; left < columnCount; left += 1) {
      normalVector[left] += weight * design[rowIndex][left] * target[rowIndex];
      for (let right = 0; right < columnCount; right += 1) {
        normalMatrix[left][right] += weight * design[rowIndex][left] * design[rowIndex][right];
      }
    }
  }
  for (let index = 0; index < columnCount; index += 1) normalMatrix[index][index] += 1e-9;
  const augmented = normalMatrix.map((row, index) => [...row, normalVector[index]]);
  for (let pivot = 0; pivot < columnCount; pivot += 1) {
    let best = pivot;
    for (let row = pivot + 1; row < columnCount; row += 1) {
      if (Math.abs(augmented[row][pivot]) > Math.abs(augmented[best][pivot])) best = row;
    }
    [augmented[pivot], augmented[best]] = [augmented[best], augmented[pivot]];
    if (Math.abs(augmented[pivot][pivot]) < 1e-12) throw new Error('Singular normal equation');
    const divisor = augmented[pivot][pivot];
    for (let column = pivot; column <= columnCount; column += 1) augmented[pivot][column] /= divisor;
    for (let row = 0; row < columnCount; row += 1) {
      if (row === pivot) continue;
      const factor = augmented[row][pivot];
      for (let column = pivot; column <= columnCount; column += 1) {
        augmented[row][column] -= factor * augmented[pivot][column];
      }
    }
  }
  const beta = augmented.map(row => row[columnCount]);
  const predict = row => beta[0] + featureNames.reduce((sum, name, index) => sum + beta[index + 1] * row[name], 0);
  const predicted = rows.map(predict);
  return {
    featureNames,
    coefficients: Object.fromEntries(['intercept', ...featureNames].map((name, index) => [name, beta[index]])),
    predict,
    metrics: { n: rows.length, rmse: rmse(target, predicted), mae: mae(target, predicted), r2: rSquared(target, predicted) },
  };
}

function csvEscape(value) {
  if (value === null || value === undefined) return '';
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function writeCsv(fileName, rows, columns) {
  const output = [columns.join(','), ...rows.map(row => columns.map(column => csvEscape(row[column])).join(','))].join('\n');
  fs.writeFileSync(path.join(outputRoot, fileName), `${output}\n`, 'utf8');
}

function classifyType(rawType) {
  const value = String(rawType || '').toLowerCase();
  return value.includes('pretrained') ? 'pretrained' : 'non_pretrained';
}

function isOpenModel(row) {
  const openWeights = String(row.Epoch_AI_Open_Weights || '').trim().toLowerCase();
  const license = String(row['Hub License'] || '').trim().toLowerCase();
  if (openWeights === 'no') return false;
  return openWeights === 'yes' || (license && !['unknown', 'other', 'n/a', 'nan'].includes(license));
}

function parseLeaderboard() {
  const rows = readCsv('leaderboard_enhanced.csv');
  const minimumDate = Date.parse('2024-06-01T00:00:00Z');
  const parsedRows = rows.map(row => {
    const timestamp = Date.parse(row['Submission Date']);
    const scores = benchmarkColumns.map(column => number(row[column]));
    return {
      model: row.Model,
      paramsB: number(row['#Params (B)']),
      submissionDate: row['Submission Date'],
      timestamp,
      month: Number.isFinite(timestamp) ? (timestamp - minimumDate) / (365.25 / 12 * 24 * 3600 * 1000) : null,
      license: row['Hub License'],
      epochOpenWeights: row.Epoch_AI_Open_Weights,
      epochOpenStatus: String(row.Epoch_AI_Open_Weights || '').trim().toLowerCase(),
      type: classifyType(row.Type),
      open: isOpenModel(row),
      score: mean(scores),
      scores,
      logParams: number(row['#Params (B)']) > 0 ? Math.log10(number(row['#Params (B)'])) : null,
      nonPretrainedIndicator: classifyType(row.Type) === 'non_pretrained' ? 1 : 0,
    };
  });
  const eligibleRows = parsedRows.filter(row => row.open && row.paramsB > 0 && Number.isFinite(row.timestamp));
  parseLeaderboard.audit = {
    eligibleBeforeCompleteCase: eligibleRows.length,
    incompleteSixScoreRowsExcluded: eligibleRows.filter(row => !row.scores.every(Number.isFinite)).length,
    explicitClosedLicenseConflicts: parsedRows.filter(row => row.epochOpenStatus === 'no' && String(row.license || '').trim() && !['unknown', 'other', 'n/a', 'nan'].includes(String(row.license).trim().toLowerCase()) && row.paramsB > 0 && Number.isFinite(row.timestamp) && row.scores.every(Number.isFinite)).length,
  };
  return eligibleRows.filter(row => row.scores.every(Number.isFinite));
}

function aggregateDetailedResults() {
  const root = path.join(dataRoot, 'detailed_results');
  const directories = fs.readdirSync(root, { withFileTypes: true }).filter(entry => entry.isDirectory());
  const aggregates = [];
  const failures = [];
  for (const directory of directories) {
    const directoryPath = path.join(root, directory.name);
    const files = fs.readdirSync(directoryPath)
      .filter(name => name.endsWith('.json'))
      .sort((left, right) => right.localeCompare(left));
    let selected = null;
    for (const file of files) {
      try {
        const parsed = JSON.parse(fs.readFileSync(path.join(directoryPath, file), 'utf8'));
        const results = parsed.results || {};
        const taskRows = [];
        for (const [task, metrics] of Object.entries(results)) {
          if (!task.startsWith('leaderboard_bbh_') || task === 'leaderboard_bbh') continue;
          const score = number(metrics['acc_norm,none']);
          if (score !== null) taskRows.push({ task, score: score * 100 });
        }
        if (!taskRows.length) continue;
        selected = { file, taskRows };
        break;
      } catch (error) {
        failures.push({ modelDirectory: directory.name, file, reason: error.message });
      }
    }
    if (!selected) continue;
    const taskScores = selected.taskRows.map(row => row.score);
    aggregates.push({
      modelDirectory: directory.name,
      sourceFile: selected.file,
      bbhTaskCount: taskScores.length,
      bbhMacroMean: mean(taskScores),
      bbhTaskSd: Math.sqrt(mean(taskScores.map(value => (value - mean(taskScores)) ** 2))),
      bbhTaskMin: Math.min(...taskScores),
      bbhTaskMax: Math.max(...taskScores),
    });
  }
  return { aggregates, failures, directoryCount: directories.length };
}

function analyzeContribution(leaderboardRows) {
  const rows = leaderboardRows.map(row => ({ ...row, scoreValue: row.score }));
  const featureNames = ['logParams', 'month', 'nonPretrainedIndicator'];
  const model = fitOls(rows, featureNames, 'scoreValue');
  const minMonth = Math.min(...rows.map(row => row.month));
  const maxMonth = Math.max(...rows.map(row => row.month));
  const firstWindow = rows.filter(row => row.month <= minMonth + 2);
  const lastWindow = rows.filter(row => row.month >= maxMonth - 2);
  const startProfile = {
    logParams: quantile(firstWindow.map(row => row.logParams), 0.95),
    month: mean(firstWindow.map(row => row.month)),
    nonPretrainedIndicator: mean(firstWindow.map(row => row.nonPretrainedIndicator)),
  };
  const endProfile = {
    logParams: quantile(lastWindow.map(row => row.logParams), 0.95),
    month: mean(lastWindow.map(row => row.month)),
    nonPretrainedIndicator: mean(lastWindow.map(row => row.nonPretrainedIndicator)),
  };
  const beta = model.coefficients;
  const scaleContribution = beta.logParams * (endProfile.logParams - startProfile.logParams);
  const timeContribution = beta.month * (endProfile.month - startProfile.month);
  const typeContribution = beta.nonPretrainedIndicator * (endProfile.nonPretrainedIndicator - startProfile.nonPretrainedIndicator);
  const absoluteTotal = Math.abs(scaleContribution) + Math.abs(timeContribution) + Math.abs(typeContribution);
  return {
    model,
    startProfile,
    endProfile,
    contributions: {
      scale: scaleContribution,
      nonScaleTime: timeContribution,
      modelTypeMix: typeContribution,
      scaleShareAbsolute: absoluteTotal ? Math.abs(scaleContribution) / absoluteTotal : null,
      nonScaleShareAbsolute: absoluteTotal ? (Math.abs(timeContribution) + Math.abs(typeContribution)) / absoluteTotal : null,
    },
  };
}

function analyzeSensitivity(rows) {
  const strict = rows.filter(row => row.epochOpenStatus === 'yes');
  const summarize = subset => {
    const contribution = analyzeContribution(subset);
    const forecast = forecastFrontier(subset);
    return {
      n: subset.length,
      coefficients: contribution.model.coefficients,
      fitMetrics: contribution.model.metrics,
      contributions: contribution.contributions,
      timeHoldout: forecast.timeHoldout,
      dateRange: [new Date(Math.min(...subset.map(row => row.timestamp))).toISOString().slice(0, 10), new Date(Math.max(...subset.map(row => row.timestamp))).toISOString().slice(0, 10)],
    };
  };
  const pretrained = rows.filter(row => row.type === 'pretrained');
  const nonPretrained = rows.filter(row => row.type === 'non_pretrained');
  const grouped = subset => {
    const fitted = fitOls(subset.map(row => ({ ...row, scoreValue: row.score })), ['logParams', 'month'], 'scoreValue');
    return { n: subset.length, coefficients: fitted.coefficients, fitMetrics: fitted.metrics };
  };
  const interactionRows = rows.map(row => ({ ...row, scoreValue: row.score, monthByType: row.month * row.nonPretrainedIndicator, logParamsByType: row.logParams * row.nonPretrainedIndicator }));
  const interaction = fitOls(interactionRows, ['logParams', 'month', 'nonPretrainedIndicator', 'monthByType', 'logParamsByType'], 'scoreValue');
  const latest = new Map();
  for (const row of rows) {
    if (!latest.has(row.model) || row.timestamp > latest.get(row.model).timestamp) latest.set(row.model, row);
  }
  const latestFit = fitOls([...latest.values()].map(row => ({ ...row, scoreValue: row.score })), ['logParams', 'month', 'nonPretrainedIndicator'], 'scoreValue');
  return {
    openFilterSensitivity: { strictEpochYes: summarize(strict), licenseProxyExpanded: summarize(rows) },
    typeSensitivity: {
      pretrained: grouped(pretrained), nonPretrained: grouped(nonPretrained),
      interaction: { n: rows.length, coefficients: interaction.coefficients, fitMetrics: interaction.metrics },
      latestModelRecord: { n: latest.size, coefficients: latestFit.coefficients, fitMetrics: latestFit.metrics },
    },
  };
}

function analyzeBridge() {
  const rawRows = readCsv('loss_benchmark_bridge_expanded.csv');
  const rows = rawRows.map(row => ({
    model: row.Model,
    source: row.Loss_Source,
    loss: number(row.Val_Loss),
    logParams: number(row.N_params_B) > 0 ? Math.log10(number(row.N_params_B)) : null,
    benchmarkScores: bridgeColumns.map(column => number(row[column])),
    comparability: String(row.Loss_Comparability || '').toLowerCase().startsWith('high') ? 'high' : 'medium',
  })).filter(row => Number.isFinite(row.loss) && Number.isFinite(row.logParams) && row.benchmarkScores.every(Number.isFinite));
  rows.forEach(row => { row.benchmark = mean(row.benchmarkScores); });
  const highRows = rows.filter(row => row.comparability === 'high');
  const highModel = fitOls(highRows, ['loss', 'logParams'], 'benchmark');
  const weightedModel = fitOls(rows, ['loss', 'logParams'], 'benchmark', rows.map(row => row.comparability === 'high' ? 1 : 0.35));
  const sorted = [...rows].sort((left, right) => left.loss - right.loss);
  const splitIndex = Math.max(3, Math.floor(sorted.length * 0.75));
  const train = sorted.slice(0, splitIndex);
  const test = sorted.slice(splitIndex);
  const validationModel = fitOls(train, ['loss', 'logParams'], 'benchmark', train.map(row => row.comparability === 'high' ? 1 : 0.35));
  const actual = test.map(row => row.benchmark);
  const predicted = test.map(validationModel.predict);
  const sources = [...new Set(rows.map(row => row.source))];
  const groupedActual = [];
  const groupedPredicted = [];
  for (const source of sources) {
    const sourceTest = rows.filter(row => row.source === source);
    const sourceTrain = rows.filter(row => row.source !== source);
    if (sourceTest.length === 0 || sourceTrain.length < 4) continue;
    const sourceModel = fitOls(sourceTrain, ['loss', 'logParams'], 'benchmark', sourceTrain.map(row => row.comparability === 'high' ? 1 : 0.35));
    sourceTest.forEach(row => {
      groupedActual.push(row.benchmark);
      groupedPredicted.push(sourceModel.predict(row));
    });
  }
  return {
    rows,
    highModel: { coefficients: highModel.coefficients, metrics: highModel.metrics },
    weightedModel: { coefficients: weightedModel.coefficients, metrics: weightedModel.metrics },
    lossHoldout: { nTrain: train.length, nTest: test.length, rmse: rmse(actual, predicted), mae: mae(actual, predicted), r2: rSquared(actual, predicted) },
    sourceHoldout: { nTest: groupedActual.length, rmse: rmse(groupedActual, groupedPredicted), mae: mae(groupedActual, groupedPredicted), r2: rSquared(groupedActual, groupedPredicted) },
  };
}

function analyzeEpochCompute() {
  const rows = readCsv('epoch_all_ai_models.csv').map(row => {
    const timestamp = Date.parse(row['Publication date']);
    const compute = number(row['Training compute (FLOP)']);
    const open = String(row['Open model weights?'] || '').trim().toLowerCase() === 'yes';
    return { timestamp, year: Number.isFinite(timestamp) ? new Date(timestamp).getUTCFullYear() : null, compute, open };
  }).filter(row => row.open && row.compute > 0 && row.year >= 2019 && row.year <= 2025);
  const annual = [];
  for (const year of [...new Set(rows.map(row => row.year))].sort()) {
    const yearRows = rows.filter(row => row.year === year);
    annual.push({ year, n: yearRows.length, frontierLogCompute: quantile(yearRows.map(row => Math.log10(row.compute)), 0.9) });
  }
  const growth = annual.slice(1).map((row, index) => row.frontierLogCompute - annual[index].frontierLogCompute);
  return { annual, medianAnnualLogGrowth: quantile(growth, 0.5), recentAnnualLogGrowth: growth.length ? growth[growth.length - 1] : null };
}

function analyzeTimeseries() {
  const rows = readCsv('leaderboard_extended_timeseries.csv').map(row => ({
    year: number(row.Year),
    paramsB: number(row.Params_B),
    score: number(row.Average),
    source: row.Source,
  })).filter(row => row.year && row.paramsB > 0 && Number.isFinite(row.score));
  const annual = [];
  for (const year of [...new Set(rows.map(row => row.year))].sort()) {
    const yearRows = rows.filter(row => row.year === year);
    annual.push({ year, n: yearRows.length, p95Score: quantile(yearRows.map(row => row.score), 0.95), maxScore: Math.max(...yearRows.map(row => row.score)) });
  }
  return { annual };
}

function forecastFrontier(leaderboardRows) {
  const rows = leaderboardRows.map(row => ({ ...row, scoreValue: row.score }));
  const cutoff = quantile(rows.map(row => row.timestamp), 0.8);
  const train = rows.filter(row => row.timestamp <= cutoff);
  const test = rows.filter(row => row.timestamp > cutoff);
  const validationModel = fitOls(train, ['logParams', 'month', 'nonPretrainedIndicator'], 'scoreValue');
  const validationActual = test.map(row => row.scoreValue);
  const validationPredicted = test.map(validationModel.predict);
  const fullModel = fitOls(rows, ['logParams', 'month', 'nonPretrainedIndicator'], 'scoreValue');
  const finalMonth = Math.max(...rows.map(row => row.month));
  const recentRows = rows.filter(row => row.month >= finalMonth - 2);
  const currentLogParamsFrontier = quantile(recentRows.map(row => row.logParams), 0.95);
  const nonPretrainedShare = mean(recentRows.map(row => row.nonPretrainedIndicator));
  const futureRow = {
    logParams: currentLogParamsFrontier,
    month: finalMonth + 12,
    nonPretrainedIndicator: nonPretrainedShare,
  };
  return {
    status: 'not_identified_for_compute_slowdown',
    statusReason: 'No validated mapping from the C4 compute frontier to the C1/C2 parameter frontier is available; adding compute growth to log10 parameter count is dimensionally unsupported.',
    model: { coefficients: fullModel.coefficients, metrics: fullModel.metrics },
    timeHoldout: { nTrain: train.length, nTest: test.length, rmse: rmse(validationActual, validationPredicted), mae: mae(validationActual, validationPredicted), r2: rSquared(validationActual, validationPredicted) },
    currentLogParamsFrontier,
    conditionalTimeOnly: {
      horizonMonths: 12,
      predictedScore: fullModel.predict(futureRow),
      interpretation: 'Conditional association forecast holding the current parameter frontier and model-type mix fixed; it is not a compute-slowdown forecast.',
    },
    predictions: [],
  };
}

function contextScenarios() {
  const rows = readCsv('model_architecture_metadata.csv').map(row => ({
    modelName: row.model_name,
    maxPositionEmbeddings: number(row.max_position_embeddings),
    nLayers: number(row.n_layers),
    nHeads: number(row.n_heads),
    dModel: number(row.d_model),
  })).filter(row => row.maxPositionEmbeddings > 0);
  const unique = [...new Set(rows.map(row => row.maxPositionEmbeddings))].sort((a, b) => a - b);
  const selected = [...new Set([unique[0], quantile(unique, 0.5), unique[unique.length - 1]].map(value => Math.round(value)))];
  return selected.map((value, index) => ({
    scenario: ['low', 'medium', 'high'][index] || `level_${index + 1}`,
    contextTokens: value,
    supportingModels: rows.filter(row => row.maxPositionEmbeddings === value).map(row => row.modelName).join(';'),
    source: 'C7 model_architecture_metadata.csv observed max_position_embeddings',
  }));
}

function main() {
  const leaderboard = parseLeaderboard();
  const detailed = aggregateDetailedResults();
  const contribution = analyzeContribution(leaderboard);
  const bridge = analyzeBridge();
  const epochCompute = analyzeEpochCompute();
  const timeseries = analyzeTimeseries();
  const forecast = forecastFrontier(leaderboard);
  const sensitivity = analyzeSensitivity(leaderboard);
  const contexts = contextScenarios();

  writeCsv('c8_bbh_task_aggregation.csv', detailed.aggregates, ['modelDirectory', 'sourceFile', 'bbhTaskCount', 'bbhMacroMean', 'bbhTaskSd', 'bbhTaskMin', 'bbhTaskMax']);
  writeCsv('c8_parse_failures.csv', detailed.failures, ['modelDirectory', 'file', 'reason']);
  writeCsv('context_scenarios.csv', contexts, ['scenario', 'contextTokens', 'supportingModels', 'source']);
  writeCsv('frontier_forecast.csv', [{
    scenario: 'compute_slowdown',
    status: forecast.status,
    predictedScore: null,
    lower95: null,
    upper95: null,
    note: forecast.statusReason,
  }], ['scenario', 'status', 'predictedScore', 'lower95', 'upper95', 'note']);

  const result = {
    definitions: {
      capability: 'Unweighted mean of the six C1/C2 benchmark scores, defined only for complete six-score cases.',
      openFilter: 'Epoch open weights Yes or recognizable Hub license when Epoch status is not No. A license is an availability proxy, not proof of accessible weights.',
      timeAxis: 'Leaderboard submission date; C1/C2 span is reported explicitly.',
      modelTypes: 'pretrained versus non_pretrained from the Type field; non_pretrained includes chat, domain-finetuned, merges and multimodal entries.',
      contribution: 'OLS score ~ log10(parameters in billions) + months since 2024-06 + non-pretrained indicator.',
      forecast: 'Compute-slowdown forecast is withheld because no validated compute-to-parameter-frontier mapping is identified; a conditional time-only association is reported separately.',
    },
    audit: {
      leaderboardUsableOpenRows: leaderboard.length,
      leaderboardEligibleBeforeCompleteCase: parseLeaderboard.audit.eligibleBeforeCompleteCase,
      leaderboardIncompleteSixScoreRowsExcluded: parseLeaderboard.audit.incompleteSixScoreRowsExcluded,
      explicitClosedLicenseConflicts: parseLeaderboard.audit.explicitClosedLicenseConflicts,
      explicitClosedRowsIncluded: leaderboard.filter(row => row.epochOpenStatus === 'no').length,
      leaderboardMinDate: new Date(Math.min(...leaderboard.map(row => row.timestamp))).toISOString().slice(0, 10),
      leaderboardMaxDate: new Date(Math.max(...leaderboard.map(row => row.timestamp))).toISOString().slice(0, 10),
      pretrainedRows: leaderboard.filter(row => row.type === 'pretrained').length,
      nonPretrainedRows: leaderboard.filter(row => row.type === 'non_pretrained').length,
      c8Directories: detailed.directoryCount,
      c8AggregatedDirectories: detailed.aggregates.length,
      c8ParseFailuresEncountered: detailed.failures.length,
    },
    contribution: {
      coefficients: contribution.model.coefficients,
      fitMetrics: contribution.model.metrics,
      startProfile: contribution.startProfile,
      endProfile: contribution.endProfile,
      contributions: contribution.contributions,
    },
    openFilterSensitivity: sensitivity.openFilterSensitivity,
    typeSensitivity: sensitivity.typeSensitivity,
    bridge: {
      highComparability: bridge.highModel,
      comparabilityWeighted: bridge.weightedModel,
      lossOrderedHoldout: bridge.lossHoldout,
      sourceHoldout: bridge.sourceHoldout,
      nHigh: bridge.rows.filter(row => row.comparability === 'high').length,
      nMedium: bridge.rows.filter(row => row.comparability === 'medium').length,
    },
    epochCompute,
    externalTimeseries: timeseries,
    forecast,
    contexts,
    limitations: [
      'C1/C2 cover only 2024-06 to 2025-03; time coefficients are short-window associations, not causal estimates.',
      'Open filtering based on licenses may include licenses with different redistribution or commercial restrictions.',
      'The extended C3 series mixes historical sources and evaluation standards, so it is used only as an external consistency check.',
      'Loss bridge values mix validation sets; medium-comparability rows receive lower weight and mapping uncertainty must propagate downstream.',
      'Parameter count is an imperfect scale proxy for MoE and post-training-heavy models; C4 compute metadata is sparse.',
    ],
  };
  fs.writeFileSync(path.join(outputRoot, 'q4_results.json'), `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify(result, null, 2));
}

main();
