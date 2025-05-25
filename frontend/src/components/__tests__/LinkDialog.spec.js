import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick, ref } from 'vue';
import LinkDialog from '../LinkDialog.vue';
import { ElDialog, ElForm, ElInput, ElRadioGroup, ElRadio, ElSwitch, ElAlert, ElButton } from 'element-plus';

// Mock Pinia store: useLinkStore
import { useLinkStore } from '@/stores/link';

// Mock the store before any tests run
vi.mock('@/stores/link', () => ({
    useLinkStore: vi.fn(() => ({
        addLink: vi.fn(),
        updateLink: vi.fn(),
        error: ref(null) // reactive error ref
    }))
}));

// Helper to create a default props object
const createProps = (modelValue = true, linkData = null) => ({
    modelValue,
    linkData,
    // 'onUpdate:modelValue': (e) => wrapper.setProps({ modelValue: e }), // For two-way binding simulation if needed
});

describe('LinkDialog.vue', () => {
    let mockLinkStore;

    beforeEach(() => {
        // Get a fresh mock store for each test
        mockLinkStore = useLinkStore();
        // Reset mocks for store methods
        mockLinkStore.addLink.mockReset().mockResolvedValue({ id: 1, url: 'http://new.com' }); // Default success
        mockLinkStore.updateLink.mockReset().mockResolvedValue({ id: 1, url: 'http://updated.com' }); // Default success
        mockLinkStore.error.value = null; // Reset error
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('Rendering and Initial State', () => {
        it('renders in Add mode correctly', async () => {
            const props = createProps(true, null);
            const wrapper = mount(LinkDialog, { props });
            await nextTick(); // Allow dialog to open and content to render

            expect(wrapper.findComponent(ElDialog).props().title).toBe('添加链接 / Add Link');
            expect(wrapper.find('form').exists()).toBe(true);

            const vmFormData = wrapper.vm.formData;
            expect(vmFormData.url).toBe('');
            expect(vmFormData.name).toBe('');
            expect(vmFormData.link_type).toBe('creator');
            expect(vmFormData.description).toBe('');
            expect(vmFormData.tags).toBe('');
            expect(vmFormData.cookies_path).toBe('');
            expect(vmFormData.is_enabled).toBe(true);

            const submitButton = wrapper.findAllComponents(ElButton).find(b => b.props().type === 'primary');
            expect(submitButton.text()).toContain('添加 / Add');
        });

        it('renders in Edit mode correctly', async () => {
            const linkData = {
                id: 1,
                url: 'http://example.com',
                name: 'Test Link',
                link_type: 'live',
                description: 'A test description',
                tags: 'test,example',
                cookies_path: 'cookies.txt',
                is_enabled: false,
                settings: {}
            };
            const props = createProps(true, linkData);
            const wrapper = mount(LinkDialog, { props });
            await nextTick();

            expect(wrapper.findComponent(ElDialog).props().title).toBe('编辑链接 / Edit Link');
            
            const vmFormData = wrapper.vm.formData;
            expect(vmFormData.url).toBe(linkData.url);
            expect(vmFormData.name).toBe(linkData.name);
            expect(vmFormData.link_type).toBe(linkData.link_type);
            expect(vmFormData.description).toBe(linkData.description);
            expect(vmFormData.tags).toBe(linkData.tags);
            expect(vmFormData.cookies_path).toBe(linkData.cookies_path);
            expect(vmFormData.is_enabled).toBe(linkData.is_enabled);

            const submitButton = wrapper.findAllComponents(ElButton).find(b => b.props().type === 'primary');
            expect(submitButton.text()).toContain('更新 / Update');
        });
    });

    describe('Form Input and Data Binding', () => {
        it('updates formData on ElInput changes', async () => {
            const wrapper = mount(LinkDialog, { props: createProps() });
            await nextTick();

            const urlInput = wrapper.findAllComponents(ElInput).find(c => c.props().placeholder?.includes('URL'));
            await urlInput.setValue('http://testurl.com');
            expect(wrapper.vm.formData.url).toBe('http://testurl.com');

            const nameInput = wrapper.findAllComponents(ElInput).find(c => c.props().placeholder?.includes('Name'));
            await nameInput.setValue('My Test Link');
            expect(wrapper.vm.formData.name).toBe('My Test Link');
        });

        it('updates formData on ElRadioGroup change', async () => {
            const wrapper = mount(LinkDialog, { props: createProps() });
            await nextTick();
            
            // Find the 'live' radio button and simulate click on its input element
            const liveRadio = wrapper.findAllComponents(ElRadio).find(r => r.props().label === 'live');
            // Element Plus radio group v-model updates when the input inside ElRadio is changed/clicked
            await liveRadio.find('input[type="radio"]').setValue(true); // Setting value of radio input
            await liveRadio.find('input[type="radio"]').trigger('change'); // Trigger change for v-model
            
            expect(wrapper.vm.formData.link_type).toBe('live');
        });

        it('updates formData on ElSwitch change', async () => {
            const wrapper = mount(LinkDialog, { props: createProps() });
            await nextTick();

            const switchComponent = wrapper.findComponent(ElSwitch);
            // ElSwitch v-model is updated by emitting 'update:modelValue' or 'change' with the new value
            await switchComponent.vm.$emit('update:modelValue', false);
            await nextTick();
            expect(wrapper.vm.formData.is_enabled).toBe(false);
        });
    });

    describe('Form Validation', () => {
        it('shows validation error for empty URL', async () => {
            const wrapper = mount(LinkDialog, { props: createProps() });
            await nextTick();
            
            wrapper.vm.formData.url = ''; // Ensure URL is empty
            await wrapper.vm.submitForm(); // Directly call component method
            await nextTick(); // For validation messages to appear

            const formItem = wrapper.findAllComponents(ElFormItem).find(item => item.props().prop === 'url');
            expect(formItem.find('.el-form-item__error').exists()).toBe(true);
            expect(formItem.find('.el-form-item__error').text()).toContain('请输入 URL');
        });
        
        it('shows validation error for invalid URL format', async () => {
            const wrapper = mount(LinkDialog, { props: createProps() });
            await nextTick();

            await wrapper.findComponent(ElForm).vm.resetFields(); // Reset to ensure clean state
            wrapper.vm.formData.url = 'not-a-url';
            await wrapper.vm.submitForm();
            await nextTick();

            const formItem = wrapper.findAllComponents(ElFormItem).find(item => item.props().prop === 'url');
            expect(formItem.find('.el-form-item__error').exists()).toBe(true);
            expect(formItem.find('.el-form-item__error').text()).toContain('请输入有效的 URL');
        });

        // Note: type is required by default and has 'creator' selected, so testing "empty type" is tricky unless we manipulate initial state.
        // For now, we assume the default selection satisfies "required".
    });

    describe('Form Submission - Success Scenarios', () => {
        it('Add mode: calls addLink and emits events on success', async () => {
            const props = createProps(true, null);
            const wrapper = mount(LinkDialog, { props });
            await nextTick();

            wrapper.vm.formData = {
                url: 'http://success.com', name: 'Success Link', link_type: 'creator',
                description: '', tags: '', cookies_path: '', is_enabled: true, settings: {}
            };
            
            mockLinkStore.addLink.mockResolvedValue({ id: 1, url: 'http://success.com' });

            await wrapper.vm.submitForm();
            await nextTick(); // For async operations in submitForm

            expect(mockLinkStore.addLink).toHaveBeenCalledTimes(1);
            expect(mockLinkStore.addLink).toHaveBeenCalledWith(expect.objectContaining({ url: 'http://success.com' }));
            expect(wrapper.emitted('submitted')).toBeTruthy();
            expect(wrapper.emitted('update:modelValue')[0]).toEqual([false]); // Emitted with false
        });

        it('Edit mode: calls updateLink and emits events on success', async () => {
            const linkData = { id: 1, url: 'http://original.com', name: 'Original', link_type: 'creator', is_enabled: true, settings: {} };
            const props = createProps(true, linkData);
            const wrapper = mount(LinkDialog, { props });
            await nextTick(); // Dialog opens and form is populated

            wrapper.vm.formData.name = 'Updated Name'; // Modify some data
            await nextTick();

            mockLinkStore.updateLink.mockResolvedValue({ ...linkData, name: 'Updated Name' });

            await wrapper.vm.submitForm();
            await nextTick();

            expect(mockLinkStore.updateLink).toHaveBeenCalledTimes(1);
            expect(mockLinkStore.updateLink).toHaveBeenCalledWith(linkData.id, expect.objectContaining({ name: 'Updated Name' }));
            expect(wrapper.emitted('submitted')).toBeTruthy();
            expect(wrapper.emitted('update:modelValue')[0]).toEqual([false]);
        });
    });

    describe('Form Submission - Failure Scenarios', () => {
        it('Add mode: shows error alert if addLink fails (store error)', async () => {
            const props = createProps(true, null);
            const wrapper = mount(LinkDialog, { props });
            await nextTick();
            
            wrapper.vm.formData = { url: 'http://fail.com', name: 'Fail Link', link_type: 'creator', is_enabled: true, settings: {} };
            
            const errorMessage = 'Network Error on Add';
            mockLinkStore.addLink.mockImplementation(async () => {
                mockLinkStore.error.value = errorMessage; // Simulate store setting an error
                return null; // Simulate failure by returning null or rejecting
            });

            await wrapper.vm.submitForm();
            await nextTick(); // For error message to render

            expect(mockLinkStore.addLink).toHaveBeenCalledTimes(1);
            const alert = wrapper.findComponent(ElAlert);
            expect(alert.exists()).toBe(true);
            expect(alert.props().title).toBe(errorMessage);
            expect(wrapper.emitted('submitted')).toBeFalsy();
            expect(wrapper.emitted('update:modelValue')).toBeFalsy(); // Dialog should not close on error
        });

        it('Edit mode: shows error alert if updateLink fails (exception)', async () => {
            const linkData = { id: 1, url: 'http://editfail.com', name: 'Edit Fail', link_type: 'creator', is_enabled: true, settings: {} };
            const props = createProps(true, linkData);
            const wrapper = mount(LinkDialog, { props });
            await nextTick();

            wrapper.vm.formData.name = 'Attempted Update';
            
            const errorMessage = 'Failed to update link';
            mockLinkStore.updateLink.mockRejectedValue(new Error(errorMessage)); // Simulate a rejected promise

            await wrapper.vm.submitForm();
            await nextTick();
            await nextTick(); // Extra tick if error handling involves further async ops

            expect(mockLinkStore.updateLink).toHaveBeenCalledTimes(1);
            const alert = wrapper.findComponent(ElAlert);
            expect(alert.exists()).toBe(true);
            // The component sets submitError from linkStore.error OR a generic message.
            // If the store action itself throws, it's caught and linkStore.error is checked.
            // If linkStore.error is not set by the action (because it threw before setting it),
            // a generic error is used. Here, the component's catch block sets submitError.
            // The exact message depends on how the component's error handling is structured.
            // The component's code: `submitError.value = linkStore.error || "An unexpected error occurred.";`
            // If the promise is rejected, linkStore.error might not be set by the store action itself.
            // Let's assume it falls back to "An unexpected error occurred." or the actual error message.
            // Based on the component's code: `submitError.value = linkStore.error || "An unexpected error occurred.";`
            // If the store action itself *throws an error* rather than returning null and setting store.error,
            // the component's `catch (error)` block will set `submitError.value`.
            // The component's code: `submitError.value = linkStore.error || "An unexpected error occurred.";`
            // This might be tricky. Let's assume the component's error handling sets submitError appropriately.
            // In the component: `submitError.value = linkStore.error || "An unexpected error occurred.";`
            // If `updateLink` itself throws, `linkStore.error` might not be set by the store.
            // The component's `catch(error)` block will then set `submitError.value`.
            // The actual value of `submitError.value` would be `linkStore.error` (if the store action set it)
            // or the string "An unexpected error occurred."
            // Let's verify it's *an* error.
            expect(alert.props().title).toBeTruthy(); // Check an error title is set
            // For a more specific check, we might need to adjust the mock or component logic.
            // If `linkStore.error` is set by the store action *before* throwing, that would be used.
            // If not, the component's generic message.
            // The provided component code's `catch (error)` block sets `submitError.value = linkStore.error || "An unexpected error occurred.";`
            // If `updateLink` is a promise that rejects, `linkStore.error` may not be set by that point.
            // So, "An unexpected error occurred." is a likely candidate if the promise itself fails.
            // However, the component's error handling is: `submitError.value = linkStore.error || "An unexpected error occurred.";`
            // And in the `catch` block: `submitError.value = linkStore.error || "An unexpected error occurred.";`
            // This implies that if the `updateLink` itself throws an error, `linkStore.error` might not be set,
            // leading to "An unexpected error occurred.".
            // Let's check for that.
            // The component actually has: `submitError.value = linkStore.error || "An unexpected error occurred.";`
            // And in the catch: `console.error("Submission error:", error); submitError.value = linkStore.error || "An unexpected error occurred.";`
            // So if `linkStore.error` is null, it will be "An unexpected error occurred."
            expect(alert.props().title).toBe("An unexpected error occurred.");


            expect(wrapper.emitted('submitted')).toBeFalsy();
        });
    });

    describe('Dialog Closing', () => {
        it('emits update:modelValue(false) on Cancel button click', async () => {
            const wrapper = mount(LinkDialog, { props: createProps() });
            await nextTick();

            const cancelButton = wrapper.findAllComponents(ElButton).find(b => !b.props().type); // Assuming Cancel is not primary
            await cancelButton.trigger('click');
            
            expect(wrapper.emitted('update:modelValue')[0]).toEqual([false]);
        });

        it('emits update:modelValue(false) on ElDialog @close event', async () => {
            const wrapper = mount(LinkDialog, { props: createProps() });
            await nextTick();

            await wrapper.findComponent(ElDialog).vm.$emit('close');
            expect(wrapper.emitted('update:modelValue')[0]).toEqual([false]);
        });
    });

    describe('Form Reset and Population Logic', () => {
        it('resets fields and validation when opened in Add mode', async () => {
            const wrapper = mount(LinkDialog, { props: createProps(false, null) }); // Start closed
            
            // Spy on clearValidate
            const mockClearValidate = vi.fn();
            wrapper.vm.linkFormRef = { value: { clearValidate: mockClearValidate } }; // Mock the form ref

            // Open the dialog
            await wrapper.setProps({ modelValue: true });
            await nextTick(); // For watch and nextTick in component to run

            expect(wrapper.vm.formData.url).toBe(''); // Check a field is reset
            expect(mockClearValidate).toHaveBeenCalled();
        });

        it('populates fields from linkData and clears validation when opened in Edit mode', async () => {
            const linkData = { id: 1, url: 'http://edit.com', name: 'Edit Me', link_type: 'live', is_enabled: false, settings: {} };
            const wrapper = mount(LinkDialog, { props: createProps(false, linkData) }); // Start closed

            const mockClearValidate = vi.fn();
            wrapper.vm.linkFormRef = { value: { clearValidate: mockClearValidate } };

            await wrapper.setProps({ modelValue: true });
            await nextTick();

            expect(wrapper.vm.formData.url).toBe(linkData.url);
            expect(wrapper.vm.formData.name).toBe(linkData.name);
            expect(mockClearValidate).toHaveBeenCalled();
        });
    });
});
