import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import ProviderFormModal from '@/components/ProviderFormModal.vue';
import type { Provider } from '@/types/providers';

const factory = (props?: Partial<InstanceType<typeof ProviderFormModal>['$props']>) =>
  mount(ProviderFormModal, {
    props: {
      visible: true,
      mode: 'create',
      provider: null,
      ...props,
    },
  });

describe('ProviderFormModal', () => {
  it('emits submit with sanitized values when the form is valid', async () => {
    const wrapper = factory();

    await wrapper.get('input[name="name"]').setValue(' Example Provider ');
    await wrapper.get('input[name="baseUrl"]').setValue('https://api.example.com/v1');
    await wrapper.get('input[name="model-0"]').setValue(' gpt-4 ');
    await wrapper.get('button[data-test="add-model"]').trigger('click');

    const modelInputs = wrapper.findAll('input[type="text"]').filter((input) => input.attributes('name')?.startsWith('model-'));
    await modelInputs[1].setValue(' text-bison-2 ');

    await wrapper.get('input[name="apiKey"]').setValue(' sk-secret ');

    await wrapper.find('form').trigger('submit');
    await flushPromises();

    const emitted = wrapper.emitted('submit');
    expect(emitted).toBeTruthy();
    const payload = emitted?.[0]?.[0];
    expect(payload).toMatchObject({
      name: 'Example Provider',
      baseUrl: 'https://api.example.com/v1',
      models: ['gpt-4', 'text-bison-2'],
      apiKey: 'sk-secret',
      isActive: true,
    });
  });

  it('surfaces validation errors when required fields are missing', async () => {
    const wrapper = factory();

    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(wrapper.text()).toContain('Provider name is required');
    expect(wrapper.text()).toContain('A valid URL is required');
    expect(wrapper.text()).toContain('Specify at least one model identifier');
    expect(wrapper.text()).toContain('API key is required');
    expect(wrapper.emitted('submit')).toBeFalsy();
  });

  it('prefills values when editing an existing provider', async () => {
    const provider: Provider = {
      id: 1,
      name: 'Acme AI',
      baseUrl: 'https://acme.ai',
      models: ['acme-pro'],
      isActive: false,
      status: 'online',
      latencyMs: 120,
      lastTestedAt: '2024-05-01T00:00:00.000Z',
      createdAt: '2024-04-01T00:00:00.000Z',
      updatedAt: '2024-04-10T00:00:00.000Z',
    };

    const wrapper = factory({ mode: 'edit', provider });
    await flushPromises();

    expect(wrapper.get('input[name="name"]').element.value).toBe('Acme AI');
    expect(wrapper.get('input[name="baseUrl"]').element.value).toBe('https://acme.ai');
    expect(wrapper.get('input[name="model-0"]').element.value).toBe('acme-pro');
    expect(wrapper.get('input[name="isActive"]').element.checked).toBe(false);
  });
});
