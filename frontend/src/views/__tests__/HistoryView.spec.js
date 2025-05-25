import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick, ref } from 'vue';
import HistoryView from '../HistoryView.vue';
import { ElMessageBox, ElTable, ElAlert, ElInput, ElSelect, ElOption, ElButton, ElTag } from 'element-plus';

// Mock Pinia store: useHistoryStore
import { useHistoryStore } from '@/stores/history';

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
vi.mock('@/stores/history', () => ({
    useHistoryStore: vi.fn(() => ({
        logs: ref([]),
        loadingStatus: ref(false),
        error: ref(null),
        fetchHistory: vi.fn(),
        deleteHistoryLog: vi.fn(),
    }))
}));

// Sample history log data
const sampleHistoryLogs = [
    { id: 1, timestamp: new Date('2023-01-01T10:00:00Z').toISOString(), link_id: 101, status: 'success', downloaded_files: ['fileA.mp4', 'fileB.txt'], error_message: null },
    { id: 2, timestamp: new Date('2023-01-02T11:00:00Z').toISOString(), link_id: 102, status: 'failed', downloaded_files: [], error_message: 'Download timed out' },
    { id: 3, timestamp: new Date('2023-01-03T12:00:00Z').toISOString(), link_id: 101, status: 'success', downloaded_files: ['fileC.jpg'], error_message: null },
];

