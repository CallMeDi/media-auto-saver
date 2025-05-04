<template>
    <el-dialog :model-value="props.modelValue" :title="isEditMode ? '编辑链接 / Edit Link' : '添加链接 / Add Link'"
        width="600px" @close="closeDialog" :close-on-click-modal="false">
        <el-form ref="linkFormRef" :model="formData" :rules="rules" label-width="120px" label-position="top">
            <el-form-item label="URL" prop="url">
                <el-input v-model="formData.url" placeholder="请输入链接 URL / Enter link URL" />
            </el-form-item>
            <el-form-item label="名称 / Name" prop="name">
                <el-input v-model="formData.name" placeholder="可选, 留空将尝试自动获取 / Optional, leave blank to auto-fetch" />
            </el-form-item>
            <el-form-item label="类型 / Type" prop="link_type">
                <el-radio-group v-model="formData.link_type">
                    <el-radio label="creator">创作者 / Creator</el-radio>
                    <el-radio label="live">直播 / Live</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item label="描述 / Description" prop="description">
                <el-input type="textarea" v-model="formData.description" placeholder="可选 / Optional" />
            </el-form-item>
            <el-form-item label="标签 / Tags" prop="tags">
                <el-input v-model="formData.tags" placeholder="可选, 逗号分隔 / Optional, comma-separated" />
            </el-form-item>
            <el-form-item label="Cookies 文件路径 / Cookies File Path" prop="cookies_path">
                <el-input v-model="formData.cookies_path"
                    placeholder="可选, 用于需要登录的网站 / Optional, for sites requiring login" />
                <div class="form-tip">例如: backend/weibo_cookies.txt / e.g., backend/weibo_cookies.txt</div>
            </el-form-item>
            <el-form-item label="启用监控 / Enable Monitoring" prop="is_enabled">
                <el-switch v-model="formData.is_enabled" />
            </el-form-item>
            <!-- TODO: 添加更多设置字段 (settings) / Add more setting fields -->
            <el-alert v-if="submitError" :title="submitError" type="error" show-icon closable
                @close="submitError = null" />
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="closeDialog">取消 / Cancel</el-button>
                <el-button type="primary" @click="submitForm" :loading="submitting">
                    {{ submitting ? '提交中...' : (isEditMode ? '更新 / Update' : '添加 / Add') }}
                </el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue';
import { ElDialog, ElForm, ElFormItem, ElInput, ElButton, ElRadioGroup, ElRadio, ElSwitch, ElAlert } from 'element-plus';
import { useLinkStore } from '@/stores/link';

const props = defineProps({
    modelValue: Boolean, // 控制对话框显示/隐藏 / Controls dialog visibility (v-model)
    linkData: { // 用于编辑模式的初始数据 / Initial data for edit mode
        type: Object,
        default: null
    }
});

const emit = defineEmits(['update:modelValue', 'submitted']); // 定义事件 / Define events

const linkStore = useLinkStore();
const linkFormRef = ref(null); // 表单引用 / Form reference
const submitting = ref(false);
const submitError = ref(null);

// 表单数据 / Form data
const formData = ref({
    url: '',
    name: '',
    link_type: 'creator',
    description: '',
    tags: '',
    cookies_path: '',
    is_enabled: true,
    settings: {} // 暂时为空 / Empty for now
});

// 判断是否为编辑模式 / Determine if it's edit mode
const isEditMode = computed(() => !!props.linkData);

// 表单验证规则 / Form validation rules
const rules = ref({
    url: [
        { required: true, message: '请输入 URL / Please enter URL', trigger: 'blur' },
        { type: 'url', message: '请输入有效的 URL / Please enter a valid URL', trigger: ['blur', 'change'] }
    ],
    link_type: [
        { required: true, message: '请选择类型 / Please select type', trigger: 'change' }
    ]
});

// 监听 modelValue (控制显示) 和 linkData (编辑数据) 的变化
// Watch for changes in modelValue (visibility control) and linkData (edit data)
watch(() => props.modelValue, (newValue) => {
    if (newValue) {
        // 对话框打开时 / When dialog opens
        submitError.value = null; // 清除错误 / Clear error
        if (isEditMode.value) {
            // 编辑模式: 填充表单 / Edit mode: populate form
            formData.value = { ...props.linkData };
        } else {
            // 添加模式: 重置表单 / Add mode: reset form
            resetFormFields();
        }
        // 确保 DOM 更新后再重置验证状态 / Ensure DOM is updated before resetting validation state
        nextTick(() => {
            linkFormRef.value?.clearValidate();
        });
    }
});

const resetFormFields = () => {
    formData.value = {
        url: '',
        name: '',
        link_type: 'creator',
        description: '',
        tags: '',
        cookies_path: '',
        is_enabled: true,
        settings: {}
    };
};

const closeDialog = () => {
    emit('update:modelValue', false); // 更新 v-model / Update v-model
};

const submitForm = async () => {
    if (!linkFormRef.value) return;
    await linkFormRef.value.validate(async (valid) => {
        if (valid) {
            submitting.value = true;
            submitError.value = null;
            let success = false;
            let result = null;

            // 准备要发送的数据 (移除 ID, 如果是添加模式)
            // Prepare data to send (remove ID if in add mode)
            const dataToSend = { ...formData.value };
            if (!isEditMode.value) {
                delete dataToSend.id; // 添加时不需要 ID / No ID needed for adding
            }

            try {
                if (isEditMode.value) {
                    // 调用更新 API / Call update API
                    result = await linkStore.updateLink(props.linkData.id, dataToSend);
                } else {
                    // 调用添加 API / Call add API
                    result = await linkStore.addLink(dataToSend);
                }
                success = !!result; // 如果返回非 null 则认为成功 / Consider success if result is not null
            } catch (error) {
                // Store action 应该已经处理了错误, 但以防万一 / Store action should handle error, but just in case
                console.error("Submission error:", error);
                submitError.value = linkStore.error || "An unexpected error occurred.";
            } finally {
                submitting.value = false;
                if (success) {
                    emit('submitted'); // 发出成功事件 / Emit success event
                    closeDialog(); // 关闭对话框 / Close dialog
                } else {
                    // 如果 store action 返回 null, 使用 store 中的错误信息
                    // If store action returned null, use error message from store
                    if (!submitError.value) {
                        submitError.value = linkStore.error || "Submission failed.";
                    }
                }
            }
        } else {
            console.log('Form validation failed');
            return false;
        }
    });
};

</script>

<style scoped>
.dialog-footer button:first-child {
    margin-right: 10px;
}

.form-tip {
    font-size: 0.8em;
    color: #909399;
    line-height: 1.2;
}

.el-alert {
    margin-bottom: 15px;
    /* 在按钮上方留出空间 / Add space above buttons */
}
</style>
