import { createApp } from "vue";
import { createPinia } from "pinia"; // 导入 Pinia / Import Pinia
import ElementPlus from "element-plus"; // 导入 Element Plus / Import Element Plus
import "element-plus/dist/index.css"; // 导入 Element Plus 样式 / Import Element Plus styles
import App from "./App.vue";
import router from "./router"; // 导入路由 / Import router
import { useAuthStore } from "./stores/auth"; // 导入 auth store / Import auth store
import "./style.css"; // 保留基础样式 / Keep basic styles

const app = createApp(App);
const pinia = createPinia(); // 创建 Pinia 实例 / Create Pinia instance

app.use(ElementPlus); // 使用 Element Plus / Use Element Plus

app.use(pinia); // 先使用 Pinia / Use Pinia first
app.use(router); // 再使用路由 / Then use router

// 在挂载应用前检查认证状态 / Check auth status before mounting the app
const authStore = useAuthStore();
authStore.checkAuth().then(() => {
  app.mount("#app");
});