describe('HistoryView.vue', () => {
    let mockHistoryStore;
    let wrapper;

    beforeEach(async () => {
        mockHistoryStore = useHistoryStore();
        // Reset store state and mocks for each test
        mockHistoryStore.logs.value = [];
        mockHistoryStore.loadingStatus.value = false;
        mockHistoryStore.error.value = null;

        mockHistoryStore.fetchHistory.mockReset().mockResolvedValue();
        mockHistoryStore.deleteHistoryLog.mockReset().mockResolvedValue(true); // Default success

        ElMessageBox.confirm.mockReset();
        ElMessageBox.alert.mockReset();

        wrapper = mount(HistoryView);
        await nextTick(); // For onMounted hook
    });

    afterEach(() => {
        vi.clearAllMocks();
        if (wrapper) {
            wrapper.unmount();
        }
    });

    describe('1. Rendering and Initial Load', () => {
        it('calls historyStore.fetchHistory on mount without arguments', () => {
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledTimes(1);
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledWith(); // No arguments
        });

        it('renders basic elements', () => {
            expect(wrapper.find('h2').text()).toContain('历史记录 / History');
            // Filter inputs
            const inputs = wrapper.findAllComponents(ElInput);
            expect(inputs.some(input => input.attributes('placeholder')?.includes('Filter Link ID'))).toBe(true);
            expect(wrapper.findComponent(ElSelect).attributes('placeholder')).toContain('Filter Status');
            // Buttons
            const buttons = wrapper.findAllComponents(ElButton);
            expect(buttons.some(b => b.text().includes('过滤 / Filter'))).toBe(true);
            expect(buttons.some(b => b.text().includes('刷新 / Refresh'))).toBe(true);
            // Table
            expect(wrapper.findComponent(ElTable).exists()).toBe(true);
        });
    });

    describe('2. Displaying History Logs', () => {
        beforeEach(async () => {
            mockHistoryStore.logs.value = [...sampleHistoryLogs];
            await nextTick();
        });

        it('renders the correct number of rows', () => {
            expect(wrapper.findAllComponents(ElTable).at(0).findAll('tbody tr').length).toBe(sampleHistoryLogs.length);
        });

        it('displays key data points for a sample success row', () => {
            const firstRow = sampleHistoryLogs[0];
            const firstRowTds = wrapper.findAll('tbody tr').at(0).findAll('td');
            
            expect(firstRowTds[0].text()).toBe(String(firstRow.id));
            expect(firstRowTds[1].text()).toBe(new Date(firstRow.timestamp).toLocaleString());
            expect(firstRowTds[2].text()).toBe(String(firstRow.link_id));
            expect(firstRowTds[3].findComponent(ElTag).props().type).toBe('success');
            expect(firstRowTds[3].text()).toBe(firstRow.status);
            
            const fileListItems = firstRowTds[4].findAll('li');
            expect(fileListItems.length).toBe(firstRow.downloaded_files.length);
            expect(fileListItems[0].text()).toBe(firstRow.downloaded_files[0]);
            
            expect(firstRowTds[5].text()).toBe(''); // No error message for success
        });

        it('displays key data points for a sample failed row', () => {
            const secondRow = sampleHistoryLogs[1];
            const secondRowTds = wrapper.findAll('tbody tr').at(1).findAll('td');

            expect(secondRowTds[3].findComponent(ElTag).props().type).toBe('danger');
            expect(secondRowTds[3].text()).toBe(secondRow.status);
            expect(secondRowTds[4].text()).toBe('-'); // No downloaded files
            expect(secondRowTds[5].text()).toBe(secondRow.error_message);
        });
    });
    
    describe('3. Toolbar Functionality', () => {
        it('Refresh Button: clears filters and calls fetchHistory without args', async () => {
            // Simulate input into filter fields
            wrapper.vm.filterLinkID = '123';
            wrapper.vm.filterStatus = 'success';
            await nextTick();

            mockHistoryStore.fetchHistory.mockClear(); // Clear initial onMounted call
            
            const refreshButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('刷新 / Refresh'));
            await refreshButton.trigger('click');
            
            expect(wrapper.vm.filterLinkID).toBe(null);
            expect(wrapper.vm.filterStatus).toBe(null);
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledTimes(1);
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledWith();
        });

        it('Filter Button: with Link ID calls fetchHistory with link_id', async () => {
            const linkId = '101';
            await wrapper.findAllComponents(ElInput).find(i => i.attributes('placeholder')?.includes('Filter Link ID')).setValue(linkId);
            
            mockHistoryStore.fetchHistory.mockClear();
            const filterButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('过滤 / Filter'));
            await filterButton.trigger('click');
            
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledTimes(1);
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledWith({ link_id: linkId });
        });

        it('Filter Button: with Status calls fetchHistory with status', async () => {
            const status = 'failed';
            // ElSelect interaction is more complex; set the ref directly for simplicity
            wrapper.vm.filterStatus = status;
            await nextTick();

            mockHistoryStore.fetchHistory.mockClear();
            const filterButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('过滤 / Filter'));
            await filterButton.trigger('click');
            
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledTimes(1);
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledWith({ status: status });
        });

        it('Filter Button: with both Link ID and Status calls fetchHistory with both params', async () => {
            const linkId = '102';
            const status = 'success';
            await wrapper.findAllComponents(ElInput).find(i => i.attributes('placeholder')?.includes('Filter Link ID')).setValue(linkId);
            wrapper.vm.filterStatus = status;
            await nextTick();

            mockHistoryStore.fetchHistory.mockClear();
            const filterButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('过滤 / Filter'));
            await filterButton.trigger('click');
            
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledTimes(1);
            expect(mockHistoryStore.fetchHistory).toHaveBeenCalledWith({ link_id: linkId, status: status });
        });
    });

    describe('4. Delete Action in Table Row', () => {
        beforeEach(async () => {
            mockHistoryStore.logs.value = [...sampleHistoryLogs];
            await nextTick();
        });

        it('calls deleteHistoryLog on confirmation and shows success alert', async () => {
            ElMessageBox.confirm.mockResolvedValueOnce(); // Simulate user confirms
            mockHistoryStore.deleteHistoryLog.mockResolvedValueOnce(true); // Simulate successful deletion

            const logToDelete = sampleHistoryLogs[0];
            const deleteButton = wrapper.findAll('tbody tr').at(0).findAllComponents(ElButton).find(b => b.text().includes('删除 / Delete'));
            await deleteButton.trigger('click');
            await nextTick(); // For ElMessageBox and async calls in handleDelete

            expect(ElMessageBox.confirm).toHaveBeenCalledTimes(1);
            expect(mockHistoryStore.deleteHistoryLog).toHaveBeenCalledTimes(1);
            expect(mockHistoryStore.deleteHistoryLog).toHaveBeenCalledWith(logToDelete.id);
            expect(ElMessageBox.alert).toHaveBeenCalledWith('历史记录已删除 / History log deleted.', 'Success', { type: 'success' });
        });

        it('does NOT call deleteHistoryLog on cancellation', async () => {
            ElMessageBox.confirm.mockRejectedValueOnce(new Error('cancel')); // Simulate user cancels

            const deleteButton = wrapper.findAll('tbody tr').at(0).findAllComponents(ElButton).find(b => b.text().includes('删除 / Delete'));
            await deleteButton.trigger('click');
            await nextTick();

            expect(ElMessageBox.confirm).toHaveBeenCalledTimes(1);
            expect(mockHistoryStore.deleteHistoryLog).not.toHaveBeenCalled();
        });

        it('shows error alert if deleteHistoryLog returns false', async () => {
            ElMessageBox.confirm.mockResolvedValueOnce(); // User confirms
            const errorMessage = "Failed to delete from server";
            mockHistoryStore.deleteHistoryLog.mockImplementationOnce(async () => {
                mockHistoryStore.error.value = errorMessage; // Simulate store setting an error
                return false; // Simulate failure
            });

            const logToDelete = sampleHistoryLogs[0];
            const deleteButton = wrapper.findAll('tbody tr').at(0).findAllComponents(ElButton).find(b => b.text().includes('删除 / Delete'));
            await deleteButton.trigger('click');
            await nextTick();

            expect(mockHistoryStore.deleteHistoryLog).toHaveBeenCalledWith(logToDelete.id);
            expect(ElMessageBox.alert).toHaveBeenCalledWith(
                expect.stringContaining(`删除历史记录失败: ${errorMessage}`),
                'Error',
                { type: 'error' }
            );
        });
    });
    
    describe('5. Loading State', () => {
        it('shows table loading when historyStore.loadingStatus is true', async () => {
            mockHistoryStore.loadingStatus.value = true;
            await nextTick();
            expect(wrapper.findComponent(ElTable).props().vloading).toBe(true);
        });
    });

    describe('6. Error Display', () => {
        it('shows global error alert when historyStore.error is set', async () => {
            const globalErrorMsg = 'Failed to fetch history data.';
            mockHistoryStore.error.value = globalErrorMsg;
            await nextTick();
            
            const alert = wrapper.findComponent(ElAlert);
            expect(alert.exists()).toBe(true);
            expect(alert.props().title).toBe(globalErrorMsg);
        });
    });
});
