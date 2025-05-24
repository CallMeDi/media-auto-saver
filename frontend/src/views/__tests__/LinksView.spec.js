import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick, ref, reactive } from 'vue';
import LinksView from '../LinksView.vue';
import LinkDialog from '@/components/LinkDialog.vue'; // Import for finding component
import { ElMessageBox, ElTable, ElAlert, ElSwitch, ElButton, ElInput, ElText } from 'element-plus';

// Mock Pinia store: useLinkStore
import { useLinkStore } from '@/stores/link';

// Mock Element Plus components and services
vi.mock('element-plus', async (importOriginal) => {
    const original = await importOriginal();
    return {
        ...original,
        ElMessageBox: {
            confirm: vi.fn(),
            alert: vi.fn(),
        },
    };
});

// Mock the store before any tests run
vi.mock('@/stores/link', () => ({
    useLinkStore: vi.fn(() => ({
        linkList: ref([]),
        isLoading: ref(false),
        error: ref(null),
        linkLoading: reactive({}), // For individual link loading
        linkErrors: reactive({}),  // For individual link errors
        fetchLinks: vi.fn(),
        updateLink: vi.fn(),
        deleteLink: vi.fn(),
        triggerLinkTask: vi.fn(),
        // addLink is not directly called by LinksView, but by LinkDialog
    }))
}));

// Sample link data
const sampleLinks = [
    { id: 1, name: 'Link 1', url: 'http://link1.com', status: 'idle', link_type: 'creator', site_name: 'SiteA', tags: 'tag1', is_enabled: true, last_checked_at: new Date().toISOString(), last_success_at: null, created_at: new Date().toISOString() },
    { id: 2, name: 'Link 2', url: 'http://link2.live', status: 'monitoring', link_type: 'live', site_name: 'SiteB', tags: 'tag2,tag3', is_enabled: false, last_checked_at: null, last_success_at: new Date().toISOString(), created_at: new Date().toISOString() },
];

