import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick, ref } from 'vue';
import PasswordResetView from '../PasswordResetView.vue';
import { ElCard, ElForm, ElFormItem, ElInput, ElButton, ElAlert, ElLink, ElMessage } from 'element-plus';
import axios from 'axios';

// Mock Vue Router: useRoute and useRouter
import { useRoute, useRouter } from 'vue-router';

// Mock axios
vi.mock('axios');

// Mock vue-router
vi.mock('vue-router', async (importOriginal) => {
    const originalRouter = await importOriginal(); // Import original to keep other exports
    return {
        ...originalRouter,
        useRoute: vi.fn(),
        useRouter: vi.fn(() => ({ push: vi.fn() })),
    };
});

// Mock Element Plus ElMessage
vi.mock('element-plus', async (importOriginal) => {
    const original = await importOriginal();
    return {
        ...original,
        ElMessage: {
            success: vi.fn(),
            error: vi.fn(), // In case error messages are also shown via ElMessage
        },
    };
});


describe('PasswordResetView.vue', () => {
    let mockRouterPush;
    let wrapper;

    const mockUseRoute = useRoute; // Get the vi.fn() instance from the mock
    const mockUseRouter = useRouter; // Get the vi.fn() instance from the mock
    

    beforeEach(async () => {
        // Reset mocks for each test
        axios.post.mockReset();
        ElMessage.success.mockReset();
        ElMessage.error.mockReset();

        mockRouterPush = vi.fn();
        mockUseRouter.mockReturnValue({ push: mockRouterPush }); // Ensure router mock is fresh

        // Default route mock (can be overridden in specific tests)
        mockUseRoute.mockReturnValue({ query: { token: 'defaulttoken123' } });
        
        wrapper = mount(PasswordResetView);
        await nextTick(); // Wait for initial render
    });

    afterEach(() => {
        vi.clearAllMocks();
        if (wrapper) {
            wrapper.unmount();
        }
    });

    describe('1. Rendering', () => {
        it('renders all main elements', () => {
            expect(wrapper.findComponent(ElCard).find('.card-header span').text()).toBe('重置密码 / Reset Password');
            
            const formItems = wrapper.findAllComponents(ElFormItem);
            const newPasswordItem = formItems.find(item => item.props().label?.includes('New Password'));
            expect(newPasswordItem.exists()).toBe(true);
            expect(newPasswordItem.findComponent(ElInput).exists()).toBe(true);
            expect(newPasswordItem.findComponent(ElInput).props().type).toBe('password');

            const confirmPasswordItem = formItems.find(item => item.props().label?.includes('Confirm New Password'));
            expect(confirmPasswordItem.exists()).toBe(true);
            expect(confirmPasswordItem.findComponent(ElInput).exists()).toBe(true);
            expect(confirmPasswordItem.findComponent(ElInput).props().type).toBe('password');

            const resetButton = wrapper.findComponent(ElButton);
            expect(resetButton.exists()).toBe(true);
            expect(resetButton.props().type).toBe('primary');
            expect(resetButton.text()).toContain('重置密码 / Reset Password');

            const backToLoginLink = wrapper.findComponent(ElLink);
            expect(backToLoginLink.exists()).toBe(true);
            expect(backToLoginLink.text()).toBe('返回登录 / Back to Login');
        });
    });

    describe('2. Form Input', () => {
        it('updates newPassword ref on input', async () => {
            const newPasswordInput = wrapper.findAllComponents(ElInput).find(input => input.props().placeholder?.includes('Enter new password'));
            await newPasswordInput.setValue('newPass123');
            expect(wrapper.vm.newPassword).toBe('newPass123');
        });

        it('updates confirmPassword ref on input', async () => {
            const confirmPasswordInput = wrapper.findAllComponents(ElInput).find(input => input.props().placeholder?.includes('Enter new password again'));
            await confirmPasswordInput.setValue('newPass123');
            expect(wrapper.vm.confirmPassword).toBe('newPass123');
        });
    });

    describe('3. Client-Side Validation (Passwords Mismatch)', () => {
        it('shows local error alert if passwords do not match and does not call API', async () => {
            wrapper.vm.newPassword = 'passwordA';
            wrapper.vm.confirmPassword = 'passwordB';
            await nextTick();

            await wrapper.vm.handleResetPassword(); // Call method directly
            await nextTick(); // For error message to appear

            const errorAlert = wrapper.findAllComponents(ElAlert).find(alert => alert.props().type === 'error');
            expect(errorAlert.exists()).toBe(true);
            expect(errorAlert.props().title).toBe('两次输入的密码不一致 / Passwords do not match');
            expect(axios.post).not.toHaveBeenCalled();
        });
    });

    describe('4. Token Handling (Missing Token)', () => {
        it('shows local error if token is missing and does not call API', async () => {
            mockUseRoute.mockReturnValue({ query: {} }); // No token in route query
            
            // Re-mount or trigger a lifecycle update if component relies on route in setup/onMounted for token
            // For this component, token is read inside handleResetPassword, so direct call is fine.
            wrapper.vm.newPassword = 'validPass';
            wrapper.vm.confirmPassword = 'validPass';
            await nextTick();

            await wrapper.vm.handleResetPassword();
            await nextTick();

            const errorAlert = wrapper.findAllComponents(ElAlert).find(alert => alert.props().type === 'error');
            expect(errorAlert.exists()).toBe(true);
            expect(errorAlert.props().title).toBe('缺少密码重置令牌 / Missing password reset token');
            expect(axios.post).not.toHaveBeenCalled();
        });
    });

    describe('5. Password Reset Submission - Success', () => {
        it('calls API, handles loading, shows success message, and navigates to login', async () => {
            const token = 'testtoken123';
            mockUseRoute.mockReturnValue({ query: { token } });
            axios.post.mockResolvedValue({ data: { message: 'Password updated successfully' } });

            wrapper.vm.newPassword = 'successPass';
            wrapper.vm.confirmPassword = 'successPass';
            await nextTick();

            const resetButton = wrapper.findComponent(ElButton);
            expect(resetButton.props().loading).toBe(false);

            const resetPromise = wrapper.vm.handleResetPassword();
            await nextTick();
            expect(resetButton.props().loading).toBe(true);
            expect(resetButton.text()).toContain('重置中... / Resetting...');

            await resetPromise;
            await nextTick();

            expect(axios.post).toHaveBeenCalledTimes(1);
            expect(axios.post).toHaveBeenCalledWith(
                '/api/v1/reset-password/',
                { token: token, new_password: 'successPass' }
            );

            expect(resetButton.props().loading).toBe(false);
            expect(resetButton.text()).toContain('重置密码 / Reset Password');
            
            // Check ElMessage.success
            expect(ElMessage.success).toHaveBeenCalledTimes(1);
            expect(ElMessage.success).toHaveBeenCalledWith('Password updated successfully');

            // Check local message for ElAlert (if still used after ElMessage)
            const successAlert = wrapper.findAllComponents(ElAlert).find(alert => alert.props().type === 'success');
            expect(successAlert.exists()).toBe(true);
            expect(successAlert.props().title).toBe('Password updated successfully');
            
            // Check navigation
            expect(mockRouterPush).toHaveBeenCalledTimes(1);
            expect(mockRouterPush).toHaveBeenCalledWith('/login');
        });
    });

    describe('6. Password Reset Submission - Failure (API Error)', () => {
        it('calls API, handles loading, and shows local error alert from API response', async () => {
            const token = 'invalidtoken456';
            mockUseRoute.mockReturnValue({ query: { token } });
            const apiErrorDetail = 'Token invalid or expired';
            axios.post.mockRejectedValue({ response: { data: { detail: apiErrorDetail } } });

            wrapper.vm.newPassword = 'failPass';
            wrapper.vm.confirmPassword = 'failPass';
            await nextTick();

            const resetButton = wrapper.findComponent(ElButton);
            
            const resetPromise = wrapper.vm.handleResetPassword();
            await nextTick();
            expect(resetButton.props().loading).toBe(true);

            // Wait for promise to settle (reject)
            try { await resetPromise; } catch (e) {}
            await nextTick();

            expect(axios.post).toHaveBeenCalledTimes(1);
            expect(axios.post).toHaveBeenCalledWith(
                '/api/v1/reset-password/',
                { token: token, new_password: 'failPass' }
            );

            expect(resetButton.props().loading).toBe(false);
            
            const errorAlert = wrapper.findAllComponents(ElAlert).find(alert => alert.props().type === 'error');
            expect(errorAlert.exists()).toBe(true);
            expect(errorAlert.props().title).toBe(apiErrorDetail);
            
            expect(mockRouterPush).not.toHaveBeenCalled();
            expect(ElMessage.success).not.toHaveBeenCalled(); // No success message
        });
    });
    
    describe('7. "Back to Login" Link Navigation', () => {
        it('calls router.push with "/login" on link click', async () => {
            const backToLoginLink = wrapper.findComponent(ElLink);
            await backToLoginLink.trigger('click');

            expect(mockRouterPush).toHaveBeenCalledTimes(1);
            expect(mockRouterPush).toHaveBeenCalledWith('/login');
        });
    });
});
