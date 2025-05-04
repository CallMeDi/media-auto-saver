<template>
    <div class="password-reset-request-view">
        <el-card class="reset-card">
            <template #header>
                <div class="card-header">
                    <span>请求密码重置 / Request Password Reset</span>
                </div>
            </template>
            <el-form @submit.prevent="handleRequestReset" label-position="top">
                <el-form-item label="用户名 / Username" prop="username">
                    <el-input v-model="username" placeholder="请输入用户名 / Enter username" required />
                </el-form-item>
                <el-form-item v-if="message">
                    <el-alert type="info" :title="message" show-icon :closable="false" />
                </el-form-item>
                <el-form-item v-if="error">
                    <el-alert type="error" :title="error" show-icon :closable="false" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%;">
                        {{ loading ? '发送中... / Sending...' : '发送重置链接 / Send Reset Link' }}
                    </el-button>
                </el-form-item>
            </el-form>
            <div class="extra-links">
                <router-link to="/login">返回登录 / Back to Login</router-link>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElCard, ElForm, ElFormItem, ElInput, ElButton, ElAlert } from 'element-plus';
import axios from 'axios'; // Import axios
import { useRouter } from 'vue-router';
import { useErrorStore } from '@/stores/error'; // Import Error Store

const username = ref('');
const loading = ref(false);
const message = ref(null);
const router = useRouter();
const errorStore = useErrorStore(); // Use Error Store

const API_BASE_URL = "/api/v1"; // Define API base URL

const handleRequestReset = async () => {
    loading.value = true;
    message.value = null;
    errorStore.clearError(); // Clear previous error using Error Store
    try {
        // Note: The backend endpoint currently returns the token directly.
        // In a real application, this should trigger an email sending process.
        const response = await axios.post(`${API_BASE_URL}/password-recovery/${username.value}`);
        message.value = `Password reset token generated for ${response.data.username}. Token: ${response.data.reset_token}. Expires at: ${new Date(response.data.expires_at).toLocaleString()}. (Note: In a real app, this token would be sent via email.)`;
        // Optionally redirect to a page informing the user to check their email
        // router.push('/check-email');
    } catch (err) {
        console.error("Password reset request failed:", err);
        errorStore.showError(err.response?.data?.detail || err.message || "Failed to request password reset.");
    } finally {
        loading.value = false;
    }
};
</script>

<style scoped>
.password-reset-request-view {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 150px);
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
    /* Add some space below the alert */
}
</style>
