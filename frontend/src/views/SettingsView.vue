<template>
    <div class="settings-view">
        <h2>设置 / Settings</h2>

        <!-- 数据库管理 -->
        <!-- Database Management -->
        <el-card class="box-card" shadow="never">
            <template #header>
                <div class="card-header">
                    <span>数据库管理 / Database Management</span>
                </div>
            </template>
            <el-form label-position="left" label-width="220px">
                <el-form-item label="导出数据库 / Export Database:">
                    <el-button @click="exportDatabase" :loading="exporting" type="primary" size="small">
                        {{ exporting ? '导出中...' : '导出 / Export' }}
                    </el-button>
                    <el-text v-if="exportError" type="danger" size="small" style="margin-left: 10px;">{{ exportError }}</el-text>
                </el-form-item>

                <el-form-item label="导入数据库 / Import Database:">
                    <el-space wrap>
                        <input type="file" ref="fileInputRef" @change="handleFileChange" accept=".sql" :disabled="importing" style="display: none;" />
                        <el-button @click="triggerFileInput" size="small" :disabled="importing">选择文件 / Choose File</el-button>
                        <el-text v-if="selectedFile" class="file-name" size="small">{{ selectedFile.name }}</el-text>
                        <el-button @click="importDatabase" :disabled="!selectedFile || importing" type="danger" size="small">
                            {{ importing ? '导入中...' : '导入并覆盖 / Import & Overwrite' }}
                        </el-button>
                    </el-space>
                    <el-text type="warning" size="small" style="display: block; margin-top: 5px;">
                        警告: 导入将覆盖当前所有数据! / Warning: Import will overwrite all current data!
                    </el-text>
                    <el-alert v-if="importMessage" :title="importMessage" :type="importError ? 'error' : 'success'" show-icon closable @close="importMessage = null" style="margin-top: 10px;" />
                </el-form-item>
            </el-form>
        </el-card>

        <!-- 账户设置 -->
        <!-- Account Settings -->
        <el-card class="box-card" shadow="never">
            <template #header>
                <div class="card-header">
                    <span>账户设置 / Account Settings</span>
                </div>
            </template>
            <el-form label-position="left" label-width="220px">
                <el-form-item label="修改密码 / Change Password:">
                    <el-button @click="showPasswordDialog = true" type="primary" plain size="small">修改 / Change</el-button>
                </el-form-item>
            </el-form>
            <!-- TODO: 添加用户名/邮箱修改 (如果需要) / Add username/email change (if needed) -->
        </el-card>

        <!-- 全局 Cookies 设置 -->
        <!-- Global Cookies Settings -->
        <el-card class="box-card" shadow="never">
            <template #header>
                <div class="card-header">
                    <span>全局 Cookies 设置 / Global Cookies Settings</span>
                </div>
            </template>
            <p class="form-tip">
                为特定网站设置全局 Cookies 文件路径。单个链接中设置的 Cookies 路径将优先于此处的全局设置。路径相对于项目根目录。
                <br />
                Set global cookies file paths for specific websites. Cookies path set in individual links will override
                global
                settings here. Paths are relative to the project root.
            </p>
            <el-form label-position="top" style="margin-top: 15px;">
                <el-form-item v-for="(path, site) in siteCookies" :key="site" :label="`${site} Cookies Path:`">
                    <el-input v-model="siteCookies[site]" :placeholder="`例如: backend/${site}_cookies.txt`" style="max-width: 400px;" />
                    <el-button type="danger" plain size="small" @click="removeSiteCookie(site)" style="margin-left: 10px;">移除 / Remove</el-button>
                </el-form-item>
                <el-form-item label="添加新网站 / Add New Site:">
                    <el-space wrap :size="10">
                        <el-input v-model="newSiteName" placeholder="网站域名 (小写, 例如 weibo.com) / Site domain (lowercase, e.g., weibo.com)" style="width: 250px;" />
                        <el-input v-model="newSiteCookiePath" placeholder="Cookies 文件路径 / Cookies file path" style="min-width: 250px; flex-grow: 1;" />
                        <el-button type="success" plain @click="addSiteCookie" :disabled="!newSiteName || !newSiteCookiePath">添加 / Add</el-button>
                    </el-space>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="saveSiteCookies" :loading="savingCookies">保存全局 Cookies / Save
                        Global
                        Cookies</el-button>
                </el-form-item>
                <el-alert v-if="cookiesError" :title="cookiesError" type="error" show-icon closable
                    @close="cookiesError = null" />
                <el-alert v-if="cookiesSuccess" title="全局 Cookies 保存成功 / Global Cookies saved successfully!"
                    type="success" show-icon closable @close="cookiesSuccess = false" />
            </el-form>
        </el-card>


        <!-- TODO: 添加下载设置 / Add Download Settings (e.g., MEDIA_ROOT, default options) -->
        <!-- TODO: 添加任务调度设置 / Add Task Scheduling Settings -->

        <!-- 修改密码对话框 -->
        <!-- Change Password Dialog -->
        <el-dialog v-model="showPasswordDialog" title="修改密码 / Change Password" width="400px"
            :close-on-click-modal="false">
            <el-form ref="passwordFormRef" :model="passwordData" :rules="passwordRules" label-position="top">
                <el-form-item label="当前密码 / Current Password" prop="currentPassword">
                    <el-input type="password" v-model="passwordData.currentPassword" show-password required />
                </el-form-item>
                <el-form-item label="新密码 / New Password" prop="newPassword">
                    <el-input type="password" v-model="passwordData.newPassword" show-password required />
                </el-form-item>
                <el-form-item label="确认新密码 / Confirm New Password" prop="confirmPassword">
                    <el-input type="password" v-model="passwordData.confirmPassword" show-password required />
                </el-form-item>
                <el-alert v-if="passwordError" :title="passwordError" type="error" show-icon closable
                    @close="passwordError = null" />
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="showPasswordDialog = false">取消 / Cancel</el-button>
                    <el-button type="primary" @click="changePassword" :loading="passwordSubmitting">
                        确认修改 / Confirm Change
                    </el-button>
                </span>
            </template>
        </el-dialog>

    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
