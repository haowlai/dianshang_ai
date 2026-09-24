<template>
  <div class="sku-page">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">商品 SKU 资产库</h1>
        <p class="page-desc">维护出海选品基础规格、特征卖点与设计参考图</p>
      </div>
      <div class="actions">
        <button class="btn btn-primary" @click="showCreateModal = true">+ 录入新商品 SKU</button>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="card filter-bar mb-4">
      <div class="filter-group">
        <label>关键词搜索:</label>
        <input type="text" v-model="searchQ" class="form-input" placeholder="输入编码或名称" @keyup.enter="loadSkus" />
      </div>
      <div class="filter-group">
        <label>类目分类:</label>
        <select v-model="selectedCategory" class="form-select" @change="loadSkus">
          <option value="">全部类目</option>
          <option value="户外运动">户外运动</option>
          <option value="数码配件">数码配件</option>
          <option value="家居生活">家居生活</option>
        </select>
      </div>
      <button class="btn btn-secondary btn-sm" @click="loadSkus">搜索过滤</button>
    </div>

    <!-- SKU 卡片栅格 -->
    <div class="sku-grid">
      <div v-for="s in skus" :key="s.id" class="sku-card card">
        <div class="sku-media">
          <img :src="s.images?.[0] || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600'" class="sku-img" />
          <span class="category-tag">{{ s.category }}</span>
        </div>
        <div class="sku-content">
          <div class="sku-code-row">
            <code class="code-pill">{{ s.code }}</code>
          </div>
          <h3 class="sku-title">{{ s.name }}</h3>
          <p class="sku-desc">{{ s.description }}</p>

          <div class="specs-box mt-2">
            <div v-for="(v, k) in s.specs" :key="k" class="spec-row">
              <span class="spec-k">{{ k }}:</span>
              <span class="spec-v">{{ v }}</span>
            </div>
          </div>
        </div>
        <div class="sku-card-actions mt-3">
          <button class="btn btn-primary btn-sm full-width" @click="generateForSku(s.id)">⚡ 发起 7-Agent 生成</button>
        </div>
      </div>
    </div>

    <!-- 录入新 SKU 弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <h3 class="modal-title mb-4">录入新商品 SKU</h3>
        <div class="form-group">
          <label class="form-label">商品编码 (SKU Code)</label>
          <input type="text" v-model="form.code" class="form-input" placeholder="例如: SKU-2026-TENT03" />
        </div>
        <div class="form-group">
          <label class="form-label">商品名称</label>
          <input type="text" v-model="form.name" class="form-input" placeholder="例如: 极简防风双人户外露营帐篷" />
        </div>
        <div class="form-group">
          <label class="form-label">类目分类</label>
          <select v-model="form.category" class="form-select">
            <option value="户外运动">户外运动</option>
            <option value="数码配件">数码配件</option>
            <option value="家居生活">家居生活</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">商品核心卖点与背景描述</label>
          <textarea v-model="form.description" class="form-textarea" rows="3" placeholder="描述材质、设计亮点、防水等级等"></textarea>
        </div>
        <div class="modal-footer mt-4">
          <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn btn-primary" @click="submitCreateSku">保存入库</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'

const router = useRouter()
const skus = ref<any[]>([])
const searchQ = ref('')
const selectedCategory = ref('')
const showCreateModal = ref(false)

const form = ref({
  code: '',
  name: '',
  category: '户外运动',
  description: '',
  specs: { "材质": "高强度复合材料", "重量": "1.5kg" },
  images: ["https://images.unsplash.com/photo-1510312305653-8ed496efae75?w=800"]
})

async function loadSkus() {
  try {
    let url = '/skus?page=1&page_size=50'
    if (searchQ.value) url += `&q=${searchQ.value}`
    if (selectedCategory.value) url += `&category=${selectedCategory.value}`
    const res = await client.get(url)
    skus.value = res.data?.data?.items || []
  } catch (e) {
    console.error(e)
  }
}

async function submitCreateSku() {
  if (!form.value.code || !form.value.name) {
    alert('请填写编码与商品名称')
    return
  }
  try {
    await client.post('/skus', form.value)
    showCreateModal.value = false
    alert('SKU 创建成功！')
    loadSkus()
  } catch (e) {
    alert('创建失败，编码可能已存在')
  }
}

async function generateForSku(skuId: string) {
  try {
    const res = await client.post('/tasks', {
      sku_id: skuId,
      config: { platform: 'amazon', language: 'en', max_retries: 2 }
    })
    const taskId = res.data?.data?.task_id
    alert('任务已发起，正在转入 7-Agent 工作台！')
    router.push(`/workbench/${taskId}`)
  } catch (e) {
    alert('发起失败')
  }
}

onMounted(() => {
  loadSkus()
})
</script>

<style scoped>
.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-title { font-size: 22px; font-weight: 700; }
.page-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.sku-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.sku-card {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}
.sku-media {
  position: relative;
  height: 180px;
  overflow: hidden;
}
.sku-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.category-tag {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(15, 23, 42, 0.75);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}
.sku-content {
  padding: 16px;
  flex: 1;
}
.sku-code-row { margin-bottom: 6px; }
.code-pill { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 11.5px; }
.sku-title { font-size: 15px; font-weight: 600; margin-bottom: 6px; }
.sku-desc { font-size: 12px; color: var(--text-muted); line-height: 1.4; max-height: 38px; overflow: hidden; }

.specs-box {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 11.5px;
}
.spec-row { display: flex; justify-content: space-between; margin-bottom: 2px; }
.spec-k { color: var(--text-light); }
.spec-v { font-weight: 500; }

.sku-card-actions { padding: 0 16px 16px; }
.full-width { width: 100%; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; }
</style>
