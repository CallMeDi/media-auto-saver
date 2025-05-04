<template>
    <div class="default-layout">
        <header class="app-header">
            <h1>Media Auto Saver</h1>
            <nav v-if="authStore.isAuthenticated">
                <router-link to="/">链接 / Links</router-link> |
                <router-link to="/history">历史 / History</router-link> |
                <router-link to="/settings">设置 / Settings</router-link> |
                <button @click="logout">登出 / Logout</button>
                <span v-if="authStore.currentUser" class="user-info">
                    (用户 / User: {{ authStore.currentUser.username }})
                </span>
            </nav>
        </header>
        <main class="app-content">
            <router-view /> <!-- 页面组件将在这里渲染 / Page components will render here -->
        </main>
        <footer class="app-footer">
            <!-- 页脚内容 (可选) / Footer content (optional) -->
        </footer>
    </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();

const logout = () => {
    authStore.logout();
};
</script>

<style scoped>
.default-layout {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.app-header {
    background-color: #f8f9fa;
    padding: 10px 20px;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.app-header h1 {
    margin: 0;
    font-size: 1.5em;
}

nav a {
    font-weight: bold;
    color: #2c3e50;
    text-decoration: none;
    margin: 0 10px;
}

nav a.router-link-exact-active {
    color: #42b983;
}

nav button {
    background: none;
    border: none;
    color: #007bff;
    cursor: pointer;
    font-size: inherit;
    margin-left: 10px;
    padding: 0;
}

nav button:hover {
    text-decoration: underline;
}

.user-info {
    margin-left: 15px;
    font-size: 0.9em;
    color: #6c757d;
}

.app-content {
    flex: 1;
    /* 让主内容区域填充剩余空间 / Make main content area fill remaining space */
    padding: 20px;
    text-align: left;
    /* 重置 App.vue 的居中对齐 / Reset center alignment from App.vue */
}

.app-footer {
    background-color: #f8f9fa;
    padding: 10px 20px;
    text-align: center;
    font-size: 0.8em;
    color: #6c757d;
    border-top: 1px solid #dee2e6;
}
</style>