// 确保导入所有使用的 Element Plus 组件 / Ensure all used Element Plus components are imported
import { ElCard, ElButton, ElDialog, ElForm, ElFormItem, ElInput, ElAlert, ElMessageBox, ElSpace, ElText } from 'element-plus';

const authStore = useAuthStore(); // 认证状态管理 / Authentication state management

// --- Database Import/Export State / 数据库导入/导出状态 ---
const exporting = ref(false); // Exporting state / 导出状态
const exportError = ref(null); // Export error message / 导出错误信息
const importing = ref(false); // Importing state / 导入状态
const importError = ref(null); // Import error flag / 导入错误标志
const importMessage = ref(null); // Import message (success or error detail) / 导入信息（成功或错误详情）
const selectedFile = ref(null); // Selected file for import / 选中的导入文件
const fileInputRef = ref(null); // Reference to the file input element / 文件输入元素的引用

// --- Change Password State / 修改密码状态 ---
const showPasswordDialog = ref(false); // Visibility of the password change dialog / 修改密码对话框的可见性
const passwordSubmitting = ref(false); // Password change submission state / 修改密码提交状态
const passwordError = ref(null); // Password change error message / 修改密码错误信息
const passwordFormRef = ref(null); // Reference to the password form element / 密码表单元素的引用
const passwordData = reactive({ // Password form data / 密码表单数据
    currentPassword: '', // Current password / 当前密码
    newPassword: '', // New password / 新密码
    confirmPassword: '' // Confirm new password / 确认新密码
});

// --- Global Cookies State / 全局 Cookies 状态 ---
const siteCookies = ref({}); // Stores site domain to cookies file path mapping / 存储网站域名到 Cookies 文件路径的映射
const savingCookies = ref(false); // Saving cookies state / 保存 Cookies 状态
const cookiesError = ref(null); // Cookies saving error message / Cookies 保存错误信息
const cookiesSuccess = ref(false); // Cookies saving success flag / Cookies 保存成功标志
const newSiteName = ref(''); // Input for new site domain / 新网站域名的输入
const newSiteCookiePath = ref(''); // Input for new site cookies path / 新网站 Cookies 路径的输入

