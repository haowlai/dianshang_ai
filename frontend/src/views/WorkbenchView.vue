<template>
  <div class="workbench-view">
    <h2>Agent 可观测工作台 (Workbench)</h2>
    <div class="workbench-layout">
      <DagGraph />
      <NodeDetail />
      <PromptViewer />
      <IoViewer />
    </div>
  </div>
</template>

<script setup lang="ts">
import DagGraph from '@/components/workbench/DagGraph.vue'
import NodeDetail from '@/components/workbench/NodeDetail.vue'
import PromptViewer from '@/components/workbench/PromptViewer.vue'
import IoViewer from '@/components/workbench/IoViewer.vue'
</script>

<style scoped>
.workbench-view { padding: 24px; }
.workbench-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
</style>
