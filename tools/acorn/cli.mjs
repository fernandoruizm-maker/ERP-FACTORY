import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {parse, version} from './acorn/dist/acorn.mjs';
import {importsFromAst} from './analyze.mjs';

try {
  if (version !== '8.19.0' || process.argv.length !== 3) throw new Error();
  const raw = fs.readFileSync(process.argv[2]);
  if (raw.length > 700000) throw new Error();
  const input = JSON.parse(raw);
  if (!input || Object.keys(input).join() !== 'source' || typeof input.source !== 'string' ||
      Buffer.byteLength(input.source) > 100000) throw new Error();
  const tree = parse(input.source, {ecmaVersion: 2025, sourceType: 'module'});
  process.stdout.write(JSON.stringify({parser_version: version,
    source_sha256: createHash('sha256').update(input.source).digest('hex'), imports: importsFromAst(tree)}));
} catch {
  process.stderr.write('DEPENDENCY_ANALYSIS_BLOCKED\n');
  process.exitCode = 1;
}
