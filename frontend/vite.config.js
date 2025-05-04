import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path"; // 导入 path 模块 / Import path module

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"), // 设置 '@' 指向 'src' 目录 / Set '@' to point to 'src' directory
    },
  },
  server: {
    proxy: {
      // 字符串简写写法: http://localhost:5173/api -> http://localhost:8000/api
      // String shorthand: http://localhost:5173/api -> http://localhost:8000/api
      // '/api': 'http://localhost:8000', // 如果后端 API 没有统一前缀, 可能需要更复杂的配置

      // 将 /api/v1 的请求代理到后端 / Proxy requests for /api/v1 to the backend
      "/api/v1": {
        target: "http://localhost:8000", // 后端服务器地址 / Backend server address
        changeOrigin: true, // 需要虚拟主机站点 / Needed for virtual hosted sites
        // rewrite: (path) => path.replace(/^\/api\/v1/, '/api/v1'), // 通常不需要重写路径 / Usually no need to rewrite path
      },
    },
  },
});
