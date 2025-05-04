import { defineStore } from "pinia";
import axios from "axios"; // 导入 axios / Import axios
import router from "@/router"; // 导入路由实例 / Import router instance
import { useErrorStore } from "./error"; // 导入 Error Store / Import Error Store
import { API_BASE_URL } from "@/utils/constants"; // 导入 API 基础 URL / Import API Base URL

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("token") || null, // 从 localStorage 初始化 token / Initialize token from localStorage
    user: null, // 当前用户信息 / Current user info
    // loginError: null, // 登录错误信息 / Login error message - Handled by Error Store
  }),
  getters: {
    isAuthenticated: (state) => !!state.token, // 是否已认证 / Is authenticated
    currentUser: (state) => state.user, // 获取当前用户 / Get current user
  },
  actions: {
    setToken(newToken) {
      this.token = newToken;
      if (newToken) {
        localStorage.setItem("token", newToken);
        axios.defaults.headers.common["Authorization"] = `Bearer ${newToken}`; // 设置 axios 默认请求头 / Set default axios header
      } else {
        localStorage.removeItem("token");
        delete axios.defaults.headers.common["Authorization"]; // 移除 axios 默认请求头 / Remove default axios header
      }
    },
    setUser(newUser) {
      this.user = newUser;
    },
    // setLoginError(error) { // Handled by Error Store
    //   this.loginError = error
    //     ? error.response?.data?.detail || error.message || "Login failed"
    //     : null;
    // },
    async login(username, password) {
      const errorStore = useErrorStore();
      // this.setLoginError(null); // 清除之前的错误 / Clear previous error - Handled by Error Store
      try {
        // 注意: 登录接口需要 'application/x-www-form-urlencoded'
        // Note: Login endpoint expects 'application/x-www-form-urlencoded'
        const params = new URLSearchParams();
        params.append("username", username);
        params.append("password", password);

        const response = await axios.post(
          `${API_BASE_URL}/login/access-token`,
          params,
          {
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
          }
        );

        const { access_token } = response.data;
        this.setToken(access_token);
        await this.fetchUser(); // 登录成功后获取用户信息 / Fetch user info after successful login
        router.push("/"); // 重定向到首页 / Redirect to home page
      } catch (error) {
        console.error("Login failed:", error);
        // this.setLoginError(error); // Handled by Error Store
        errorStore.showError(
          error.response?.data?.detail || error.message || "Login failed"
        );
        this.setToken(null); // 登录失败清除 token / Clear token on login failure
        this.setUser(null);
      }
    },
    async fetchUser() {
      if (!this.token) return; // 如果没有 token, 不执行 / Don't proceed if no token
      const errorStore = useErrorStore();
      try {
        const response = await axios.get(`${API_BASE_URL}/users/me`); // 请求头已在 setToken 中设置 / Header set in setToken
        this.setUser(response.data);
      } catch (error) {
        console.error("Failed to fetch user:", error);
        errorStore.showError(
          "Failed to fetch user information. Please log in again."
        );
        // 如果获取用户信息失败 (例如 token 过期), 则登出 / Logout if fetching user fails (e.g., token expired)
        this.logout();
      }
    },
    logout() {
      this.setToken(null);
      this.setUser(null);
      router.push("/login"); // 重定向到登录页 / Redirect to login page
    },
    // 应用启动时检查 token 并获取用户信息 / Check token and fetch user on app startup
    async checkAuth() {
      if (this.token) {
        axios.defaults.headers.common["Authorization"] = `Bearer ${this.token}`;
        await this.fetchUser();
      }
    },
  },
});
