import { defineStore } from "pinia";
import axios from "axios";
import { useAuthStore } from "./auth"; // 需要认证信息 / Need auth info
import { useErrorStore } from "./error"; // 导入 Error Store / Import Error Store
import { API_BASE_URL } from "@/utils/constants"; // 导入 API 基础 URL / Import API Base URL

export const useHistoryStore = defineStore("history", {
  state: () => ({
    historyLogs: [], // 历史记录列表 / List of history entries
    isLoading: false, // 加载状态 / Loading state
    // error: null, // 错误信息 / Error message - Handled by Error Store
    // Pagination state if needed
    // totalLogs: 0,
    // currentPage: 1,
    // pageSize: 20,
  }),
  getters: {
    logs: (state) => state.historyLogs, // 获取历史记录列表 / Get history entries list
    loadingStatus: (state) => state.isLoading, // 获取加载状态 / Get loading status
    // fetchError: (state) => state.error, // 错误信息 (由 Error Store 处理) / Error message (Handled by Error Store)
  },
  actions: {
    /**
     * @description Fetch history entries from the backend.
     * @description 从后端获取历史记录列表。
     * @param {object} params - Optional query parameters. / 可选的查询参数。
     */
    async fetchHistory(params = {}) {
      this.isLoading = true;
      // this.error = null; // Error handled by Error Store
      const authStore = useAuthStore();
      const errorStore = useErrorStore();
      if (!authStore.isAuthenticated) {
        // this.error = "User not authenticated"; // Error handled by Error Store
        errorStore.showError("User not authenticated. Please log in."); // 显示错误消息 / Show error message
        this.isLoading = false;
        return;
      }

      try {
        // TODO: Add pagination and filtering params / TODO: 添加分页和过滤参数
        const response = await axios.get(`${API_BASE_URL}/history/`, {
          params,
        });
        this.historyLogs = response.data;
        // this.totalLogs = response.headers['x-total-count']; // If backend provides total count / 如果后端提供总数
      } catch (err) {
        console.error("Failed to fetch history:", err); // 打印错误到控制台 / Log error to console
        // this.error = // Error handled by Error Store
        //   err.response?.data?.detail ||
        //   err.message ||
        //   "Failed to fetch history.";
        errorStore.showError(
          err.response?.data?.detail ||
            err.message ||
            "Failed to fetch history."
        ); // 显示错误消息 / Show error message
        this.historyLogs = []; // 清空列表 / Clear list on error
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * @description Delete a history entry by its ID.
     * @description 根据 ID 删除历史记录。
     * @param {number} logId - The ID of the history entry to delete. / 要删除的历史记录 ID。
     * @returns {Promise<boolean>} True if deletion was successful, false otherwise. / 删除成功返回 true，否则返回 false。
     */
    async deleteHistoryLog(logId) {
      this.isLoading = true; // Consider separate loading state for deletion / 可以为删除操作设置单独的加载状态
      // this.error = null; // Error handled by Error Store
      const authStore = useAuthStore();
      const errorStore = useErrorStore();
      if (!authStore.isAuthenticated) {
        // this.error = "User not authenticated"; // Error handled by Error Store
        errorStore.showError("User not authenticated. Please log in."); // 显示错误消息 / Show error message
        this.isLoading = false;
        return false; // 返回 false 表示失败 / Return false on failure
      }
      try {
        await axios.delete(`${API_BASE_URL}/history/${logId}`);
        // Remove the log from the local state or refetch / 从本地状态移除记录或重新获取
        this.historyLogs = this.historyLogs.filter((log) => log.id !== logId);
        errorStore.showSuccess("History log deleted successfully!"); // 显示成功消息 / Show success message
        // Or: await this.fetchHistory(); // 或者: 重新获取列表
        return true; // 返回 true 表示成功 / Return true on success
      } catch (err) {
        console.error(`Failed to delete history log ${logId}:`, err); // 打印错误到控制台 / Log error to console
        // this.error = // Error handled by Error Store
        //   err.response?.data?.detail ||
        //   err.message ||
        //   "Failed to delete history log.";
        errorStore.showError(
          err.response?.data?.detail ||
            err.message ||
            "Failed to delete history log."
        ); // 显示错误消息 / Show error message
        return false; // 返回 false 表示失败 / Return false on failure
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * @description Delete all history entries associated with a specific link.
     * @description 删除与特定链接关联的所有历史记录。
     * @param {number} linkId - The ID of the link. / 链接的 ID。
     * @returns {Promise<boolean>} True if deletion was successful, false otherwise. / 删除成功返回 true，否则返回 false。
     */
    async deleteHistoryByLink(linkId) {
      this.isLoading = true;
      // this.error = null; // Error handled by Error Store
      const authStore = useAuthStore();
      const errorStore = useErrorStore();
      if (!authStore.isAuthenticated) {
        // this.error = "User not authenticated"; // Error handled by Error Store
        errorStore.showError("User not authenticated. Please log in."); // 显示错误消息 / Show error message
        this.isLoading = false;
        return false; // 返回 false 表示失败 / Return false on failure
      }
      try {
        await axios.delete(`${API_BASE_URL}/history/by_link/${linkId}`);
        // Refetch history after deletion (or filter locally if feasible) / 删除后重新获取历史记录 (如果可行则在本地过滤)
        await this.fetchHistory();
        errorStore.showSuccess("History for link deleted successfully!"); // 显示成功消息 / Show success message
        return true; // 返回 true 表示成功 / Return true on success
      } catch (err) {
        console.error(`Failed to delete history for link ${linkId}:`, err); // 打印错误到控制台 / Log error to console
        // this.error = // Error handled by Error Store
        //   err.response?.data?.detail ||
        //   err.message ||
        //   "Failed to delete history for link.";
        errorStore.showError(
          err.response?.data?.detail ||
            err.message ||
            "Failed to delete history for link."
        ); // 显示错误消息 / Show error message
        return false; // 返回 false 表示失败 / Return false on failure
      } finally {
        this.isLoading = false;
      }
    },
  },
});