// --- Password Form Validation Rules / 密码表单验证规则 ---
const validateConfirmPassword = (rule, value, callback) => {
    if (value === '') {
        callback(new Error('请再次输入新密码 / Please confirm your new password'));
    } else if (value !== passwordData.newPassword) {
        callback(new Error("两次输入的新密码不一致 / New passwords do not match!"));
    } else {
        callback();
    }
};
const passwordRules = {
    currentPassword: [{ required: true, message: '请输入当前密码 / Please enter current password', trigger: 'blur' }],
    newPassword: [
        { required: true, message: '请输入新密码 / Please enter new password', trigger: 'blur' },
        { min: 8, message: '密码长度不能少于 8 位 / Password must be at least 8 characters', trigger: 'blur' }
    ],
    confirmPassword: [
        { required: true, message: '请确认新密码 / Please confirm new password', trigger: 'blur' },
        { validator: validateConfirmPassword, trigger: 'blur' }
    ]
};


// --- Methods / 方法 ---
// Export database / 导出数据库
const exportDatabase = async () => {
    exporting.value = true;
    exportError.value = null;
    try {
        const response = await axios.get('/api/v1/database/export', {
            responseType: 'blob', // Expect a blob response for file download / 期望 blob 响应用于文件下载
            headers: { Authorization: `Bearer ${authStore.token}` } // 需要认证 / Requires authentication
        });
        // Create a download link / 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        // Extract filename from Content-Disposition header / 从 Content-Disposition 头部提取文件名
        const contentDisposition = response.headers['content-disposition'];
        let filename = 'database_backup.sql'; // Default filename / 默认文件名
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
            if (filenameMatch && filenameMatch.length === 2)
                filename = filenameMatch[1];
        }
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url); // Clean up the URL object / 清理 URL 对象
    } catch (error) {
        console.error('Database export failed:', error);
        exportError.value = error.response?.data?.detail || error.message || 'Database export failed.';
    } finally {
        exporting.value = false;
    }
};

// Trigger the hidden file input click / 触发隐藏的文件输入点击
const triggerFileInput = () => {
    fileInputRef.value?.click();
};

// Handle file selection for import / 处理导入文件的选择
const handleFileChange = (event) => {
    selectedFile.value = event.target.files[0];
    importMessage.value = null; // Clear previous messages / 清除之前的消息
    importError.value = null;
};

// Import database / 导入数据库
const importDatabase = async () => {
    if (!selectedFile.value) return; // Do nothing if no file is selected / 如果没有选择文件则不执行任何操作

    // Show confirmation dialog before importing / 导入前显示确认对话框
    try {
        await ElMessageBox.confirm(
            '确定要导入数据库吗？这将覆盖所有当前数据！/ Are you sure you want to import the database? This will overwrite all current data!',
            '确认导入 / Confirm Import',
            { confirmButtonText: '确认导入 / Confirm', cancelButtonText: '取消 / Cancel', type: 'warning' }
        );
    } catch {
        console.log('Import cancelled');
        return; // User cancelled / 用户取消
    }

    importing.value = true;
    importError.value = null;
    importMessage.value = null;
    const formData = new FormData();
    formData.append('file', selectedFile.value); // Append the selected file to form data / 将选中的文件添加到表单数据

    try {
        const response = await axios.post('/api/v1/database/import', formData, {
            headers: {
                'Content-Type': 'multipart/form-data', // Required for file uploads / 文件上传必需
                Authorization: `Bearer ${authStore.token}` // 需要认证 / Requires authentication
            }
        });
        importMessage.value = response.data.message || 'Import started in background.'; // Display success message / 显示成功消息
        selectedFile.value = null; // Clear selected file state / 清空选中的文件状态
        if (fileInputRef.value) fileInputRef.value.value = ''; // Clear file input element value / 清空文件输入元素的值
    } catch (error) {
        console.error('Database import failed:', error);
        importError.value = true; // Set error flag / 设置错误标志
        importMessage.value = error.response?.data?.detail || error.message || 'Database import failed.'; // Display error message / 显示错误消息
    } finally {
        importing.value = false;
    }
};