describe('LinksView.vue', () => {
    let mockLinkStore;
    let wrapper;

    beforeEach(async () => {
        mockLinkStore = useLinkStore();
        // Reset store state and mocks for each test
        mockLinkStore.linkList.value = [];
        mockLinkStore.isLoading.value = false;
        mockLinkStore.error.value = null;
        for (const key in mockLinkStore.linkLoading) delete mockLinkStore.linkLoading[key];
        for (const key in mockLinkStore.linkErrors) delete mockLinkStore.linkErrors[key];

        mockLinkStore.fetchLinks.mockReset().mockResolvedValue();
        mockLinkStore.updateLink.mockReset().mockResolvedValue({ success: true }); // Default success
        mockLinkStore.deleteLink.mockReset().mockResolvedValue(true); // Default success
        mockLinkStore.triggerLinkTask.mockReset().mockResolvedValue();

        ElMessageBox.confirm.mockReset();
        ElMessageBox.alert.mockReset();

        wrapper = mount(LinksView, {
            global: {
                // stubs: { LinkDialog: true } // Shallow stub if not testing its events directly
            }
        });
        // onMounted calls fetchLinks, so wait for it if it's async
        await nextTick(); // For onMounted hook
    });

    afterEach(() => {
        vi.clearAllMocks();
        if (wrapper) {
            wrapper.unmount();
        }
    });

    describe('1. Rendering and Initial Load', () => {
        it('calls linkStore.fetchLinks on mount', () => {
            expect(mockLinkStore.fetchLinks).toHaveBeenCalledTimes(1);
        });

        it('renders basic elements', () => {
            expect(wrapper.find('h2').text()).toContain('链接管理 / Link Management');
            expect(wrapper.findComponent(ElButton).text()).toContain('添加链接 / Add Link');
            expect(wrapper.findAllComponents(ElButton).some(b => b.text().includes('刷新 / Refresh'))).toBe(true);
            expect(wrapper.findComponent(ElInput).attributes('placeholder')).toContain('过滤链接');
            expect(wrapper.findComponent(ElTable).exists()).toBe(true);
        });
    });

    describe('2. Displaying Links in Table', () => {
        beforeEach(async () => {
            mockLinkStore.linkList.value = [...sampleLinks];
            await nextTick();
        });

        it('renders the correct number of rows', () => {
            expect(wrapper.findAllComponents(ElTable).at(0).findAll('tbody tr').length).toBe(sampleLinks.length);
        });

        it('displays key data points for a sample row', () => {
            const firstRowColumns = wrapper.findAll('tbody tr').at(0).findAll('td');
            // This mapping depends on the ElTableColumn order in the template
            expect(firstRowColumns[1].text()).toBe(sampleLinks[0].name); // Name
            expect(firstRowColumns[2].find('a').attributes('href')).toBe(sampleLinks[0].url); // URL
            expect(firstRowColumns[2].text()).toBe(sampleLinks[0].url);
            expect(firstRowColumns[3].text()).toContain(sampleLinks[0].link_type); // Type
            expect(firstRowColumns[5].text()).toContain(sampleLinks[0].status); // Status

            const switchComponent = wrapper.findAllComponents(ElSwitch).at(0);
            expect(switchComponent.props().modelValue).toBe(sampleLinks[0].is_enabled);
        });
    });

    describe('3. Toolbar Functionality', () => {
        it('Refresh Button: calls fetchLinks', async () => {
            mockLinkStore.fetchLinks.mockClear(); // Clear initial onMounted call
            const refreshButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('刷新 / Refresh'));
            await refreshButton.trigger('click');
            expect(mockLinkStore.fetchLinks).toHaveBeenCalledTimes(1);
        });

        it('Filter: calls fetchLinks with search payload', async () => {
            const filterText = 'TestFilter';
            await wrapper.findComponent(ElInput).setValue(filterText);
            
            mockLinkStore.fetchLinks.mockClear();
            const filterButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('过滤 / Filter'));
            await filterButton.trigger('click');
            
            expect(mockLinkStore.fetchLinks).toHaveBeenCalledTimes(1);
            expect(mockLinkStore.fetchLinks).toHaveBeenCalledWith({ search: filterText });
        });

        it('Add Link Button: opens LinkDialog in add mode', async () => {
            const addLinkButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('添加链接 / Add Link'));
            await addLinkButton.trigger('click');
            await nextTick();

            expect(wrapper.vm.showDialog).toBe(true);
            expect(wrapper.vm.editingLink).toBe(null);
            expect(wrapper.findComponent(LinkDialog).props().modelValue).toBe(true);
            expect(wrapper.findComponent(LinkDialog).props().linkData).toBe(null);
        });
    });

    describe('4. Link Row Actions', () => {
        beforeEach(async () => {
            mockLinkStore.linkList.value = [...sampleLinks];
            await nextTick();
        });

        it('Toggle Enable/Disable: calls updateLink', async () => {
            const linkToToggle = sampleLinks[0]; // is_enabled: true
            const switchComponent = wrapper.findAllComponents(ElSwitch).at(0);

            // Simulate the change event from ElSwitch by directly setting the new value and emitting 'change'
            // ElSwitch internally handles the modelValue update and emits change.
            // For testing, we can simulate the new value it would pass.
            await switchComponent.vm.$emit('change', !linkToToggle.is_enabled); // ElSwitch emits new value on change
            
            expect(mockLinkStore.updateLink).toHaveBeenCalledTimes(1);
            expect(mockLinkStore.updateLink).toHaveBeenCalledWith(linkToToggle.id, { is_enabled: !linkToToggle.is_enabled });
        });
        
        it('Toggle Enable/Disable: shows ElMessageBox.alert on updateLink failure', async () => {
            const linkToToggle = sampleLinks[0];
            const switchComponent = wrapper.findAllComponents(ElSwitch).at(0);
            const errorMessage = "Failed to update";
            
            mockLinkStore.updateLink.mockImplementationOnce(async () => {
                mockLinkStore.error.value = errorMessage; // Simulate error being set in store
                return { success: false }; // Or however failure is indicated by the store action
            });
            mockLinkStore.fetchLinks.mockClear(); // To check if refreshLinks is called

            await switchComponent.vm.$emit('change', !linkToToggle.is_enabled);
            await nextTick(); // Wait for async operations in toggleEnable

            expect(ElMessageBox.alert).toHaveBeenCalledWith(
                expect.stringContaining(`Failed to update status for link ${linkToToggle.id}: ${errorMessage}`),
                'Error',
                { type: 'error' }
            );
            expect(mockLinkStore.fetchLinks).toHaveBeenCalled(); // refreshLinks called on error
        });

        it('Edit Link: opens LinkDialog with correct link data', async () => {
            const linkToEdit = sampleLinks[1];
            const editButton = wrapper.findAll('tbody tr').at(1).findAllComponents(ElButton).find(b => b.text().includes('编辑 / Edit'));
            await editButton.trigger('click');
            await nextTick();

            expect(wrapper.vm.showDialog).toBe(true);
            expect(wrapper.vm.editingLink).toEqual({ ...linkToEdit }); // Check data passed to dialog
            expect(wrapper.findComponent(LinkDialog).props().modelValue).toBe(true);
            expect(wrapper.findComponent(LinkDialog).props().linkData).toEqual({ ...linkToEdit });
        });

        it('Manual Trigger: calls triggerLinkTask', async () => {
            const linkToTrigger = sampleLinks[0];
            const triggerButton = wrapper.findAll('tbody tr').at(0).findAllComponents(ElButton).find(b => b.text().includes('手动触发 / Manual Trigger'));
            await triggerButton.trigger('click');
            
            expect(mockLinkStore.triggerLinkTask).toHaveBeenCalledTimes(1);
            expect(mockLinkStore.triggerLinkTask).toHaveBeenCalledWith(linkToTrigger.id);
        });

        it('Delete Link: calls deleteLink on confirmation', async () => {
            ElMessageBox.confirm.mockResolvedValueOnce(); // Simulate user confirms
            mockLinkStore.deleteLink.mockResolvedValueOnce(true); // Simulate successful deletion

            const linkToDelete = sampleLinks[0];
            const deleteButton = wrapper.findAll('tbody tr').at(0).findAllComponents(ElButton).find(b => b.text().includes('删除 / Delete'));
            await deleteButton.trigger('click');
            await nextTick(); // For ElMessageBox and async calls in handleDelete

            expect(ElMessageBox.confirm).toHaveBeenCalledTimes(1);
            expect(mockLinkStore.deleteLink).toHaveBeenCalledTimes(1);
            expect(mockLinkStore.deleteLink).toHaveBeenCalledWith(linkToDelete.id);
            expect(ElMessageBox.alert).toHaveBeenCalledWith('链接已删除 / Link deleted.', 'Success', { type: 'success' });
        });

        it('Delete Link: does NOT call deleteLink on cancellation', async () => {
            ElMessageBox.confirm.mockRejectedValueOnce(new Error('cancel')); // Simulate user cancels

            const deleteButton = wrapper.findAll('tbody tr').at(0).findAllComponents(ElButton).find(b => b.text().includes('删除 / Delete'));
            await deleteButton.trigger('click');
            await nextTick();

            expect(ElMessageBox.confirm).toHaveBeenCalledTimes(1);
            expect(mockLinkStore.deleteLink).not.toHaveBeenCalled();
        });
    });
    
    describe('5. LinkDialog Interaction', () => {
        it('calls fetchLinks when LinkDialog emits "submitted"', async () => {
            // Open the dialog first (e.g., by clicking "Add Link")
            const addLinkButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('添加链接 / Add Link'));
            await addLinkButton.trigger('click');
            await nextTick();
            
            mockLinkStore.fetchLinks.mockClear(); // Clear initial and any other calls

            const linkDialog = wrapper.findComponent(LinkDialog);
            linkDialog.vm.$emit('submitted'); // Simulate event from dialog
            
            expect(mockLinkStore.fetchLinks).toHaveBeenCalledTimes(1);
        });
    });

    describe('6. Loading States', () => {
        it('shows table loading when linkStore.isLoading is true', async () => {
            mockLinkStore.isLoading.value = true;
            await nextTick();
            expect(wrapper.findComponent(ElTable).props().vloading).toBe(true); // Check v-loading prop
        });

        it('shows button loading for a specific link', async () => {
            const linkIdToLoad = sampleLinks[0].id;
            mockLinkStore.linkList.value = [...sampleLinks]; // Ensure links are in table
            mockLinkStore.linkLoading[linkIdToLoad] = true;
            await nextTick();

            const firstRowButtons = wrapper.findAll('tbody tr').at(0).findAllComponents(ElButton);
            firstRowButtons.forEach(button => {
                // Assuming all action buttons on the row should show loading
                expect(button.props().loading).toBe(true);
            });
        });
    });

    describe('7. Error Display', () => {
        it('shows global error alert when linkStore.error is set', async () => {
            const globalErrorMsg = 'Global network failure';
            mockLinkStore.error.value = globalErrorMsg;
            await nextTick();
            
            const alert = wrapper.findComponent(ElAlert);
            expect(alert.exists()).toBe(true);
            expect(alert.props().title).toBe(globalErrorMsg);
        });

        it('shows specific link error text', async () => {
            const linkWithError = sampleLinks[0];
            const specificErrorMsg = 'This link is broken';
            mockLinkStore.linkList.value = [...sampleLinks];
            mockLinkStore.linkErrors[linkWithError.id] = specificErrorMsg;
            await nextTick();

            const firstRow = wrapper.findAll('tbody tr').at(0);
            const errorText = firstRow.findComponent(ElText); // Assuming ElText is used for error
            expect(errorText.exists()).toBe(true);
            expect(errorText.text()).toBe(specificErrorMsg);
        });
    });
});
