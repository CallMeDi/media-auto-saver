import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth"; // 导入 Auth Store / Import Auth Store

// 导入页面组件 / Import page components
import LoginView from "../views/LoginView.vue";
import LinksView from "../views/LinksView.vue";
import HistoryView from "../views/HistoryView.vue";
import SettingsView from "../views/SettingsView.vue";
import PasswordResetRequestView from "../views/PasswordResetRequestView.vue";
import PasswordResetView from "../views/PasswordResetView.vue";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: LoginView,
  },
  {
    path: "/password-reset-request",
    name: "PasswordResetRequest",
    component: PasswordResetRequestView,
  },
  {
    path: "/reset-password",
    name: "PasswordReset",
    component: PasswordResetView,
  },
  {
    path: "/", // 根路径, 指向链接列表 / Root path, points to links list
    name: "Home",
    component: LinksView,
    meta: { requiresAuth: true }, // 标记需要认证 / Mark as requiring auth
  },
  {
    path: "/history",
    name: "History",
    component: HistoryView,
    meta: { requiresAuth: true },
  },
  {
    path: "/settings",
    name: "Settings",
    component: SettingsView,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // 使用 HTML5 History 模式 / Use HTML5 History mode
  routes,
});

// --- 导航守卫 (用于认证检查) / Navigation Guard (for authentication check) ---
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore(); // 获取 Auth Store 实例 / Get Auth Store instance
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
  const isAuthenticated = authStore.isAuthenticated; // 从 Store 获取认证状态 / Get auth status from Store

  if (requiresAuth && !isAuthenticated) {
    // 如果需要认证但用户未登录, 重定向到登录页
    // If auth is required and user is not logged in, redirect to login page
    next({ name: "Login" });
  } else if (to.name === "Login" && isAuthenticated) {
    // 如果用户已登录但尝试访问登录页, 重定向到首页
    // If user is logged in but tries to access login page, redirect to home
    next({ name: "Home" });
  } else {
    // 其他情况正常放行 / Otherwise, proceed normally
    next();
  }
});

export default router;
