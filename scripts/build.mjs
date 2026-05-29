import { mkdir, readFile, writeFile } from 'node:fs/promises';

const sourcePath = new URL('../src/index.js', import.meta.url);
const distDir = new URL('../dist/', import.meta.url);
const distFile = new URL('../dist/index.js', import.meta.url);
const metadataFile = new URL('../dist/build-info.json', import.meta.url);

await mkdir(distDir, { recursive: true });

const source = await readFile(sourcePath, 'utf8');
const banner = '// Archivo generado por el pipeline reusable\n';

await writeFile(distFile, `${banner}${source}`, 'utf8');
await writeFile(
  metadataFile,
  JSON.stringify(
    {
      generatedAt: new Date().toISOString(),
      files: ['index.js']
    },
    null,
    2
  ),
  'utf8'
);

console.log('Build completado en dist/.');