import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth'; // Will be mocked
import { useErrorStore } from '@/stores/error'; // Will be mocked
import { useLinkStore }_from_ '../link'; // Path to the store
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

// Sample link data
const sampleLinksData = [
    { id: 1, name: 'Link 1', url: 'http://link1.com' },
    { id: 2, name: 'Link 2', url: 'http://link2.com' },
];
const newLinkData = { name: 'New Link', url: 'http://newlink.com' };
const createdLinkData = { id: 3, ...newLinkData };
const updateData = { name: 'Updated Link Name' };
const updatedLinkData = { id: 1, ...sampleLinksData[0], ...updateData };


describe('Pinia Store: link.js', () => {
    let linkStore;
    let mockAuthStore;
    let mockErrorStore;

    beforeEach(() => {
        setActivePinia(createPinia());
        
        axios.get.mockReset();
        axios.post.mockReset();
        axios.put.mockReset();
        axios.delete.mockReset();

        mockAuthStore = useAuthStore();
        mockErrorStore = useErrorStore();
        
        if (mockAuthStore.isAuthenticated !== undefined) {
            vi.mocked(useAuthStore).mockReturnValue({ isAuthenticated: true });
            mockAuthStore = useAuthStore();
        }
        mockErrorStore.showError.mockReset();
        mockErrorStore.showSuccess.mockReset();

        linkStore = useLinkStore_();
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('1. Initial State & Getters', () => {
        it('initializes state correctly', () => {
            expect(linkStore.links).toEqual([]);
            expect(linkStore.isLoading).toBe(false);
            expect(linkStore.linkLoading).toEqual({});
            expect(linkStore.linkErrors).toEqual({});
        });

        it('linkList getter returns links state', () => {
            linkStore.links = [...sampleLinksData];
            expect(linkStore.linkList).toEqual(sampleLinksData);
        });

        it('loadingStatus getter returns isLoading state', () => {
            linkStore.isLoading = true;
            expect(linkStore.loadingStatus).toBe(true);
        });
    });

    describe('2. fetchLinks Action', () => {
        it('Not Authenticated: calls errorStore.showError, handles isLoading, no API call', async () => {
            vi.mocked(useAuthStore).mockReturnValueOnce({ isAuthenticated: false });
            mockAuthStore = useAuthStore();

            await linkStore.fetchLinks();

            expect(mockErrorStore.showError).toHaveBeenCalledWith("User not authenticated. Please log in.");
            expect(linkStore.isLoading).toBe(false);
            expect(axios.get).not.toHaveBeenCalled();
        });

        it('Authenticated - Success: handles isLoading, calls API, updates links', async () => {
            axios.get.mockResolvedValue({ data: sampleLinksData });
            const params = { filter: 'test' }; // Original param name was 'filter' in prompt
                                            // Store transforms it to 'search'

            const promise = linkStore.fetchLinks(params);
            expect(linkStore.isLoading).toBe(true);
            await promise;

            expect(axios.get).toHaveBeenCalledWith(`${API_BASE_URL}/links/`, { params: { search: 'test' } });
            expect(linkStore.links).toEqual(sampleLinksData);
            expect(linkStore.isLoading).toBe(false);
            expect(mockErrorStore.showError).not.toHaveBeenCalled();
        });

        it('Authenticated - Failure: handles isLoading, calls errorStore.showError, links is empty', async () => {
            const errorDetail = 'API Fetch Error';
            axios.get.mockRejectedValue({ response: { data: { detail: errorDetail } } });
            linkStore.links = [...sampleLinksData]; // Pre-fill

            const promise = linkStore.fetchLinks();
            expect(linkStore.isLoading).toBe(true);
            await promise;

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(linkStore.links).toEqual([]);
            expect(linkStore.isLoading).toBe(false);
        });
    });

    describe('3. addLink Action', () => {
        it('Not Authenticated: calls errorStore.showError, handles linkLoading, returns null', async () => {
            vi.mocked(useAuthStore).mockReturnValueOnce({ isAuthenticated: false });
            mockAuthStore = useAuthStore();
            
            const result = await linkStore.addLink(newLinkData);

            expect(mockErrorStore.showError).toHaveBeenCalledWith("User not authenticated. Please log in.");
            expect(linkStore.linkLoading[0]).toBe(false);
            expect(axios.post).not.toHaveBeenCalled();
            expect(result).toBeNull();
        });

        it('Authenticated - Success: handles linkLoading, calls API, fetches links, shows success, returns data', async () => {
            axios.post.mockResolvedValue({ data: createdLinkData });
            const fetchLinksSpy = vi.spyOn(linkStore, 'fetchLinks').mockResolvedValue();

            const promise = linkStore.addLink(newLinkData);
            expect(linkStore.linkLoading[0]).toBe(true);
            const result = await promise;

            expect(axios.post).toHaveBeenCalledWith(`${API_BASE_URL}/links/`, newLinkData);
            expect(fetchLinksSpy).toHaveBeenCalled();
            expect(mockErrorStore.showSuccess).toHaveBeenCalledWith("Link added successfully!");
            expect(result).toEqual(createdLinkData);
            expect(linkStore.linkErrors[0]).toBeNull();
            expect(linkStore.linkLoading[0]).toBe(false);
        });

        it('Authenticated - Failure: handles linkLoading, calls errorStore.showError, sets linkError, returns null', async () => {
            const errorDetail = 'Add Link Failed';
            axios.post.mockRejectedValue({ response: { data: { detail: errorDetail } } });

            const promise = linkStore.addLink(newLinkData);
            expect(linkStore.linkLoading[0]).toBe(true);
            const result = await promise;

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(linkStore.linkErrors[0]).toBe(errorDetail);
            expect(result).toBeNull();
            expect(linkStore.linkLoading[0]).toBe(false);
        });
    });

    describe('4. updateLink Action', () => {
        const linkIdToUpdate = sampleLinksData[0].id;

        it('Not Authenticated: calls errorStore.showError, handles linkLoading, returns null', async () => {
            vi.mocked(useAuthStore).mockReturnValueOnce({ isAuthenticated: false });
            mockAuthStore = useAuthStore();
            
            const result = await linkStore.updateLink(linkIdToUpdate, updateData);

            expect(mockErrorStore.showError).toHaveBeenCalledWith("User not authenticated. Please log in.");
            expect(linkStore.linkLoading[linkIdToUpdate]).toBe(false);
            expect(axios.put).not.toHaveBeenCalled();
            expect(result).toBeNull();
        });

        it('Authenticated - Success: handles linkLoading, calls API, fetches links, shows success, returns data', async () => {
            axios.put.mockResolvedValue({ data: updatedLinkData });
            const fetchLinksSpy = vi.spyOn(linkStore, 'fetchLinks').mockResolvedValue();

            const promise = linkStore.updateLink(linkIdToUpdate, updateData);
            expect(linkStore.linkLoading[linkIdToUpdate]).toBe(true);
            const result = await promise;

            expect(axios.put).toHaveBeenCalledWith(`${API_BASE_URL}/links/${linkIdToUpdate}`, updateData);
            expect(fetchLinksSpy).toHaveBeenCalled();
            expect(mockErrorStore.showSuccess).toHaveBeenCalledWith("Link updated successfully!");
            expect(result).toEqual(updatedLinkData);
            expect(linkStore.linkErrors[linkIdToUpdate]).toBeNull();
            expect(linkStore.linkLoading[linkIdToUpdate]).toBe(false);
        });

        it('Authenticated - Failure: handles linkLoading, calls errorStore.showError, sets linkError, returns null', async () => {
            const errorDetail = 'Update Link Failed';
            axios.put.mockRejectedValue({ response: { data: { detail: errorDetail } } });

            const promise = linkStore.updateLink(linkIdToUpdate, updateData);
            expect(linkStore.linkLoading[linkIdToUpdate]).toBe(true);
            const result = await promise;

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(linkStore.linkErrors[linkIdToUpdate]).toBe(errorDetail);
            expect(result).toBeNull();
            expect(linkStore.linkLoading[linkIdToUpdate]).toBe(false);
        });
    });

    describe('5. deleteLink Action', () => {
        const linkIdToDelete = sampleLinksData[0].id;

        it('Not Authenticated: calls errorStore.showError, handles linkLoading, returns false', async () => {
            vi.mocked(useAuthStore).mockReturnValueOnce({ isAuthenticated: false });
            mockAuthStore = useAuthStore();
            
            const result = await linkStore.deleteLink(linkIdToDelete);

            expect(mockErrorStore.showError).toHaveBeenCalledWith("User not authenticated. Please log in.");
            expect(linkStore.linkLoading[linkIdToDelete]).toBe(false);
            expect(axios.delete).not.toHaveBeenCalled();
            expect(result).toBe(false);
        });

        it('Authenticated - Success: handles linkLoading, calls API, fetches links, shows success, returns true', async () => {
            axios.delete.mockResolvedValue({});
            const fetchLinksSpy = vi.spyOn(linkStore, 'fetchLinks').mockResolvedValue();

            const promise = linkStore.deleteLink(linkIdToDelete);
            expect(linkStore.linkLoading[linkIdToDelete]).toBe(true);
            const result = await promise;

            expect(axios.delete).toHaveBeenCalledWith(`${API_BASE_URL}/links/${linkIdToDelete}`);
            expect(fetchLinksSpy).toHaveBeenCalled();
            expect(mockErrorStore.showSuccess).toHaveBeenCalledWith("Link deleted successfully!");
            expect(result).toBe(true);
            expect(linkStore.linkErrors[linkIdToDelete]).toBeNull();
            expect(linkStore.linkLoading[linkIdToDelete]).toBe(false);
        });

        it('Authenticated - Failure: handles linkLoading, calls errorStore.showError, sets linkError, returns false', async () => {
            const errorDetail = 'Delete Link Failed';
            axios.delete.mockRejectedValue({ response: { data: { detail: errorDetail } } });

            const promise = linkStore.deleteLink(linkIdToDelete);
            expect(linkStore.linkLoading[linkIdToDelete]).toBe(true);
            const result = await promise;

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(linkStore.linkErrors[linkIdToDelete]).toBe(errorDetail);
            expect(result).toBe(false);
            expect(linkStore.linkLoading[linkIdToDelete]).toBe(false);
        });
    });

    describe('6. triggerLinkTask Action', () => {
        const linkIdToTrigger = sampleLinksData[0].id;

        it('Not Authenticated: calls errorStore.showError, handles linkLoading, returns false', async () => {
            vi.mocked(useAuthStore).mockReturnValueOnce({ isAuthenticated: false });
            mockAuthStore = useAuthStore();
            
            const result = await linkStore.triggerLinkTask(linkIdToTrigger);

            expect(mockErrorStore.showError).toHaveBeenCalledWith("User not authenticated. Please log in.");
            expect(linkStore.linkLoading[linkIdToTrigger]).toBe(false);
            expect(axios.post).not.toHaveBeenCalled();
            expect(result).toBe(false);
        });

        it('Authenticated - Success: handles linkLoading, calls API, shows success, returns true', async () => {
            axios.post.mockResolvedValue({});

            const promise = linkStore.triggerLinkTask(linkIdToTrigger);
            expect(linkStore.linkLoading[linkIdToTrigger]).toBe(true);
            const result = await promise;

            expect(axios.post).toHaveBeenCalledWith(`${API_BASE_URL}/links/${linkIdToTrigger}/trigger`);
            expect(mockErrorStore.showSuccess).toHaveBeenCalledWith(`Task triggered for link ${linkIdToTrigger}!`);
            expect(result).toBe(true);
            expect(linkStore.linkErrors[linkIdToTrigger]).toBeNull();
            expect(linkStore.linkLoading[linkIdToTrigger]).toBe(false);
        });

        it('Authenticated - Failure: handles linkLoading, calls errorStore.showError, sets linkError, returns false', async () => {
            const errorDetail = 'Trigger Task Failed';
            axios.post.mockRejectedValue({ response: { data: { detail: errorDetail } } });

            const promise = linkStore.triggerLinkTask(linkIdToTrigger);
            expect(linkStore.linkLoading[linkIdToTrigger]).toBe(true);
            const result = await promise;

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(linkStore.linkErrors[linkIdToTrigger]).toBe(errorDetail);
            expect(result).toBe(false);
            expect(linkStore.linkLoading[linkIdToTrigger]).toBe(false);
        });
    });
});
