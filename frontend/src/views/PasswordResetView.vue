<template>
    <div class="password-reset-view">
        <el-card class="reset-card">
            <template #header>
                <div class="card-header">
                    <span>重置密码 / Reset Password</span>
                </div>
            </template>
            <el-form @submit.prevent="handleResetPassword" label-position="top">
                <el-form-item label="新密码 / New Password" prop="newPassword">
                    <el-input type="password" v-model="newPassword" placeholder="请输入新密码 / Enter new password"
                        show-password required />
                </el-form-item>
                <el-form-item label="确认新密码 / Confirm New Password" prop="confirmPassword">
                    <el-input type="password" v-model="confirmPassword"
                        placeholder="请再次输入新密码 / Enter new password again" show-password required />
                </el-form-item>
                <el-form-item v-if="message">
                    <el-alert type="success" :title="message" show-icon :closable="true" @close="message = null" />
                </el-form-item>
                <el-form-item v-if="error">
                    <el-alert type="error" :title="error" show-icon :closable="true" @close="error = null" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%;">
                        {{ loading ? '重置中... / Resetting...' : '重置密码 / Reset Password' }}
                    </el-button>
                </el-form-item>
            </el-form>
            <div class="extra-links">
                <el-link type="primary" @click="goToLogin">返回登录 / Back to Login</el-link>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElCard, ElForm, ElFormItem, ElInput, ElButton, ElAlert, ElMessage, ElLink } from 'element-plus';
import axios from 'axios';
import { useRoute, useRouter } from 'vue-router'; // Import useRoute and useRouter

const newPassword = ref('');
const confirmPassword = ref('');
const loading = ref(false);
const message = ref(null);
const error = ref(null);

const route = useRoute(); // Get route instance to access query params
const router = useRouter();
const API_BASE_URL = "/api/v1";

const handleResetPassword = async () => {
    if (newPassword.value !== confirmPassword.value) {
        error.value = "两次输入的密码不一致 / Passwords do not match";
        return;
    }

    loading.value = true;
    message.value = null;
    error.value = null;

    const token = route.query.token; // Get token from query parameter

    if (!token) {
        error.value = "缺少密码重置令牌 / Missing password reset token";
        loading.value = false;
        return;
    }

    try {
        const response = await axios.post(`${API_BASE_URL}/reset-password/`, {
            token: token,
            new_password: newPassword.value,
        });
        message.value = response.data.message || "密码重置成功 / Password reset successfully";
        ElMessage.success(message.value);
        // Redirect to login page after successful reset
        router.push('/login');
    } catch (err) {
        console.error("Password reset failed:", err);
        error.value = err.response?.data?.detail || err.message || "Failed to reset password.";
    } finally {
        loading.value = false;
    }
};

const goToLogin = () => {
    router.push('/login');
};
</script>

<style scoped>
.password-reset-view {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - var(--el-header-height, 60px) - var(--el-footer-height, 60px) - 40px);
}

.reset-card {
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
    margin-bottom: 15px;
}
</style>
