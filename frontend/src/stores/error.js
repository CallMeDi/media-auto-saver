import { defineStore } from "pinia";
import { ElMessage } from "element-plus"; // Import ElMessage for notifications

export const useErrorStore = defineStore("error", {
  state: () => ({
    // You could potentially store active errors here if needed,
    // but for simple notifications, just using ElMessage directly is fine.
  }),
  actions: {
    showError(message) {
      console.error("Global Error:", message); // Log error for debugging
      ElMessage({
        message: message || "An unexpected error occurred.",
        type: "error",
        showClose: true,
      });
    },
    // You could add other types like showWarning, showInfo, showSuccess
    showSuccess(message) {
      ElMessage({
        message: message || "Operation successful.",
        type: "success",
        showClose: true,
      });
    },
  },
});