// Change user password / 修改用户密码
const changePassword = async () => {
    if (!passwordFormRef.value) return; // Ensure form reference is available / 确保表单引用可用
    // Validate the form before submitting / 提交前验证表单
    await passwordFormRef.value.validate(async (valid) => {
        if (valid) {
            passwordSubmitting.value = true;
            passwordError.value = null;
            try {
                // Call backend API to change password / 调用后端修改密码的 API
                const response = await axios.put('/api/v1/users/me/password', {
                    current_password: passwordData.currentPassword,
                    new_password: passwordData.newPassword
                }, {
                    headers: { Authorization: `Bearer ${authStore.token}` } // 需要认证 / Requires authentication
                });

                // Show success message and close dialog / 显示成功消息并关闭对话框
                ElMessageBox.alert('密码修改成功 / Password changed successfully.', 'Success', { type: 'success' });
                showPasswordDialog.value = false;
                // Clear form / 清空表单
                passwordData.currentPassword = '';
                passwordData.newPassword = '';
                passwordData.confirmPassword = '';

            } catch (error) {
                console.error('Failed to change password:', error);
                passwordError.value = error.response?.data?.detail || error.message || 'Failed to change password.'; // Display error message / 显示错误消息
            } finally {
                passwordSubmitting.value = false;
            }
        } else {
            console.log('Password form validation failed');
            return false; // Validation failed / 验证失败
        }
    });
};

// --- Cookies Related Methods / Cookies 相关方法 ---
// Fetch global site cookies settings / 获取全局网站 Cookies 设置
const fetchSiteCookies = async () => {
    cookiesError.value = null; // Clear previous error / 清除之前的错误
    try {
        // Call backend API to get global Cookies settings / 调用后端 API 获取全局 Cookies 设置
        const response = await axios.get('/api/v1/settings/cookies', {
            headers: { Authorization: `Bearer ${authStore.token}` } // 需要认证 / Requires authentication
        });
        siteCookies.value = response.data; // Update state with fetched data / 使用获取的数据更新状态
    } catch (error) {
        console.error('Failed to fetch site cookies:', error);
        cookiesError.value = error.response?.data?.detail || error.message || 'Failed to fetch site cookies.'; // Display error message / 显示错误消息
    }
};

// Add a new site cookie entry / 添加新的网站 Cookie 条目
const addSiteCookie = () => {
    const site = newSiteName.value.trim().toLowerCase(); // Get and format site name / 获取并格式化网站名称
    const path = newSiteCookiePath.value.trim(); // Get cookies path / 获取 Cookies 路径
    if (site && path) {
        siteCookies.value[site] = path; // Add/update the entry / 添加/更新条目
        newSiteName.value = ''; // Clear input fields / 清空输入字段
        newSiteCookiePath.value = '';
    }
};

// Remove a site cookie entry / 移除网站 Cookie 条目
const removeSiteCookie = (site) => {
    delete siteCookies.value[site]; // Delete the entry / 删除条目
};

// Save global site cookies settings / 保存全局网站 Cookies 设置
const saveSiteCookies = async () => {
    savingCookies.value = true;
    cookiesError.value = null;
    cookiesSuccess.value = false;
    try {
        // Call backend API to save global Cookies settings / 调用后端 API 保存全局 Cookies 设置
        const response = await axios.put('/api/v1/settings/cookies', { site_cookies: siteCookies.value }, {
            headers: { Authorization: `Bearer ${authStore.token}` } // 需要认证 / Requires authentication
        });
        cookiesSuccess.value = true; // Set success flag / 设置成功标志
        setTimeout(() => cookiesSuccess.value = false, 3000); // Hide success message after 3s / 3 秒后隐藏成功提示

    } catch (error) {
        console.error('Failed to save site cookies:', error);
        cookiesError.value = error.response?.data?.detail || error.message || 'Failed to save site cookies.'; // Display error message / 显示错误消息
    } finally {
        savingCookies.value = false;
    }
};

// Fetch cookies settings when component mounts / 组件挂载时获取 Cookies 设置
onMounted(() => {
    fetchSiteCookies();
});

</script>

<style scoped>
.settings-view {
    padding: 20px;
    max-width: 800px;
    margin: 0 auto;
}

.box-card {
    margin-bottom: 20px;
}

.card-header span {
    font-weight: bold;
}

/* Removed .setting-item and related label styling as el-form-item is used */

.file-name {
    /* margin-left: 10px; Handled by el-space */
    font-style: italic;
    /* color: #606266; /* ElText default or type will handle */
}

/* Removed .warning-message, .error-message, .success-message as el-text or el-alert are used */

.form-tip {
    font-size: 0.8em;
    color: #909399;
    line-height: 1.2;
    margin-top: 4px;
}

.el-alert {
    margin-bottom: 15px;
}
</style>
