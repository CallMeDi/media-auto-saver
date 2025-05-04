import { defineStore } from "pinia";
import axios from "axios";
import { useAuthStore } from "./auth"; // 需要认证信息 / Need auth info
import { useErrorStore } from "./error"; // 导入 Error Store / Import Error Store
import { API_BASE_URL } from "@/utils/constants"; // 导入 API 基础 URL / Import API Base URL

export const useLinkStore = defineStore("link", {
  state: () => ({
    links: [], // 链接列表 / List of links
    isLoading: false, // 主列表加载状态 / Main list loading state
    linkLoading: {}, // 单个链接操作加载状态: { linkId: boolean } / Single link operation loading state: { linkId: boolean }
    linkErrors: {}, // 单个链接操作错误信息: { linkId: string | null } / Single link operation error message: { linkId: string | null }
    // error: null, // 错误信息 - 由 Error Store 处理 / Error message - Handled by Error Store
    // 可以添加分页信息 / Can add pagination info later
    // totalLinks: 0,
    // currentPage: 1,
    // pageSize: 10,
  }),
  getters: {
    linkList: (state) => state.links,
    loadingStatus: (state) => state.isLoading,
    // fetchError: (state) => state.error, // 由 Error Store 处理 / Handled by Error Store
  },
  actions: {
    /**
     * @description Fetch links from the backend.
     * @description 从后端获取链接列表。
     * @param {object} params - Optional query parameters. / 可选的查询参数。
     */
    async fetchLinks(params = {}) {
      this.isLoading = true;
      // this.error = null; // 由 Error Store 处理 / Handled by Error Store
      const authStore = useAuthStore();
      const errorStore = useErrorStore();
      if (!authStore.isAuthenticated) {
        // this.error = "User not authenticated"; // 由 Error Store 处理 / Handled by Error Store
        errorStore.showError("User not authenticated. Please log in.");
        this.isLoading = false;
        return;
      }

      try {
        // 添加分页、过滤参数 / Add pagination, filter parameters
        // The backend /api/v1/links/ endpoint supports filtering by site_name, status, is_enabled, tags.
        // The current frontend filter input is for "Name or URL".
        // We need to update the backend to support filtering by name or URL, or adjust the frontend filter.
        // For now, let's pass the filter text as a 'search' parameter, assuming the backend will be updated.
        const response = await axios.get(`${API_BASE_URL}/links/`, {
          params: {
            ...params,
            search: params.filter, // Pass the filter text as 'search' parameter
            filter: undefined, // Remove the 'filter' key if it exists
          },
        });
        this.links = response.data;
        // this.totalLinks = response.headers['x-total-count']; // 如果后端返回总数 / If backend returns total count
      } catch (err) {
        console.error("Failed to fetch links:", err); // 打印错误到控制台 / Log error to console
        // this.error = // Handled by Error Store
        //   err.response?.data?.detail || err.message || "Failed to fetch links.";
        errorStore.showError(
          err.response?.data?.detail || err.message || "Failed to fetch links."
        );
        this.links = []; // 清空列表 / Clear list on error
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * @description Add a new link to the backend.
     * @description 向后端添加新链接。
     * @param {object} linkData - The data for the new link. / 新链接的数据。
     * @returns {Promise<object|null>} The created link data or null on failure. / 创建的链接数据或失败时返回 null。
     */
    async addLink(linkData) {
      this.linkLoading[0] = true; // Use 0 or a specific ID for add operation loading
      this.linkErrors[0] = null;
      const authStore = useAuthStore();
      const errorStore = useErrorStore();
      if (!authStore.isAuthenticated) {
        errorStore.showError("User not authenticated. Please log in.");
        this.linkLoading[0] = false;
        return null;
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/links/`, linkData);
        await this.fetchLinks();
        errorStore.showSuccess("Link added successfully!");
        return response.data;
      } catch (err) {
        console.error("Failed to add link:", err);
        const errorMessage =
          err.response?.data?.detail || err.message || "Failed to add link.";
        errorStore.showError(errorMessage);
        this.linkErrors[0] = errorMessage;
        return null;
      } finally {
        this.linkLoading[0] = false;
      }
    },

    /**
     * @description Update an existing link.
     * @description 更新现有链接。
     * @param {number} linkId - The ID of the link to update. / 要更新的链接 ID。
     * @param {object} updateData - The data to update the link with. / 用于更新链接的数据。
     * @returns {Promise<object|null>} The updated link data or null on failure. / 更新后的链接数据或失败时返回 null。
     */
    async updateLink(linkId, updateData) {
      this.linkLoading[linkId] = true;
      this.linkErrors[linkId] = null;
      const authStore = useAuthStore();
      const errorStore = useErrorStore();
      if (!authStore.isAuthenticated) {
        errorStore.showError("User not authenticated. Please log in.");
        this.linkLoading[linkId] = false;
        return null;
      }
      try {
        const response = await axios.put(
          `${API_BASE_URL}/links/${linkId}`,
          updateData
        );
        await this.fetchLinks();
        errorStore.showSuccess("Link updated successfully!");
        return response.data;
      } catch (err) {
        console.error(`Failed to update link ${linkId}:`, err);
        const errorMessage =
          err.response?.data?.detail || err.message || "Failed to update link.";
        errorStore.showError(errorMessage);
        this.linkErrors[linkId] = errorMessage;
        return null;
      } finally {
        this.linkLoading[linkId] = false;
      }
    },

    /**
     * @description Delete a link by its ID.
     * @description 根据 ID 删除链接。
     * @param {number} linkId - The ID of the link to delete. / 要删除的链接 ID。
     * @returns {Promise<boolean>} True if deletion was successful, false otherwise. / 删除成功返回 true，否则返回 false。
     */
    async deleteLink(linkId) {
      this.linkLoading[linkId] = true;
      this.linkErrors[linkId] = null;
      const authStore = useAuthStore();
      const errorStore = useErrorStore();
      if (!authStore.isAuthenticated) {
        errorStore.showError("User not authenticated. Please log in.");
        this.linkLoading[linkId] = false;
        return false;
      }
      try {
        await axios.delete(`${API_BASE_URL}/links/${linkId}`);
        await this.fetchLinks();
        errorStore.showSuccess("Link deleted successfully!");
        return true;
      } catch (err) {
        console.error(`Failed to delete link ${linkId}:`, err);
        const errorMessage =
          err.response?.data?.detail || err.message || "Failed to delete link.";
        errorStore.showError(errorMessage);
        this.linkErrors[linkId] = errorMessage;
        return false;
      } finally {
        this.linkLoading[linkId] = false;
      }
    },

    /**
     * @description Manually trigger the monitoring/download task for a single link.
     * @description 手动触发单个链接的监控/下载任务。
     * @param {number} linkId - The ID of the link to trigger. / 要触发的链接 ID。
     * @returns {Promise<boolean>} True if triggering was successful, false otherwise. / 触发成功返回 true，否则返回 false。
     */
    async triggerLinkTask(linkId) {
      this.linkLoading[linkId] = true;
      this.linkErrors[linkId] = null;
      const authStore = useAuthStore();
      const errorStore = useErrorStore();
      if (!authStore.isAuthenticated) {
        errorStore.showError("User not authenticated. Please log in.");
        this.linkLoading[linkId] = false;
        return false;
      }
      try {
        await axios.post(`${API_BASE_URL}/links/${linkId}/trigger`);
        errorStore.showSuccess(`Task triggered for link ${linkId}!`);
        // Optionally refresh the links list to show updated status immediately
        // await this.fetchLinks();
        return true;
      } catch (err) {
        console.error(`Failed to trigger task for link ${linkId}:`, err);
        const errorMessage =
          err.response?.data?.detail ||
          err.message ||
          `Failed to trigger task for link ${linkId}.`;
        errorStore.showError(errorMessage);
        this.linkErrors[linkId] = errorMessage;
        return false;
      } finally {
        this.linkLoading[linkId] = false;
      }
    },
  },
});
