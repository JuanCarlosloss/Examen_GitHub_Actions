import { mkdir, writeFile, readdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';

const reportsDir = new URL('../reports/', import.meta.url);
const reportFile = new URL('../reports/test-report.tap', import.meta.url);

await mkdir(reportsDir, { recursive: true });

// Buscar dinámicamente archivos de test para evitar problemas con globs en Windows
const testDir = new URL('../test/', import.meta.url);
const files = await readdir(testDir);
const testFiles = files
  .filter(file => file.endsWith('.test.js'))
  .map(file => `test/${file}`);

const child = spawn(process.execPath, ['--test', '--test-reporter', 'tap', ...testFiles], {
  cwd: new URL('..', import.meta.url),
  shell: true,
  stdio: ['ignore', 'pipe', 'pipe']
});

let report = '';

child.stdout.on('data', (chunk) => {
  const text = chunk.toString();
  report += text;
  process.stdout.write(text);
});

child.stderr.on('data', (chunk) => {
  const text = chunk.toString();
  report += text;
  process.stderr.write(text);
});

const exitCode = await new Promise((resolve) => {
  child.on('close', resolve);
});

await writeFile(reportFile, report, 'utf8');

if (exitCode !== 0) {
  process.exit(exitCode ?? 1);
}