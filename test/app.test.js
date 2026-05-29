import test from 'node:test';
import assert from 'node:assert/strict';

import { greetPipeline } from '../src/index.js';

test('greetPipeline devuelve un mensaje estable', () => {
  assert.equal(greetPipeline('Node.js'), 'Pipeline lista para Node.js');
});