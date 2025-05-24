import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick, ref } from 'vue';
import LoginView from '../LoginView.vue';
import { ElCard, ElForm, ElFormItem, ElInput, ElButton, ElLink } from 'element-plus';

// Mock Pinia store: useAuthStore
import { useAuthStore } from '@/stores/auth';
// Mock Vue Router: useRouter
import { useRouter } from 'vue-router';
// Mock Error Store (though not directly interacted with for assertions in this component)
import { useErrorStore } from '@/stores/error';

// Mock the stores and router
vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    login: vi.fn(),
    // Add other properties if needed, e.g., error or loading states from store
  }))
}));

vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn()
  }))
}));

vi.mock('@/stores/error', () => ({
    useErrorStore: vi.fn(() => ({
        // Mock any methods if they were to be called, e.g., clearError
        // clearError: vi.fn() 
    }))
}));


describe('LoginView.vue', () => {
    let mockAuthStore;
    let mockRouter;
    let mockErrorStore; // Not used for assertions but good to have if component logic changes
    let wrapper;

    beforeEach(async () => {
        // Get fresh mock instances for each test
        mockAuthStore = useAuthStore();
        mockRouter = useRouter();
        mockErrorStore = useErrorStore();

        // Reset mocks for store methods and router push
        mockAuthStore.login.mockReset().mockResolvedValue(undefined); // Default success (no specific return needed)
        mockRouter.push.mockReset();
        
        wrapper = mount(LoginView, {
            global: {
                stubs: { // Stubbing heavy components if they don't affect logic much
                    // ElCard: true, // Example, but better to let them render for layout checks
                }
            }
        });
        await nextTick(); // Wait for initial render
    });

    afterEach(() => {
        vi.clearAllMocks();
        if (wrapper) {
            wrapper.unmount();
        }
    });

    describe('Rendering', () => {
        it('renders all main elements', () => {
            // Title (within ElCard header)
            expect(wrapper.findComponent(ElCard).find('.card-header span').text()).toBe('登录 / Login');
            
            // Username input
            const formItems = wrapper.findAllComponents(ElFormItem);
            const usernameItem = formItems.find(item => item.props().label?.includes('Username'));
            expect(usernameItem.exists()).toBe(true);
            expect(usernameItem.findComponent(ElInput).exists()).toBe(true);

            // Password input
            const passwordItem = formItems.find(item => item.props().label?.includes('Password'));
            expect(passwordItem.exists()).toBe(true);
            const passwordInput = passwordItem.findComponent(ElInput);
            expect(passwordInput.exists()).toBe(true);
            expect(passwordInput.props().type).toBe('password');

            // Login button
            const loginButton = wrapper.findComponent(ElButton);
            expect(loginButton.exists()).toBe(true);
            expect(loginButton.props().type).toBe('primary');
            expect(loginButton.text()).toContain('登录 / Login');

            // Forgot Password link
            const forgotPasswordLink = wrapper.findComponent(ElLink);
            expect(forgotPasswordLink.exists()).toBe(true);
            expect(forgotPasswordLink.text()).toBe('忘记密码? / Forgot Password?');
        });
    });

    describe('Form Input', () => {
        it('updates username ref on input', async () => {
            const usernameInput = wrapper.findAllComponents(ElInput).find(input => input.props().placeholder?.includes('username'));
            await usernameInput.setValue('testuser123');
            expect(wrapper.vm.username).toBe('testuser123');
        });

        it('updates password ref on input', async () => {
            const passwordInput = wrapper.findAllComponents(ElInput).find(input => input.props().placeholder?.includes('password'));
            await passwordInput.setValue('securePass!');
            expect(wrapper.vm.password).toBe('securePass!');
        });
    });

    describe('Login Submission (Success)', () => {
        it('calls authStore.login with correct credentials and handles loading state', async () => {
            mockAuthStore.login.mockResolvedValueOnce(); // Simulate successful login

            const username = 'testuser';
            const password = 'password123';
            
            await wrapper.vm.username.value = username; // Set internal refs directly or via input.setValue
            await wrapper.vm.password.value = password;
            await nextTick();

            const loginButton = wrapper.findComponent(ElButton);
            expect(loginButton.props().loading).toBe(false); // Initial state

            // Trigger form submission
            // Directly calling handleLogin as form submission via .trigger('submit') on ElForm might be complex
            // or use wrapper.find('form').trigger('submit') if native-type="submit" works as expected with ElForm
            const loginPromise = wrapper.vm.handleLogin(); // Call the method
            
            await nextTick(); // Allow loading state to update
            expect(loginButton.props().loading).toBe(true); // Check loading state during submission
            expect(loginButton.text()).toContain('登录中... / Logging in...');

            await loginPromise; // Wait for login to resolve
            await nextTick(); // For loading state to revert

            expect(mockAuthStore.login).toHaveBeenCalledTimes(1);
            expect(mockAuthStore.login).toHaveBeenCalledWith(username, password);
            
            expect(loginButton.props().loading).toBe(false); // Check loading state after submission
            expect(loginButton.text()).toContain('登录 / Login');
        });
    });

    describe('Login Submission (Failure)', () => {
        it('calls authStore.login and handles loading state on failure', async () => {
            const loginError = new Error('Invalid credentials');
            mockAuthStore.login.mockRejectedValueOnce(loginError); // Simulate failed login

            const username = 'wronguser';
            const password = 'wrongpassword';

            await wrapper.vm.username.value = username;
            await wrapper.vm.password.value = password;
            await nextTick();

            const loginButton = wrapper.findComponent(ElButton);
            
            const loginPromise = wrapper.vm.handleLogin();
            
            await nextTick();
            expect(loginButton.props().loading).toBe(true);
            expect(loginButton.text()).toContain('登录中... / Logging in...');

            // Wait for the promise to settle (reject in this case)
            try {
                await loginPromise;
            } catch (e) {
                // Expected rejection, or handle if component catches it
            }
            await nextTick(); // For loading state to revert

            expect(mockAuthStore.login).toHaveBeenCalledTimes(1);
            expect(mockAuthStore.login).toHaveBeenCalledWith(username, password);
            
            expect(loginButton.props().loading).toBe(false);
            expect(loginButton.text()).toContain('登录 / Login');
            // No specific error display is asserted here as per component's current structure
        });
    });

    describe('"Forgot Password?" Link Navigation', () => {
        it('calls router.push with "/password-reset-request" on link click', async () => {
            const forgotPasswordLink = wrapper.findComponent(ElLink);
            await forgotPasswordLink.trigger('click');

            expect(mockRouter.push).toHaveBeenCalledTimes(1);
            expect(mockRouter.push).toHaveBeenCalledWith('/password-reset-request');
        });
    });
});
