<template>
    <div class="history-view">
        <h2>历史记录 / History</h2>

        <div class="toolbar">
            <el-input v-model="filterLinkID" placeholder="过滤链接 ID / Filter Link ID"
                style="width: 150px; margin-right: 10px;" clearable />
            <el-select v-model="filterStatus" placeholder="过滤状态 / Filter Status"
                style="width: 150px; margin-right: 10px;" clearable>
                <el-option label="成功 / Success" value="success"></el-option>
                <el-option label="失败 / Failed" value="failed"></el-option>
                <!-- Add other relevant statuses if needed -->
            </el-select>
            <el-button @click="applyFilter">过滤 / Filter</el-button>
            <el-button @click="refreshHistory" :loading="historyStore.loadingStatus">刷新 / Refresh</el-button>
        </div>

        <el-alert v-if="historyStore.error" :title="historyStore.error" type="error" show-icon closable />

        <el-table :data="historyStore.logs" v-loading="historyStore.loadingStatus" style="width: 100%" stripe border>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="timestamp" label="时间戳 / Timestamp" width="180" :formatter="formatDate" sortable />
            <el-table-column prop="link_id" label="链接 ID / Link ID" width="100" />
            <!-- 可以添加一列显示链接名称 (需要关联查询或前端处理) / Can add column for link name (needs join query or frontend handling) -->
            <el-table-column prop="status" label="状态 / Status" width="100">
                <template #default="scope">
                    <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                        {{ scope.row.status }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="downloaded_files" label="下载文件 / Downloaded Files" min-width="250">
                <template #default="scope">
                    <ul v-if="scope.row.downloaded_files && scope.row.downloaded_files.length > 0">
                        <li v-for="(file, index) in scope.row.downloaded_files" :key="index" class="file-path">
                            {{ file }}
                        </li>
                    </ul>
                    <span v-else>-</span>
                </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息 / Error Message" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作 / Actions" width="100" fixed="right">
                <template #default="scope">
                    <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除 / Delete</el-button>
                </template>
            </el-table-column>
            <!-- TODO: 添加显示 details 的列 / Add column to show details -->
        </el-table>
        <!-- TODO: 添加分页 / Add pagination -->
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'; // 导入 ref / Import ref
import { ElTable, ElTableColumn, ElButton, ElTag, ElAlert, ElMessageBox, ElInput, ElSelect, ElOption } from 'element-plus'; // 导入工具栏组件 / Import toolbar components
import { useHistoryStore } from '@/stores/history';

const historyStore = useHistoryStore();

const filterLinkID = ref(null); // 过滤链接 ID / Filter Link ID
const filterStatus = ref(null); // 过滤状态 / Filter Status

onMounted(() => {
    historyStore.fetchHistory();
});

const refreshHistory = () => {
    // Reset filters when refreshing from the button
    filterLinkID.value = null;
    filterStatus.value = null;
    historyStore.fetchHistory();
};

const applyFilter = () => {
    const params = {};
    if (filterLinkID.value) {
        params.link_id = filterLinkID.value;
    }
    if (filterStatus.value) {
        params.status = filterStatus.value;
    }
    historyStore.fetchHistory(params);
};

const formatDate = (row, column, cellValue, index) => {
    if (!cellValue) return '';
    try {
        return new Date(cellValue).toLocaleString();
    } catch (e) {
        return cellValue;
    }
};

const handleDelete = async (log) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除这条历史记录 (ID: ${log.id}) 吗？/ Are you sure you want to delete this history log (ID: ${log.id})?`,
            '确认删除 / Confirm Deletion',
            {
                confirmButtonText: '删除 / Delete',
                cancelButtonText: '取消 / Cancel',
                type: 'warning',
            }
        );
        const success = await historyStore.deleteHistoryLog(log.id);
        if (success) {
            ElMessageBox.alert('历史记录已删除 / History log deleted.', 'Success', { type: 'success' });
        } else {
            ElMessageBox.alert(`删除历史记录失败: ${historyStore.error}`, 'Error', { type: 'error' });
        }
    } catch (e) {
        console.log('Deletion cancelled');
    }
};
</script>

<style scoped>
.history-view {
    padding: 20px;
}

.toolbar {
    margin-bottom: 15px;
    text-align: right;
}

.el-table {
    margin-top: 15px;
}

ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.file-path {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.4;
}
</style>
