<template>
    <div class="links-view">
        <h2>链接管理 / Link Management</h2>

        <el-row justify="end" class="toolbar">
            <el-space wrap>
                <el-button type="primary" @click="openAddDialog" :loading="linkStore.linkLoading[0]">添加链接 / Add Link</el-button>
                <el-button @click="refreshLinks" :loading="linkStore.isLoading">刷新 / Refresh</el-button>
                <el-input v-model="filterText" placeholder="过滤链接 (名称或URL) / Filter links (Name or URL)" style="width: 250px;" clearable />
                <el-button @click="applyFilter" :disabled="linkStore.isLoading">过滤 / Filter</el-button>
            </el-space>
        </el-row>

        <!-- 单个链接操作错误提示 -->
        <!-- Single link operation error messages -->
        <el-alert v-if="linkStore.error" :title="linkStore.error" type="error" show-icon closable style="margin-bottom: 15px;" />

        <el-table :data="linkStore.linkList" style="width: 100%" stripe border v-loading="linkStore.isLoading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称 / Name" min-width="150" show-overflow-tooltip />
            <el-table-column prop="url" label="URL" min-width="250" show-overflow-tooltip>
                <template #default="scope">
                    <a :href="scope.row.url" target="_blank" rel="noopener noreferrer">{{ scope.row.url }}</a>
                </template>
            </el-table-column>
            <el-table-column prop="link_type" label="类型 / Type" width="100">
                <template #default="scope">
                    <el-tag :type="scope.row.link_type === 'creator' ? 'success' : 'warning'">
                        {{ scope.row.link_type }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="site_name" label="网站 / Site" width="120" />
            <el-table-column prop="status" label="状态 / Status" width="120">
                <template #default="scope">
                    <el-tag :type="getStatusTagType(scope.row.status)">
                        {{ scope.row.status }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="tags" label="标签 / Tags" min-width="150" show-overflow-tooltip />
            <el-table-column prop="is_enabled" label="启用 / Enabled" width="80">
                <template #default="scope">
                    <el-switch v-model="scope.row.is_enabled" @change="toggleEnable(scope.row)" />
                </template>
            </el-table-column>
            <el-table-column label="操作 / Actions" width="250" fixed="right">
                <template #default="scope">
                    <el-button size="small" @click="handleEdit(scope.row)"
                        :loading="linkStore.linkLoading[scope.row.id]">编辑 / Edit</el-button>
                    <el-button size="small" type="primary" @click="handleManualTrigger(scope.row)"
                        :loading="linkStore.linkLoading[scope.row.id]">手动触发 / Manual
                        Trigger</el-button>
                    <el-button size="small" type="danger" @click="handleDelete(scope.row)"
                        :loading="linkStore.linkLoading[scope.row.id]">删除 / Delete</el-button>
                    <el-text v-if="linkStore.linkErrors[scope.row.id]" type="danger" size="small" class="link-error-display">
                        {{ linkStore.linkErrors[scope.row.id] }}
                    </el-text>
                </template>
            </el-table-column>
            <el-table-column prop="last_checked_at" label="上次检查 / Last Checked" width="160" :formatter="formatDate" />
            <el-table-column prop="last_success_at" label="上次成功 / Last Success" width="160" :formatter="formatDate" />
            <el-table-column prop="created_at" label="创建时间 / Created" width="160" :formatter="formatDate" />
        </el-table>

        <!-- 添加/编辑链接对话框 -->
        <!-- Add/Edit Link Dialog -->
        <LinkDialog v-model="showDialog" :link-data="editingLink" @submitted="refreshLinks" />

    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'; // 导入 computed / Import computed
import { 
    ElTable, ElTableColumn, ElButton, ElTag, ElSwitch, ElAlert, ElMessageBox, 
    ElInput, ElSpace, ElRow, ElCol, ElText 
} from 'element-plus';
import { useLinkStore } from '@/stores/link';
import LinkDialog from '@/components/LinkDialog.vue'; // 导入对话框组件 / Import dialog component

const linkStore = useLinkStore();
const showDialog = ref(false); // 通用对话框显示状态 / General dialog visibility state
const editingLink = ref(null); // 当前正在编辑的链接数据 / Data of the link being edited

// 计算属性判断是添加还是编辑模式 / Computed property to determine add or edit mode
const isEditMode = computed(() => !!editingLink.value);

// 组件挂载时获取链接列表 / Fetch links when component is mounted
onMounted(() => {
    linkStore.fetchLinks();
});

const refreshLinks = () => {
    linkStore.fetchLinks();
};

const filterText = ref(''); // 过滤文本 / Filter text

const applyFilter = () => {
    // 调用 fetchLinks 并传递 search 参数 / Call fetchLinks passing the search parameter
    linkStore.fetchLinks({ search: filterText.value });
};

const openAddDialog = () => {
    console.log("Opening Add Dialog..."); // 添加日志 / Add log
    editingLink.value = null; // 清空编辑数据, 进入添加模式 / Clear editing data, enter add mode
    showDialog.value = true;
};

const handleEdit = (link) => {
    editingLink.value = { ...link }; // 复制数据以避免直接修改 store / Copy data to avoid direct store modification
    showDialog.value = true; // 打开同一个对话框 / Open the same dialog
};


const getStatusTagType = (status) => {
    switch (status) {
        case 'idle': return 'info';
        case 'monitoring': return 'primary';
        case 'downloading': return 'warning';
        case 'recording': return 'warning';
        case 'error': return 'danger';
        // case 'disabled': return 'info'; // Removed status
        default: return 'info';
    }
};

const formatDate = (row, column, cellValue, index) => {
    if (!cellValue) return '';
    try {
        return new Date(cellValue).toLocaleString();
    } catch (e) {
        return cellValue; // 返回原始值如果格式化失败 / Return original value if formatting fails
    }
};

const toggleEnable = async (link) => {
    // 乐观更新 UI / Optimistic UI update
    // const originalState = link.is_enabled;
    // link.is_enabled = !originalState; // 这会直接修改 store 中的状态, 可能需要更谨慎处理 / This directly modifies store state, might need careful handling

    await linkStore.updateLink(link.id, { is_enabled: link.is_enabled });
    if (linkStore.error) {
        // 如果更新失败, 恢复状态 (需要更复杂的逻辑来处理)
        // If update fails, revert state (needs more complex logic)
        // link.is_enabled = originalState;
        ElMessageBox.alert(`Failed to update status for link ${link.id}: ${linkStore.error}`, 'Error', { type: 'error' });
        // 手动刷新以获取正确状态 / Manually refresh to get correct state
        refreshLinks();
    }
};


const handleDelete = async (link) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除链接 "${link.name || link.url}" 吗？这将同时删除其所有历史记录。/ Are you sure you want to delete link "${link.name || link.url}"? This will also delete all its history.`,
            '确认删除 / Confirm Deletion',
            {
                confirmButtonText: '删除 / Delete',
                cancelButtonText: '取消 / Cancel',
                type: 'warning',
            }
        );
        // 后端 API 会自动删除关联的历史记录 / Backend API automatically deletes associated history
        // console.warn(`History deletion for link ${link.id} not implemented yet.`); // 注释掉或移除 / Comment out or remove
        // 再删除链接 / Then delete the link
        const success = await linkStore.deleteLink(link.id);
        if (success) {
            ElMessageBox.alert('链接已删除 / Link deleted.', 'Success', { type: 'success' });
        } else {
            ElMessageBox.alert(`删除链接失败: ${linkStore.error}`, 'Error', { type: 'error' });
        }
    } catch (e) {
        // 用户取消 / User cancelled
        console.log('Deletion cancelled');
    }
};

const handleManualTrigger = async (link) => {
    console.log("Manually triggering link:", link.id);
    await linkStore.triggerLinkTask(link.id);
    // Optionally refresh the list after triggering to see status changes
    // refreshLinks();
};

</script>

<style scoped>
.links-view {
    padding: 20px;
}

.toolbar {
    margin-bottom: 15px;
    /* text-align: right; removed, handled by el-row justify="end" */
}

.el-table {
    margin-top: 15px; /* Retained for spacing under toolbar/alert */
}

.link-error-display {
    display: block; /* Make it take its own line */
    margin-top: 5px; /* Add some space above the error message */
}

a {
    color: var(--el-color-primary); /* Use Element Plus primary color for links */
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
    color: var(--el-color-primary-light-3); /* Slightly lighter on hover */
}
</style>
