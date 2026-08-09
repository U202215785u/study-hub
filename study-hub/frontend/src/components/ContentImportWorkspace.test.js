import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { describe, expect, it } from 'vitest'
import ContentImportWorkspace from './ContentImportWorkspace.vue'

describe('ContentImportWorkspace', () => {
  it('shows the failure code and reason for a failed parser task', () => {
    const wrapper = mount(ContentImportWorkspace, {
      props: {
        parser: {
          batch: ref(null),
          tasks: ref([{
            task_id: 'failed-parser-task',
            title: 'Example article',
            status: 'error',
            progress_text: 'Failed',
            error_code: 'PARSER-2001',
            error: 'Claude request timed out after 480 seconds',
          }]),
          preflight: async () => ({}),
          confirm: async () => ({}),
        },
      },
    })

    expect(wrapper.text()).toContain('PARSER-2001')
    expect(wrapper.text()).toContain('Claude request timed out after 480 seconds')
  })
})
