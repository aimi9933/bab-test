import { describe, expect, it } from 'vitest';
import { normalizeModels } from '@/composables/useProviders';

describe('normalizeModels', () => {
  it('trims whitespace and removes empty entries', () => {
    const models = [' gpt-4 ', '', 'text-bison', '   '];
    expect(normalizeModels(models)).toEqual(['gpt-4', 'text-bison']);
  });

  it('returns an empty array when no models are provided', () => {
    const models: string[] = [];
    expect(normalizeModels(models)).toEqual([]);
  });
});
