<template>
    <div class="login-view">
        <el-card class="login-card">
            <template #header>
                <div class="card-header">
                    <span>登录 / Login</span>
                </div>
            </template>
            <el-form @submit.prevent="handleLogin" label-position="top">
                <el-form-item label="用户名 / Username" prop="username">
                    <el-input v-model="username" placeholder="请输入用户名 / Enter username" required />
                </el-form-item>
                <el-form-item label="密码 / Password" prop="password">
                    <el-input type="password" v-model="password" placeholder="请输入密码 / Enter password" show-password
                        required />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%;">
                        {{ loading ? '登录中... / Logging in...' : '登录 / Login' }}
                    </el-button>
                </el-form-item>
            </el-form>
            <div class="extra-links">
                <el-link type="primary" @click="goToPasswordReset">忘记密码? / Forgot Password?</el-link>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElCard, ElForm, ElFormItem, ElInput, ElButton, ElAlert, ElLink } from 'element-plus'; // 导入 Element Plus 组件 / Import Element Plus components
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router'; // 导入 useRouter / Import useRouter
import { useErrorStore } from '@/stores/error'; // Import Error Store

const username = ref('');
const password = ref('');
const loading = ref(false);
const authStore = useAuthStore();
const router = useRouter(); // 获取 router 实例 / Get router instance
const errorStore = useErrorStore(); // Use Error Store

const handleLogin = async () => {
    loading.value = true;
    // errorStore.clearError(); // Removed - Error store uses transient ElMessage, no state to clear
    await authStore.login(username.value, password.value);
    // 登录成功/失败由 authStore 处理 (包括跳转) / Login success/failure handled by authStore (including redirect)
    loading.value = false;
};

const goToPasswordReset = () => {
    router.push('/password-reset-request');
};
</script>

<style scoped>
.login-view {
    display: flex;
    justify-content: center;
    align-items: center;
    /* Assuming header and footer are each around 60px height, and main content has 20px padding top/bottom. */
    /* var(--el-header-height) and var(--el-footer-height) are typically 60px for Element Plus. */
    /* 40px accounts for 20px top + 20px bottom padding of el-main. */
    min-height: calc(100vh - var(--el-header-height, 60px) - var(--el-footer-height, 60px) - 40px);
}

.login-card {
    width: 100%;
    max-width: 450px;
}

.card-header {
    text-align: center;
    font-size: 1.5em;
}

.extra-links {
    margin-top: 15px;
    text-align: center;
    font-size: 0.9em;
}

.el-alert {
    width: 100%;
    /* 让警告框撑满 / Make alert full width */
}
</style>
