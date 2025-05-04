<script setup>
import DefaultLayout from '@/layouts/DefaultLayout.vue'; // 导入布局组件 / Import layout component
// 可以根据路由元信息决定使用哪个布局 / Can decide which layout to use based on route meta info
</script>

<template>
  <!-- 使用默认布局包裹整个应用 -->
  <!-- Wrap the entire application with the default layout -->
  <DefaultLayout>
    <!-- <router-view /> 会被渲染在 DefaultLayout 的 <main> 区域 -->
    <!-- <router-view /> will be rendered in the <main> area of DefaultLayout -->
  </DefaultLayout>
</template>

<style>
/* 全局样式可以保留或移到单独的文件 */
/* Global styles can be kept here or moved to a separate file */
body {
  margin: 0;
  /* 移除 body 的默认 margin / Remove default body margin */
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  /* text-align: center; */
  /* 布局组件会处理对齐 / Layout component handles alignment */
  /* margin-top: 60px; */
  /* 布局组件会处理边距 / Layout component handles margin */
}
</style>
