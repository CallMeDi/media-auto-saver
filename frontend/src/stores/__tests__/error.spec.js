import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { ElMessage } from 'element-plus'; // Will be mocked
import { useErrorStore } from '../error'; // Adjust path as necessary, assuming this is correct

// Mock Element Plus ElMessage
// Based on the store code `ElMessage({ ... })`, ElMessage is a direct function.
vi.mock('element-plus', async (importOriginal) => {
  const original = await importOriginal(); // Import original to keep other exports if any
  return {
    ...original,
    ElMessage: vi.fn(), // Mock ElMessage as a function
  };
});

describe('Pinia Store: error.js', () => {
    let errorStore;
    let consoleErrorSpy;

    beforeEach(() => {
        setActivePinia(createPinia());
        
        // Suppress console.error output during tests and spy on it
        consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        
        // Reset ElMessage mock before each test
        ElMessage.mockReset(); // Since ElMessage is now vi.fn()

        // Get a fresh store instance
        errorStore = useErrorStore();
    });

    afterEach(() => {
        consoleErrorSpy.mockRestore(); // Restore console.error
        vi.clearAllMocks(); // Clear all mocks
    });

    describe('1. showError Action', () => {
        it('calls console.error and ElMessage with custom message', () => {
            const customErrorMessage = 'This is a custom error!';
            errorStore.showError(customErrorMessage);

            expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
            expect(consoleErrorSpy).toHaveBeenCalledWith("Global Error:", customErrorMessage);
            
            expect(ElMessage).toHaveBeenCalledTimes(1);
            expect(ElMessage).toHaveBeenCalledWith({
                message: customErrorMessage,
                type: 'error',
                showClose: true,
            });
        });

        it('calls ElMessage with default message when no message is provided', () => {
            errorStore.showError(undefined); // Or errorStore.showError()

            expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
            // The console.error will log "Global Error:", undefined in this case.
            // If a default message for console is also desired, the store's showError would need adjustment.
            // For now, we just check it was called.
            expect(consoleErrorSpy).toHaveBeenCalledWith("Global Error:", undefined);


            expect(ElMessage).toHaveBeenCalledTimes(1);
            expect(ElMessage).toHaveBeenCalledWith({
                message: 'An unexpected error occurred.',
                type: 'error',
                showClose: true,
            });
        });

        it('calls ElMessage with default message when message is null', () => {
            errorStore.showError(null);

            expect(consoleErrorSpy).toHaveBeenCalledTimes(1);
            expect(consoleErrorSpy).toHaveBeenCalledWith("Global Error:", null);


            expect(ElMessage).toHaveBeenCalledTimes(1);
            expect(ElMessage).toHaveBeenCalledWith({
                message: 'An unexpected error occurred.', // Falls back to default
                type: 'error',
                showClose: true,
            });
        });
    });

    describe('2. showSuccess Action', () => {
        it('calls ElMessage with custom success message', () => {
            const customSuccessMessage = 'Operation completed successfully!';
            errorStore.showSuccess(customSuccessMessage);

            expect(ElMessage).toHaveBeenCalledTimes(1);
            expect(ElMessage).toHaveBeenCalledWith({
                message: customSuccessMessage,
                type: 'success',
                showClose: true,
            });
            // console.error should not be called for success messages
            expect(consoleErrorSpy).not.toHaveBeenCalled();
        });

        it('calls ElMessage with default success message when no message is provided', () => {
            errorStore.showSuccess(undefined); // Or errorStore.showSuccess()

            expect(ElMessage).toHaveBeenCalledTimes(1);
            expect(ElMessage).toHaveBeenCalledWith({
                message: 'Operation successful.',
                type: 'success',
                showClose: true,
            });
            expect(consoleErrorSpy).not.toHaveBeenCalled();
        });
        
        it('calls ElMessage with default success message when message is null', () => {
            errorStore.showSuccess(null);

            expect(ElMessage).toHaveBeenCalledTimes(1);
            expect(ElMessage).toHaveBeenCalledWith({
                message: 'Operation successful.', // Falls back to default
                type: 'success',
                showClose: true,
            });
            expect(consoleErrorSpy).not.toHaveBeenCalled();
        });
    });
});
