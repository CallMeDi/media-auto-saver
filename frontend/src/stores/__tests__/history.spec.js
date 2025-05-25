import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth'; // Will be mocked
import { useErrorStore } from '@/stores/error'; // Will be mocked
import { useHistoryStore }_from_ '../history'; // Path to the store
import { API_BASE_URL } from '@/utils/constants';

// Mocks
vi.mock('axios');

vi.mock('@/stores/auth', () => ({
    useAuthStore: vi.fn(() => ({ 
        isAuthenticated: true // Default to authenticated for most tests
    }))
}));

vi.mock('@/stores/error', () => ({
    useErrorStore: vi.fn(() => ({
        showError: vi.fn(),
        showSuccess: vi.fn()
    }))
}));

// Sample history data
const sampleLogs = [
    { id: 1, link_id: 101, data: 'Log 1' },
    { id: 2, link_id: 102, data: 'Log 2' },
    { id: 3, link_id: 101, data: 'Log 3 for link 101' }
];


describe('Pinia Store: history.js', () => {
    let historyStore;
    let mockAuthStore;
    let mockErrorStore;

    beforeEach(() => {
        setActivePinia(createPinia());
        
        // Reset axios mocks
        axios.get.mockReset();
        axios.delete.mockReset();

        // Get fresh mock instances for dependent stores
        mockAuthStore = useAuthStore();
        mockErrorStore = useErrorStore();
        
        // Reset dependent store mocks
        if (mockAuthStore.isAuthenticated !== undefined) { // Re-config if it's a direct value
            vi.mocked(useAuthStore).mockReturnValue({ isAuthenticated: true });
            mockAuthStore = useAuthStore(); // re-assign
        }
        mockErrorStore.showError.mockReset();
        mockErrorStore.showSuccess.mockReset();

        // Get a fresh history store instance
        historyStore = useHistoryStore_();
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('1. Initial State & Getters', () => {
        it('initializes historyLogs as an empty array', () => {
            expect(historyStore.historyLogs).toEqual([]);
        });

        it('initializes isLoading as false', () => {
            expect(historyStore.isLoading).toBe(false);
        });

        it('logs getter returns historyLogs state', () => {
            const testLogs = [{ id: 1, data: 'test' }];
            historyStore.historyLogs = testLogs;
            expect(historyStore.logs).toEqual(testLogs);
        });

        it('loadingStatus getter returns isLoading state', () => {
            historyStore.isLoading = true;
            expect(historyStore.loadingStatus).toBe(true);
        });
    });

    describe('2. fetchHistory Action', () => {
        it('Not Authenticated: calls errorStore.showError and does not call axios.get', async () => {
            vi.mocked(useAuthStore).mockReturnValueOnce({ isAuthenticated: false });
            mockAuthStore = useAuthStore(); // re-assign to get the new mocked value

            await historyStore.fetchHistory();

            expect(mockErrorStore.showError).toHaveBeenCalledWith("User not authenticated. Please log in.");
            expect(historyStore.isLoading).toBe(false); // Should be reset
            expect(axios.get).not.toHaveBeenCalled();
        });

        it('Authenticated - Success: fetches and updates historyLogs, handles loading state', async () => {
            axios.get.mockResolvedValue({ data: sampleLogs });
            const params = { link_id: 123 };

            const fetchPromise = historyStore.fetchHistory(params);
            
            expect(historyStore.isLoading).toBe(true);
            await fetchPromise;

            expect(axios.get).toHaveBeenCalledTimes(1);
            expect(axios.get).toHaveBeenCalledWith(`${API_BASE_URL}/history/`, { params });
            expect(historyStore.historyLogs).toEqual(sampleLogs);
            expect(historyStore.isLoading).toBe(false);
            expect(mockErrorStore.showError).not.toHaveBeenCalled();
        });

        it('Authenticated - Failure: calls errorStore.showError and clears logs, handles loading state', async () => {
            const errorDetail = 'Failed to fetch';
            axios.get.mockRejectedValue({ response: { data: { detail: errorDetail } } });
            historyStore.historyLogs = [...sampleLogs]; // Pre-fill to check if it's cleared

            const fetchPromise = historyStore.fetchHistory();
            
            expect(historyStore.isLoading).toBe(true);
            await fetchPromise;

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(historyStore.historyLogs).toEqual([]);
            expect(historyStore.isLoading).toBe(false);
        });
    });

    describe('3. deleteHistoryLog Action', () => {
        const logIdToDelete = sampleLogs[0].id;

        it('Not Authenticated: calls errorStore.showError and returns false', async () => {
            vi.mocked(useAuthStore).mockReturnValueOnce({ isAuthenticated: false });
            mockAuthStore = useAuthStore();

            const result = await historyStore.deleteHistoryLog(logIdToDelete);

            expect(mockErrorStore.showError).toHaveBeenCalledWith("User not authenticated. Please log in.");
            expect(historyStore.isLoading).toBe(false);
            expect(axios.delete).not.toHaveBeenCalled();
            expect(result).toBe(false);
        });

        it('Authenticated - Success: deletes log, updates state, shows success, returns true', async () => {
            historyStore.historyLogs = [...sampleLogs];
            axios.delete.mockResolvedValue({});

            const deletePromise = historyStore.deleteHistoryLog(logIdToDelete);

            expect(historyStore.isLoading).toBe(true);
            const result = await deletePromise;

            expect(axios.delete).toHaveBeenCalledWith(`${API_BASE_URL}/history/${logIdToDelete}`);
            expect(historyStore.historyLogs.find(log => log.id === logIdToDelete)).toBeUndefined();
            expect(historyStore.historyLogs.length).toBe(sampleLogs.length - 1);
            expect(mockErrorStore.showSuccess).toHaveBeenCalledWith("History log deleted successfully!");
            expect(historyStore.isLoading).toBe(false);
            expect(result).toBe(true);
        });

        it('Authenticated - Failure: calls errorStore.showError, returns false', async () => {
            const errorDetail = "Deletion failed";
            axios.delete.mockRejectedValue({ response: { data: { detail: errorDetail } } });

            const deletePromise = historyStore.deleteHistoryLog(logIdToDelete);
            
            expect(historyStore.isLoading).toBe(true);
            const result = await deletePromise;

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(historyStore.isLoading).toBe(false);
            expect(result).toBe(false);
        });
    });

    describe('4. deleteHistoryByLink Action', () => {
        const linkIdToDeleteFor = 101;

        it('Not Authenticated: calls errorStore.showError and returns false', async () => {
            vi.mocked(useAuthStore).mockReturnValueOnce({ isAuthenticated: false });
            mockAuthStore = useAuthStore();

            const result = await historyStore.deleteHistoryByLink(linkIdToDeleteFor);

            expect(mockErrorStore.showError).toHaveBeenCalledWith("User not authenticated. Please log in.");
            expect(historyStore.isLoading).toBe(false);
            expect(axios.delete).not.toHaveBeenCalled();
            expect(result).toBe(false);
        });

        it('Authenticated - Success: calls delete, fetches history, shows success, returns true', async () => {
            axios.delete.mockResolvedValue({});
            const fetchHistorySpy = vi.spyOn(historyStore, 'fetchHistory').mockResolvedValue();

            const deletePromise = historyStore.deleteHistoryByLink(linkIdToDeleteFor);

            expect(historyStore.isLoading).toBe(true);
            const result = await deletePromise;

            expect(axios.delete).toHaveBeenCalledWith(`${API_BASE_URL}/history/by_link/${linkIdToDeleteFor}`);
            expect(fetchHistorySpy).toHaveBeenCalled();
            expect(mockErrorStore.showSuccess).toHaveBeenCalledWith("History for link deleted successfully!");
            expect(historyStore.isLoading).toBe(false);
            expect(result).toBe(true);
        });

        it('Authenticated - Failure: calls errorStore.showError, returns false', async () => {
            const errorDetail = "Bulk deletion failed";
            axios.delete.mockRejectedValue({ response: { data: { detail: errorDetail } } });
            const fetchHistorySpy = vi.spyOn(historyStore, 'fetchHistory');


            const deletePromise = historyStore.deleteHistoryByLink(linkIdToDeleteFor);
            
            expect(historyStore.isLoading).toBe(true);
            const result = await deletePromise;

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(fetchHistorySpy).not.toHaveBeenCalled(); // Should not fetch if delete fails
            expect(historyStore.isLoading).toBe(false);
            expect(result).toBe(false);
        });
    });
});
