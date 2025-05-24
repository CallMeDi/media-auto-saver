<template>
    <el-container direction="vertical" class="default-layout">
        <el-header class="app-header">
            <el-row justify="space-between" align="middle" style="width: 100%;">
                <el-col :span="8">
                    <h1>Media Auto Saver</h1>
                </el-col>
                <el-col :span="16" style="text-align: right;">
                    <el-menu v-if="authStore.isAuthenticated" mode="horizontal" :router="true" class="app-nav">
                        <el-menu-item index="/">
                            <router-link to="/">链接 / Links</router-link>
                        </el-menu-item>
                        <el-menu-item index="/history">
                            <router-link to="/history">历史 / History</router-link>
                        </el-menu-item>
                        <el-menu-item index="/settings">
                            <router-link to="/settings">设置 / Settings</router-link>
                        </el-menu-item>
                        <!-- User Dropdown -->
                        <el-dropdown v-if="authStore.currentUser" class="user-dropdown" trigger="click">
                            <span class="el-dropdown-link">
                                用户 / User: {{ authStore.currentUser.username }} <i class="el-icon-arrow-down el-icon--right"></i>
                            </span>
                            <template #dropdown>
                                <el-dropdown-menu>
                                    <el-dropdown-item @click="logout">登出 / Logout</el-dropdown-item>
                                </el-dropdown-menu>
                            </template>
                        </el-dropdown>
                    </el-menu>
                </el-col>
            </el-row>
        </el-header>
        <el-main class="app-content">
            <router-view /> <!-- 页面组件将在这里渲染 / Page components will render here -->
        </el-main>
        <el-footer class="app-footer">
            <!-- 页脚内容 (可选) / Footer content (optional) -->
            <p>&copy; {{ new Date().getFullYear() }} Media Auto Saver. All rights reserved.</p>
        </el-footer>
    </el-container>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';
import { 
    ElContainer, ElHeader, ElMain, ElFooter, 
    ElRow, ElCol, ElMenu, ElMenuItem, 
    ElButton, ElDropdown, ElDropdownMenu, ElDropdownItem 
} from 'element-plus';

const authStore = useAuthStore();

const logout = () => {
    authStore.logout();
};
</script>

<style scoped>
.default-layout {
    min-height: 100vh;
}

.app-header {
    /* background-color: #f8f9fa; Retain or use Element Plus variable */
    border-bottom: 1px solid var(--el-border-color-light);
    display: flex; /* Keep flex for el-row to work as expected if needed */
    align-items: center; /* Align items vertically */
    padding: 0 20px; /* Adjust padding as ElHeader has its own */
}

.app-header h1 {
    margin: 0;
    font-size: 1.5em;
    color: var(--el-text-color-primary);
}

.app-nav {
    display: inline-flex; /* Align menu items and button nicely */
    align-items: center;
    border-bottom: none; /* ElMenu might add its own border */
}

.app-nav .el-menu-item {
    padding: 0 15px; /* Adjust padding */
}

.app-nav .el-menu-item a {
    text-decoration: none;
    color: inherit; /* Inherit color from ElMenuItem */
}

/* Element Plus handles active link styling via :router="true" and el-menu-item index */

.user-dropdown {
    margin-left: 20px; /* Spacing from the menu items */
    display: flex; /* Align items nicely if needed */
    align-items: center; /* Align items nicely */
    cursor: pointer;
}

.el-dropdown-link {
    color: var(--el-text-color-regular); /* Standard text color */
    display: flex;
    align-items: center;
}

.el-dropdown-link:hover {
    color: var(--el-color-primary); /* Highlight on hover */
}

.app-content {
    /* flex: 1; ElMain should handle this */
    padding: 20px;
    text-align: left; 
}

.app-footer {
    /* background-color: #f8f9fa; Retain or use Element Plus variable */
    padding: 10px 20px;
    text-align: center;
    font-size: 0.8em;
    color: var(--el-text-color-secondary);
    border-top: 1px solid var(--el-border-color-light);
}
</style>
