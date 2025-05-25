import { describe, it, expect, vi, beforeEach, afterEach, beforeEachProviders } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import axios from 'axios';
import router from '@/router'; // Will be mocked
import { useErrorStore } from '@/stores/error'; // Will be mocked
import { useAuthStore }_from_ '../auth'; // Path to the store

// Mocks
vi.mock('axios');
vi.mock('@/router', () => ({
    default: { // Assuming router is exported as default
        push: vi.fn()
    }
}));
vi.mock('@/stores/error', () => ({
    useErrorStore: vi.fn(() => ({
        showError: vi.fn()
    }))
}));

// Helper for localStorage mocking
const localStorageMock = (() => {
    let store = {};
    return {
        getItem: vi.fn((key) => store[key] || null),
        setItem: vi.fn((key, value) => { store[key] = value.toString(); }),
        removeItem: vi.fn((key) => { delete store[key]; }),
        clear: () => { store = {}; }
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock
});


describe('Pinia Store: auth.js', () => {
    let authStore;
    let mockErrorStore;

    beforeEach(() => {
        setActivePinia(createPinia());
        localStorageMock.clear(); // Clear localStorage mock for each test
        
        // Reset axios mocks and default headers
        axios.post.mockReset();
        axios.get.mockReset();
        delete axios.defaults.headers.common['Authorization'];

        // Get a fresh store instance
        authStore = useAuthStore_(); // useAuthStore_ to avoid conflict with describe block
        mockErrorStore = useErrorStore(); // Get the mocked error store instance
        
        // Reset router push mock
        if (router.push.mockReset) { // router.push might be undefined if router itself is fully mocked
             router.push.mockReset();
        } else {
            // If router is just an object with a push mock:
            router.push = vi.fn();
        }
        
        // Reset error store mock if necessary
        mockErrorStore.showError.mockReset();

    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('1. Initial State and Getters', () => {
        it('initializes token from localStorage if present', () => {
            localStorageMock.getItem.mockReturnValueOnce('test-token-from-storage');
            // Re-initialize store to pick up mocked localStorage value during construction
            const newAuthStore = useAuthStore_();
            expect(localStorageMock.getItem).toHaveBeenCalledWith('token');
            expect(newAuthStore.token).toBe('test-token-from-storage');
        });

        it('initializes token as null if not in localStorage', () => {
            localStorageMock.getItem.mockReturnValueOnce(null);
            const newAuthStore = useAuthStore_();
            expect(newAuthStore.token).toBe(null);
        });

        it('isAuthenticated getter returns true when token exists', () => {
            authStore.token = 'some-token';
            expect(authStore.isAuthenticated).toBe(true);
        });

        it('isAuthenticated getter returns false when token is null', () => {
            authStore.token = null;
            expect(authStore.isAuthenticated).toBe(false);
        });

        it('currentUser getter returns the user state', () => {
            const user = { id: 1, username: 'test' };
            authStore.user = user;
            expect(authStore.currentUser).toEqual(user);
        });
    });

    describe('2. setToken Action', () => {
        it('sets token, localStorage, and axios header with a new token', () => {
            const newToken = 'new-auth-token';
            authStore.setToken(newToken);
            expect(authStore.token).toBe(newToken);
            expect(localStorageMock.setItem).toHaveBeenCalledWith('token', newToken);
            expect(axios.defaults.headers.common['Authorization']).toBe(`Bearer ${newToken}`);
        });

        it('clears token, localStorage, and axios header when token is null', () => {
            // First set a token to ensure it's cleared
            authStore.setToken('initial-token');
            
            authStore.setToken(null);
            expect(authStore.token).toBe(null);
            expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
            expect(axios.defaults.headers.common['Authorization']).toBeUndefined();
        });
    });

    describe('3. setUser Action', () => {
        it('updates user state', () => {
            const newUser = { id: 2, username: 'anotheruser' };
            authStore.setUser(newUser);
            expect(authStore.user).toEqual(newUser);
        });
    });

    describe('4. login Action', () => {
        it('Success: sets token, fetches user, and navigates to home', async () => {
            const loginData = { access_token: 'login-access-token' };
            axios.post.mockResolvedValue({ data: loginData });
            
            // Mock fetchUser to avoid its internal axios call for this specific test
            const fetchUserSpy = vi.spyOn(authStore, 'fetchUser').mockResolvedValue();
            const setTokenSpy = vi.spyOn(authStore, 'setToken');

            await authStore.login('testuser', 'password');

            expect(axios.post).toHaveBeenCalledWith(
                expect.stringContaining('/login/access-token'),
                expect.any(URLSearchParams), // Check that URLSearchParams is used
                expect.objectContaining({ headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
            );
            expect(setTokenSpy).toHaveBeenCalledWith(loginData.access_token);
            expect(fetchUserSpy).toHaveBeenCalled();
            expect(router.push).toHaveBeenCalledWith('/');
            expect(mockErrorStore.showError).not.toHaveBeenCalled();
        });

        it('Failure: calls errorStore.showError and clears token/user', async () => {
            const errorDetail = 'Invalid credentials';
            axios.post.mockRejectedValue({ response: { data: { detail: errorDetail } } });
            
            const setTokenSpy = vi.spyOn(authStore, 'setToken');
            const setUserSpy = vi.spyOn(authStore, 'setUser');

            await authStore.login('testuser', 'wrongpassword');

            expect(mockErrorStore.showError).toHaveBeenCalledWith(errorDetail);
            expect(setTokenSpy).toHaveBeenCalledWith(null);
            expect(setUserSpy).toHaveBeenCalledWith(null);
            expect(router.push).not.toHaveBeenCalled();
        });
    });

    describe('5. fetchUser Action', () => {
        it('With token - Success: fetches and sets user', async () => {
            authStore.token = 'valid-token'; // Set token first
            const userData = { id: 1, username: 'fetchedUser' };
            axios.get.mockResolvedValue({ data: userData });
            const setUserSpy = vi.spyOn(authStore, 'setUser');

            await authStore.fetchUser();

            expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('/users/me'));
            expect(setUserSpy).toHaveBeenCalledWith(userData);
            expect(mockErrorStore.showError).not.toHaveBeenCalled();
        });

        it('With token - Failure: calls errorStore.showError and logs out', async () => {
            authStore.token = 'expired-token';
            const errorMsg = 'Token has expired';
            axios.get.mockRejectedValue({ response: { data: { detail: errorMsg } } });
            const logoutSpy = vi.spyOn(authStore, 'logout').mockImplementation(() => {}); // Mock logout to prevent router push conflicts

            await authStore.fetchUser();

            expect(mockErrorStore.showError).toHaveBeenCalledWith('Failed to fetch user information. Please log in again.');
            expect(logoutSpy).toHaveBeenCalled();
        });

        it('Without token: does not make API call', async () => {
            authStore.token = null;
            await authStore.fetchUser();
            expect(axios.get).not.toHaveBeenCalled();
        });
    });
    
    describe('6. logout Action', () => {
        it('clears token, user, and navigates to login', () => {
            // Set initial state as if user was logged in
            authStore.token = 'some-token';
            authStore.user = { id: 1, name: 'test' };
            axios.defaults.headers.common['Authorization'] = `Bearer some-token`;
            localStorageMock.setItem('token', 'some-token');

            const setTokenSpy = vi.spyOn(authStore, 'setToken');
            const setUserSpy = vi.spyOn(authStore, 'setUser');

            authStore.logout();

            expect(setTokenSpy).toHaveBeenCalledWith(null); // setToken internally handles localStorage and axios headers
            expect(setUserSpy).toHaveBeenCalledWith(null);
            expect(router.push).toHaveBeenCalledWith('/login');
        });
    });

    describe('7. checkAuth Action', () => {
        it('With token: sets axios header and fetches user', async () => {
            authStore.token = 'persistent-token'; // Simulate token being present from localStorage initially
            const fetchUserSpy = vi.spyOn(authStore, 'fetchUser').mockResolvedValue();

            await authStore.checkAuth();

            expect(axios.defaults.headers.common['Authorization']).toBe(`Bearer persistent-token`);
            expect(fetchUserSpy).toHaveBeenCalled();
        });

        it('Without token: does not fetch user', async () => {
            authStore.token = null;
            const fetchUserSpy = vi.spyOn(authStore, 'fetchUser');

            await authStore.checkAuth();

            expect(fetchUserSpy).not.toHaveBeenCalled();
        });
    });
});
