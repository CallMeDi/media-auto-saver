import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick, ref, reactive } from 'vue';
import SettingsView from '../SettingsView.vue';
import { ElMessageBox, ElCard, ElButton, ElDialog, ElForm, ElFormItem, ElInput, ElAlert, ElText } from 'element-plus';
import axios from 'axios';

// Mock Pinia store: useAuthStore
import { useAuthStore } from '@/stores/auth';

// Mock axios
vi.mock('axios');

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

// Mock useAuthStore
vi.mock('@/stores/auth', () => ({
    useAuthStore: vi.fn(() => ({
        token: 'mocktoken12345' // Provide a mock token
    }))
}));


describe('SettingsView.vue', () => {
    let wrapper;
    let mockAuthStore; // To ensure it's accessible if needed, though already mocked

    // Mocks for window.URL and document.createElement for file download simulation
    const mockCreateObjectURL = vi.fn();
    const mockRevokeObjectURL = vi.fn();
    const mockLinkClick = vi.fn();
    const mockLinkRemove = vi.fn();

    beforeEach(async () => {
        axios.get.mockReset();
        axios.post.mockReset();
        axios.put.mockReset();
        ElMessageBox.confirm.mockReset();
        ElMessageBox.alert.mockReset();
        
        mockAuthStore = useAuthStore(); // Initialize to get the mocked instance

        // Setup mocks for download simulation
        global.URL.createObjectURL = mockCreateObjectURL;
        global.URL.revokeObjectURL = mockRevokeObjectURL;
        global.document.createElement = vi.fn(() => ({
            href: '',
            setAttribute: vi.fn(),
            click: mockLinkClick,
            remove: mockLinkRemove,
        }));
        global.document.body.appendChild = vi.fn();
        global.document.body.removeChild = vi.fn(); // Though remove() is on element itself

        wrapper = mount(SettingsView, {
            global: {
                // stubs: { ElDialog: true } // Can stub dialog if not testing its internal form deeply initially
            }
        });
        // onMounted calls fetchSiteCookies, so wait if it's async
        // Assuming fetchSiteCookies is called and might be async
        await nextTick();
    });

    afterEach(() => {
        vi.clearAllMocks();
        if (wrapper) {
            wrapper.unmount();
        }
    });

    describe('1. Database Management', () => {
        describe('Export Database', () => {
            it('successfully exports database', async () => {
                const blobData = new Blob(['test sql data']);
                axios.get.mockResolvedValue({
                    data: blobData,
                    headers: { 'content-disposition': 'attachment; filename="database_export_test.sql"' }
                });
                mockCreateObjectURL.mockReturnValue('blob:http://localhost/mock-url');

                const exportButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('导出 / Export'));
                await exportButton.trigger('click');
                
                expect(wrapper.vm.exporting).toBe(true);
                await nextTick(); // for axios call
                await nextTick(); // for promise to resolve and DOM updates

                expect(axios.get).toHaveBeenCalledWith('/api/v1/database/export', expect.any(Object));
                expect(mockCreateObjectURL).toHaveBeenCalledWith(blobData);
                expect(document.createElement).toHaveBeenCalledWith('a');
                expect(mockLinkClick).toHaveBeenCalled();
                expect(mockLinkRemove).toHaveBeenCalled(); // or document.body.removeChild if that was used
                expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:http://localhost/mock-url');
                expect(wrapper.vm.exporting).toBe(false);
                expect(wrapper.vm.exportError).toBe(null);
            });

            it('handles export failure', async () => {
                const errorMsg = 'Export failed due to server error';
                axios.get.mockRejectedValue({ response: { data: { detail: errorMsg } } });

                const exportButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('导出 / Export'));
                await exportButton.trigger('click');
                
                expect(wrapper.vm.exporting).toBe(true);
                await nextTick();
                await nextTick();

                expect(wrapper.vm.exporting).toBe(false);
                expect(wrapper.vm.exportError).toBe(errorMsg);
            });
        });

        describe('Import Database', () => {
            let fileInputRefMock;
            
            beforeEach(() => {
                // Mock the ref for file input
                fileInputRefMock = { value: { click: vi.fn(), value: '' } }; // Mock the .value of the ref
                wrapper.vm.fileInputRef = fileInputRefMock; // Assign to component instance
            });

            it('triggers file input on "Choose File" click', async () => {
                const chooseFileButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('选择文件 / Choose File'));
                await chooseFileButton.trigger('click');
                expect(fileInputRefMock.value.click).toHaveBeenCalled();
            });

            it('updates selectedFile on file change', async () => {
                const mockFile = new File(['dummy sql content'], 'import.sql', { type: 'application/sql' });
                const event = { target: { files: [mockFile] } };
                
                // Call the method directly as simulating file input change event on a mocked ref is tricky
                wrapper.vm.handleFileChange(event); 
                await nextTick();

                expect(wrapper.vm.selectedFile).toBe(mockFile);
                expect(wrapper.findComponent(ElText).text()).toBe('import.sql'); // Check if filename is displayed
            });

            it('successfully imports database after confirmation', async () => {
                ElMessageBox.confirm.mockResolvedValue('confirm'); // User confirms
                const mockFile = new File(['dummy sql content'], 'import.sql', { type: 'application/sql' });
                wrapper.vm.selectedFile = mockFile; // Simulate file selected
                axios.post.mockResolvedValue({ data: { message: 'Import successful!' } });

                const importButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('导入并覆盖 / Import & Overwrite'));
                await importButton.trigger('click');
                
                expect(wrapper.vm.importing).toBe(true);
                await nextTick();
                await nextTick();

                expect(ElMessageBox.confirm).toHaveBeenCalled();
                expect(axios.post).toHaveBeenCalledWith('/api/v1/database/import', expect.any(FormData), expect.any(Object));
                expect(wrapper.vm.importing).toBe(false);
                expect(wrapper.vm.importMessage).toBe('Import successful!');
                expect(wrapper.vm.selectedFile).toBe(null); // File selection should be cleared
            });

            it('handles import failure from API', async () => {
                ElMessageBox.confirm.mockResolvedValue('confirm');
                const mockFile = new File(['dummy sql content'], 'import_fail.sql', { type: 'application/sql' });
                wrapper.vm.selectedFile = mockFile;
                const errorMsg = 'Import API error';
                axios.post.mockRejectedValue({ response: { data: { detail: errorMsg } } });

                const importButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('导入并覆盖 / Import & Overwrite'));
                await importButton.trigger('click');
                await nextTick();
                await nextTick();

                expect(wrapper.vm.importing).toBe(false);
                expect(wrapper.vm.importError).toBe(true);
                expect(wrapper.vm.importMessage).toBe(errorMsg);
            });

            it('does not import if user cancels confirmation', async () => {
                ElMessageBox.confirm.mockRejectedValue('cancel');
                const mockFile = new File(['dummy sql content'], 'import_cancel.sql', { type: 'application/sql' });
                wrapper.vm.selectedFile = mockFile;

                const importButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('导入并覆盖 / Import & Overwrite'));
                await importButton.trigger('click');
                await nextTick();

                expect(axios.post).not.toHaveBeenCalled();
                expect(wrapper.vm.importing).toBe(false);
            });
        });
    });

    describe('2. Account Settings (Change Password Dialog)', () => {
        it('opens change password dialog', async () => {
            const changePassButton = wrapper.findAllComponents(ElButton).find(b => b.text() === '修改 / Change');
            await changePassButton.trigger('click');
            expect(wrapper.vm.showPasswordDialog).toBe(true);
            expect(wrapper.findComponent(ElDialog).props().modelValue).toBe(true);
        });

        // Tests for inside the dialog
        describe('Change Password Dialog Logic', () => {
            beforeEach(async () => {
                wrapper.vm.showPasswordDialog = true; // Open the dialog
                await nextTick();
            });

            it('validates password mismatch', async () => {
                const dialogWrapper = wrapper.findComponent(ElDialog);
                const inputs = dialogWrapper.findAllComponents(ElInput);
                await inputs.find(i => i.props().placeholder === undefined && i.vm.modelValue === wrapper.vm.passwordData.newPassword).setValue('newPass123');
                await inputs.find(i => i.props().placeholder === undefined && i.vm.modelValue === wrapper.vm.passwordData.confirmPassword).setValue('newPassMismatch');
                
                const confirmButton = dialogWrapper.findAllComponents(ElButton).find(b => b.text().includes('确认修改'));
                await confirmButton.trigger('click');
                await nextTick(); // for validation

                expect(wrapper.vm.passwordError).toBe("两次输入的新密码不一致 / New passwords do not match!");
                const errorAlert = dialogWrapper.findComponent(ElAlert);
                expect(errorAlert.exists()).toBe(true);
                expect(errorAlert.props().title).toBe("两次输入的新密码不一致 / New passwords do not match!");
            });
            
            it('validates new password too short (min 8 chars)', async () => {
                const dialogWrapper = wrapper.findComponent(ElDialog);
                const inputs = dialogWrapper.findAllComponents(ElInput);
                await inputs.find(i => i.vm.modelValue === wrapper.vm.passwordData.currentPassword).setValue('currentP');
                await inputs.find(i => i.vm.modelValue === wrapper.vm.passwordData.newPassword).setValue('short');
                await inputs.find(i => i.vm.modelValue === wrapper.vm.passwordData.confirmPassword).setValue('short');

                const confirmButton = dialogWrapper.findAllComponents(ElButton).find(b => b.text().includes('确认修改'));
                await confirmButton.trigger('click'); // This should trigger form validation
                await nextTick();
                
                // Check for validation message on the newPassword field
                // Note: Accessing form validation messages can be tricky.
                // The component's passwordError ref is for API errors, not form validation errors.
                // We rely on Element Plus form validation to show errors.
                // For this test, we'll check if the API call was prevented.
                expect(axios.put).not.toHaveBeenCalled();
            });


            it('successfully changes password', async () => {
                axios.put.mockResolvedValue({ data: { message: 'Password changed' } });
                ElMessageBox.alert.mockResolvedValueOnce(); // For success alert

                const dialogWrapper = wrapper.findComponent(ElDialog);
                wrapper.vm.passwordData.currentPassword = 'oldPassword';
                wrapper.vm.passwordData.newPassword = 'newValidPassword';
                wrapper.vm.passwordData.confirmPassword = 'newValidPassword';
                await nextTick();

                const confirmButton = dialogWrapper.findAllComponents(ElButton).find(b => b.text().includes('确认修改'));
                await confirmButton.trigger('click');
                
                expect(wrapper.vm.passwordSubmitting).toBe(true);
                await nextTick();
                await nextTick();

                expect(axios.put).toHaveBeenCalledWith('/api/v1/users/me/password', {
                    current_password: 'oldPassword',
                    new_password: 'newValidPassword'
                }, expect.any(Object));
                expect(ElMessageBox.alert).toHaveBeenCalledWith('密码修改成功 / Password changed successfully.', 'Success', { type: 'success' });
                expect(wrapper.vm.showPasswordDialog).toBe(false);
                expect(wrapper.vm.passwordSubmitting).toBe(false);
            });

            it('handles password change failure from API', async () => {
                const errorMsg = 'Incorrect current password';
                axios.put.mockRejectedValue({ response: { data: { detail: errorMsg } } });

                const dialogWrapper = wrapper.findComponent(ElDialog);
                wrapper.vm.passwordData.currentPassword = 'wrongOldPassword';
                wrapper.vm.passwordData.newPassword = 'newValidPasswordFail';
                wrapper.vm.passwordData.confirmPassword = 'newValidPasswordFail';
                await nextTick();

                const confirmButton = dialogWrapper.findAllComponents(ElButton).find(b => b.text().includes('确认修改'));
                await confirmButton.trigger('click');
                await nextTick();
                await nextTick();

                expect(wrapper.vm.passwordError).toBe(errorMsg);
                expect(dialogWrapper.findComponent(ElAlert).props().title).toBe(errorMsg);
                expect(wrapper.vm.showPasswordDialog).toBe(true); // Dialog remains open
                expect(wrapper.vm.passwordSubmitting).toBe(false);
            });
        });
    });

    describe('3. Global Cookies Settings', () => {
        const sampleCookiesData = { "example.com": "path/to/cookie.txt", "test.org": "another/path.json" };

        it('fetches site cookies on mount', async () => {
            axios.get.mockResolvedValue({ data: sampleCookiesData });
            // Re-mount or trigger onMounted if not covered by initial mount
            // For this case, the initial mount in global beforeEach already called it.
            // We need to ensure the mock is set *before* that initial mount.
            // So, this test should be fine if the main beforeEach's mount calls onMounted.
            // Let's ensure the mock is set for the onMounted call.
            axios.get.mockClear(); // Clear any previous calls
            axios.get.mockResolvedValue({ data: sampleCookiesData });
            
            wrapper.unmount(); // Unmount the one from global beforeEach
            wrapper = mount(SettingsView); // Mount again to trigger onMounted with this specific mock
            await nextTick();

            expect(axios.get).toHaveBeenCalledWith('/api/v1/settings/cookies', expect.any(Object));
            expect(wrapper.vm.siteCookies).toEqual(sampleCookiesData);
        });

        it('handles fetch site cookies failure', async () => {
            const errorMsg = "Failed to load cookies";
            axios.get.mockRejectedValue({ response: { data: { detail: errorMsg } } });
            
            wrapper.unmount(); 
            wrapper = mount(SettingsView);
            await nextTick();

            expect(wrapper.vm.cookiesError).toBe(errorMsg);
        });

        it('adds a new site cookie entry', async () => {
            wrapper.vm.siteCookies = {}; // Start with empty
            wrapper.vm.newSiteName = 'newsite.com';
            wrapper.vm.newSiteCookiePath = 'new/path.txt';
            await nextTick();

            const addButton = wrapper.findAllComponents(ElButton).find(b => b.text() === '添加 / Add');
            await addButton.trigger('click');
            
            expect(wrapper.vm.siteCookies['newsite.com']).toBe('new/path.txt');
            expect(wrapper.vm.newSiteName).toBe('');
            expect(wrapper.vm.newSiteCookiePath).toBe('');
        });

        it('removes a site cookie entry', async () => {
            wrapper.vm.siteCookies = { ...sampleCookiesData };
            await nextTick();
            
            // Find the remove button for "example.com"
            const exampleComItem = wrapper.findAllComponents(ElFormItem).find(item => item.props().label?.startsWith('example.com'));
            const removeButton = exampleComItem.findComponent(ElButton); // Assuming it's the only button there
            await removeButton.trigger('click');

            expect(wrapper.vm.siteCookies['example.com']).toBeUndefined();
            expect(wrapper.vm.siteCookies['test.org']).toBe('another/path.json'); // Ensure others remain
        });

        it('saves global cookies successfully', async () => {
            axios.put.mockResolvedValue({ data: {} }); // Success response
            wrapper.vm.siteCookies = { "updated.com": "updated/path.txt" };
            await nextTick();

            const saveButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('保存全局 Cookies'));
            await saveButton.trigger('click');
            
            expect(wrapper.vm.savingCookies).toBe(true);
            await nextTick();
            await nextTick();

            expect(axios.put).toHaveBeenCalledWith('/api/v1/settings/cookies', { site_cookies: { "updated.com": "updated/path.txt" } }, expect.any(Object));
            expect(wrapper.vm.cookiesSuccess).toBe(true);
            expect(wrapper.vm.savingCookies).toBe(false);
        });

        it('handles save global cookies failure', async () => {
            const errorMsg = "Failed to save cookies";
            axios.put.mockRejectedValue({ response: { data: { detail: errorMsg } } });
            wrapper.vm.siteCookies = { "fail.com": "fail/path.txt" };
            await nextTick();

            const saveButton = wrapper.findAllComponents(ElButton).find(b => b.text().includes('保存全局 Cookies'));
            await saveButton.trigger('click');
            await nextTick();
            await nextTick();

            expect(wrapper.vm.cookiesError).toBe(errorMsg);
            expect(wrapper.vm.cookiesSuccess).toBe(false);
            expect(wrapper.vm.savingCookies).toBe(false);
        });
    });
});
