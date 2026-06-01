<template>
  <div class="monitor-dashboard">
    <!-- 刷新频率控制器 -->
    <div class="refresh-bar">
      <span class="refresh-label">数据刷新频率:</span>
      <el-select
        v-model="refreshInterval"
        @change="handleIntervalChange"
        style="width: 140px"
        size="small"
      >
        <el-option label="极速 (0.1秒)" :value="100" />
        <el-option label="高频 (1秒)" :value="1000" />
        <el-option label="快速 (3秒)" :value="3000" />
        <el-option label="标准 (5秒)" :value="5000" />
        <el-option label="平缓 (10秒)" :value="10000" />
        <el-option label="暂停刷新" :value="0" />
      </el-select>
    </div>

    <!-- 第一行：核心资源卡片（带 sparkline） -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="grafana-stat-card" :style="{ borderTop: '3px solid ' + cpuColor }">
          <div class="stat-label">CPU 使用率</div>
          <div class="stat-value-wrap">
            <span class="stat-big-num" :style="{ color: cpuColor }">{{
              monitorData.cpu?.percent ?? '--'
            }}</span>
            <span class="stat-unit">%</span>
          </div>
          <div class="stat-sparkline" ref="cpuSparkRef"></div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="grafana-stat-card" :style="{ borderTop: '3px solid ' + memColor }">
          <div class="stat-label">内存使用率</div>
          <div class="stat-value-wrap">
            <span class="stat-big-num" :style="{ color: memColor }">{{
              monitorData.memory?.percent ?? '--'
            }}</span>
            <span class="stat-unit">%</span>
          </div>
          <div class="stat-detail">
            {{ monitorData.memory?.used_gb ?? '--' }} /
            {{ monitorData.memory?.total_gb ?? '--' }} GB
          </div>
          <div class="stat-sparkline" ref="memSparkRef"></div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="grafana-stat-card" :style="{ borderTop: '3px solid ' + diskCColor }">
          <div class="stat-label">磁盘 C: 使用率</div>
          <div class="stat-value-wrap">
            <span class="stat-big-num" :style="{ color: diskCColor }">{{
              monitorData.disk_c?.percent ?? '--'
            }}</span>
            <span class="stat-unit">%</span>
          </div>
          <div class="stat-detail">
            {{ monitorData.disk_c?.used_gb ?? '--' }} /
            {{ monitorData.disk_c?.total_gb ?? '--' }} GB
          </div>
          <div class="stat-sparkline" ref="diskCSparkRef"></div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="grafana-stat-card" :style="{ borderTop: '3px solid ' + diskDColor }">
          <div class="stat-label">磁盘 D: 使用率</div>
          <div class="stat-value-wrap">
            <span class="stat-big-num" :style="{ color: diskDColor }">{{
              monitorData.disk_d?.percent ?? '--'
            }}</span>
            <span class="stat-unit">%</span>
          </div>
          <div class="stat-detail">
            {{ monitorData.disk_d?.used_gb ?? '--' }} /
            {{ monitorData.disk_d?.total_gb ?? '--' }} GB
          </div>
          <div class="stat-sparkline" ref="diskDSparkRef"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第二行：QPS / 活跃用户 / 网络 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="grafana-stat-card compact" style="border-top: 3px solid #ff6b6b">
          <div class="stat-label">API 实时 QPS</div>
          <div class="stat-value-wrap">
            <span class="stat-big-num" style="color: #ff6b6b">{{
              monitorData.qps ?? '--'
            }}</span>
            <span class="stat-unit">req/s</span>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="grafana-stat-card compact" style="border-top: 3px solid #feca57">
          <div class="stat-label">在线活跃用户 (15min)</div>
          <div class="stat-value-wrap">
            <span class="stat-big-num" style="color: #feca57">{{
              monitorData.active_users ?? '--'
            }}</span>
            <span class="stat-unit">人</span>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="grafana-stat-card compact" style="border-top: 3px solid #6c5ce7">
          <div class="stat-label">网络下载速率</div>
          <div class="stat-value-wrap">
            <span class="stat-big-num" style="color: #6c5ce7">{{
              networkDelta?.recv ?? '--'
            }}</span>
            <span class="stat-unit">KB/s</span>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="grafana-stat-card compact" style="border-top: 3px solid #00b894">
          <div class="stat-label">网络上传速率</div>
          <div class="stat-value-wrap">
            <span class="stat-big-num" style="color: #00b894">{{
              networkDelta?.sent ?? '--'
            }}</span>
            <span class="stat-unit">KB/s</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第三行：CPU + 内存趋势 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">CPU 负载趋势</span>
            <span class="panel-subtitle">{{
              refreshInterval > 0 ? `更新间隔 ${refreshInterval / 1000}s` : '已暂停刷新'
            }}</span>
          </div>
          <div class="panel-chart" ref="cpuChartRef"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">内存使用趋势</span>
            <span class="panel-subtitle">{{
              refreshInterval > 0 ? `更新间隔 ${refreshInterval / 1000}s` : '已暂停刷新'
            }}</span>
          </div>
          <div class="panel-chart" ref="memChartRef"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第四行：磁盘 I/O + 网络流量 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">磁盘 I/O 读写速率</span>
            <span class="panel-subtitle">KB/s</span>
          </div>
          <div class="panel-chart" ref="diskIOChartRef"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">网络流量实时速率</span>
            <span class="panel-subtitle">KB/s</span>
          </div>
          <div class="panel-chart" ref="netChartRef"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第五行：C 盘 + D 盘环形图 -->
    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">磁盘 C: 空间分布</span>
          </div>
          <div class="panel-chart panel-chart-sm" ref="diskCChartRef"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">磁盘 D: 空间分布</span>
          </div>
          <div class="panel-chart panel-chart-sm" ref="diskDChartRef"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 第六行：全站数据概览 Liquid Fill 水波球 -->
    <el-row :gutter="16">
      <el-col :xs="24" :sm="8" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">案件总数</span>
          </div>
          <div class="panel-chart panel-chart-sm" ref="caseLiquidRef"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">电子卷宗</span>
          </div>
          <div class="panel-chart panel-chart-sm" ref="volumeLiquidRef"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8" style="margin-bottom: 16px">
        <div class="grafana-panel">
          <div class="panel-header">
            <span class="panel-title">律师人数</span>
          </div>
          <div class="panel-chart panel-chart-sm" ref="lawyerLiquidRef"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import 'echarts-liquidfill'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const MAX_HISTORY = 30
const monitorData = ref({})
const siteStats = ref({ cases: 0, volumes: 0, lawyers: 0 })
const monitorTimer = ref(null)
const refreshInterval = ref(5000)
const history = ref({
  cpu: [],
  mem: [],
  disk_c: [],
  disk_d: [],
  recv: [],
  sent: [],
  disk_read: [],
  disk_write: [],
  timestamps: [],
})
const networkDelta = ref({ sent: 0, recv: 0 })
let prevNetwork = null

// 图表容器引用 (sparklines)
const cpuSparkRef = ref(null)
const memSparkRef = ref(null)
const diskCSparkRef = ref(null)
const diskDSparkRef = ref(null)
// 图表容器引用 (大图)
const cpuChartRef = ref(null)
const memChartRef = ref(null)
const diskIOChartRef = ref(null)
const netChartRef = ref(null)
const diskCChartRef = ref(null)
const diskDChartRef = ref(null)
// 图表容器引用 (水波球)
const caseLiquidRef = ref(null)
const volumeLiquidRef = ref(null)
const lawyerLiquidRef = ref(null)

// 图表实例
let cpuSparkChart = null
let memSparkChart = null
let diskCSparkChart = null
let diskDSparkChart = null
let cpuChart = null
let memChart = null
let diskIOChart = null
let netChart = null
let diskCChart = null
let diskDChart = null
let caseLiquidChart = null
let volumeLiquidChart = null
let lawyerLiquidChart = null

// 根据阈值返回颜色 (Grafana 风格: 绿 → 黄 → 红)
const cpuColor = computed(() => {
  const v = monitorData.value.cpu?.percent ?? 0
  if (v >= 90) return '#f56c6c'
  if (v >= 70) return '#e6a23c'
  return '#67c23a'
})
const memColor = computed(() => {
  const v = monitorData.value.memory?.percent ?? 0
  if (v >= 90) return '#f56c6c'
  if (v >= 70) return '#e6a23c'
  return '#67c23a'
})
const diskCColor = computed(() => {
  const v = monitorData.value.disk_c?.percent ?? 0
  if (v >= 90) return '#f56c6c'
  if (v >= 70) return '#e6a23c'
  return '#67c23a'
})
const diskDColor = computed(() => {
  const v = monitorData.value.disk_d?.percent ?? 0
  if (v >= 90) return '#f56c6c'
  if (v >= 70) return '#e6a23c'
  return '#67c23a'
})

/** 创建一个迷你 sparkline 的 ECharts 配置 */
function makeSparkOption(data, color) {
  return {
    grid: { top: 2, right: 2, bottom: 2, left: 2 },
    xAxis: { show: false, data: data.map((_, i) => i) },
    yAxis: { show: false, min: 0, max: 100 },
    series: [
      {
        type: 'line',
        data,
        smooth: true,
        symbol: 'none',
        lineStyle: { color, width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '40' },
            { offset: 1, color: color + '05' },
          ]),
        },
        animation: true,
      },
    ],
  }
}

/** 初始化顶部迷你 sparkline 图表（4 个核心资源卡片） */
function initSparkCharts() {
  const emptyOpt = makeSparkOption([0], '#909399')
  cpuSparkChart = echarts.init(cpuSparkRef.value)
  cpuSparkChart.setOption(emptyOpt)
  memSparkChart = echarts.init(memSparkRef.value)
  memSparkChart.setOption(emptyOpt)
  diskCSparkChart = echarts.init(diskCSparkRef.value)
  diskCSparkChart.setOption(emptyOpt)
  diskDSparkChart = echarts.init(diskDSparkRef.value)
  diskDSparkChart.setOption(emptyOpt)
}

/** 初始化 CPU 趋势大图 */
function initCpuChart() {
  cpuChart = echarts.init(cpuChartRef.value)
  cpuChart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v) => v + '%' },
    grid: { top: 10, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#a0a4b0', fontSize: 11 } },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#a0a4b0', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#2a2d35' } },
    },
    series: [
      {
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#67c23a', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103,194,58,0.3)' },
            { offset: 1, color: 'rgba(103,194,58,0.02)' },
          ]),
        },
        markLine: {
          silent: true,
          data: [
            { yAxis: 90, lineStyle: { color: '#f56c6c', type: 'dashed' } },
            { yAxis: 70, lineStyle: { color: '#e6a23c', type: 'dashed' } },
          ],
          symbol: 'none',
          label: { formatter: '{c}%' },
        },
      },
    ],
  })
}

/** 初始化内存趋势大图 */
function initMemChart() {
  memChart = echarts.init(memChartRef.value)
  memChart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v) => v + '%' },
    grid: { top: 10, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#a0a4b0', fontSize: 11 } },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#a0a4b0', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#2a2d35' } },
    },
    series: [
      {
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#409eff', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.3)' },
            { offset: 1, color: 'rgba(64,158,255,0.02)' },
          ]),
        },
        markLine: {
          silent: true,
          data: [
            { yAxis: 90, lineStyle: { color: '#f56c6c', type: 'dashed' } },
            { yAxis: 70, lineStyle: { color: '#e6a23c', type: 'dashed' } },
          ],
          symbol: 'none',
          label: { formatter: '{c}%' },
        },
      },
    ],
  })
}

/** 创建一个环形图配置 */
function makeDonutOption(used, free, usedColor) {
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} GB ({d}%)' },
    series: [
      {
        type: 'pie',
        radius: ['55%', '80%'],
        center: ['50%', '55%'],
        emphasis: { label: { fontSize: 18, fontWeight: 'bold' } },
        label: { show: false },
        data: [
          { value: used, name: '已用', itemStyle: { color: usedColor } },
          { value: free, name: '可用', itemStyle: { color: '#2a2d35' } },
        ],
      },
    ],
  }
}

/** 初始化磁盘 C: 环形图 */
function initDiskCChart() {
  diskCChart = echarts.init(diskCChartRef.value)
  diskCChart.setOption(makeDonutOption(0, 1, '#409eff'))
}

/** 初始化磁盘 D: 环形图 */
function initDiskDChart() {
  diskDChart = echarts.init(diskDChartRef.value)
  diskDChart.setOption(makeDonutOption(0, 1, '#409eff'))
}

/** 初始化磁盘 I/O 读写速率双线图 */
function initDiskIOChart() {
  diskIOChart = echarts.init(diskIOChartRef.value)
  diskIOChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['读取', '写入'], right: 10, textStyle: { color: '#a0a4b0', fontSize: 12 } },
    grid: { top: 30, right: 20, bottom: 30, left: 55 },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#a0a4b0', fontSize: 11 } },
    yAxis: {
      type: 'value',
      name: 'KB/s',
      nameTextStyle: { color: '#a0a4b0' },
      axisLabel: { color: '#a0a4b0' },
      splitLine: { lineStyle: { color: '#2a2d35' } },
    },
    series: [
      {
        name: '读取',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#ff6b6b', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255,107,107,0.3)' },
            { offset: 1, color: 'rgba(255,107,107,0.02)' },
          ]),
        },
      },
      {
        name: '写入',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#feca57', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(254,202,87,0.3)' },
            { offset: 1, color: 'rgba(254,202,87,0.02)' },
          ]),
        },
      },
    ],
  })
}

/** 初始化 3 个水波球 (Liquid Fill) 图表 */
function initLiquidCharts() {
  const makeLiquid = (color1, color2, defaultText) => ({
    series: [
      {
        type: 'liquidFill',
        data: [0],
        radius: '80%',
        center: ['50%', '52%'],
        color: [
          {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: color1 },
              { offset: 1, color: color2 },
            ],
          },
        ],
        backgroundStyle: { color: '#1a1c23' },
        outline: { show: false },
        shape: 'roundRect',
        amplitude: 6,
        waveLength: '80%',
        label: {
          show: true,
          color: '#d0d2d8',
          insideColor: '#ffffff',
          fontSize: 22,
          fontWeight: 'bold',
          formatter: defaultText,
        },
      },
    ],
  })

  caseLiquidChart = echarts.init(caseLiquidRef.value)
  caseLiquidChart.setOption(makeLiquid('#409eff', '#0050b3', '--\n案件'))

  volumeLiquidChart = echarts.init(volumeLiquidRef.value)
  volumeLiquidChart.setOption(makeLiquid('#13ce66', '#0d8a44', '--\n卷宗'))

  lawyerLiquidChart = echarts.init(lawyerLiquidRef.value)
  lawyerLiquidChart.setOption(makeLiquid('#6c5ce7', '#4a3db5', '--\n律师'))
}

/** 初始化网络流量趋势大图 (双线面积图) */
function initNetChart() {
  netChart = echarts.init(netChartRef.value)
  netChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['下载', '上传'], right: 10, textStyle: { color: '#a0a4b0', fontSize: 12 } },
    grid: { top: 30, right: 20, bottom: 30, left: 55 },
    xAxis: { type: 'category', data: [], axisLabel: { color: '#a0a4b0', fontSize: 11 } },
    yAxis: {
      type: 'value',
      name: 'KB/s',
      nameTextStyle: { color: '#a0a4b0' },
      axisLabel: { color: '#a0a4b0' },
      splitLine: { lineStyle: { color: '#2a2d35' } },
    },
    series: [
      {
        name: '下载',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#6c5ce7', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(108,92,231,0.3)' },
            { offset: 1, color: 'rgba(108,92,231,0.02)' },
          ]),
        },
      },
      {
        name: '上传',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#00b894', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,184,148,0.3)' },
            { offset: 1, color: 'rgba(0,184,148,0.02)' },
          ]),
        },
      },
    ],
  })
}

/** 计算网络速率 (通过与上次数据的差值) */
function calcNetworkDelta(network) {
  if (!prevNetwork) {
    prevNetwork = {
      bytes_recv: network.bytes_recv,
      bytes_sent: network.bytes_sent,
      time: Date.now(),
    }
    return { sent: 0, recv: 0 }
  }
  const elapsed = (Date.now() - prevNetwork.time) / 1000
  if (elapsed <= 0) return { sent: 0, recv: 0 }

  const recvDelta = Math.max(0, (network.bytes_recv - prevNetwork.bytes_recv) / 1024 / elapsed)
  const sentDelta = Math.max(0, (network.bytes_sent - prevNetwork.bytes_sent) / 1024 / elapsed)

  prevNetwork = {
    bytes_recv: network.bytes_recv,
    bytes_sent: network.bytes_sent,
    time: Date.now(),
  }

  return {
    sent: sentDelta.toFixed(2),
    recv: recvDelta.toFixed(2),
  }
}

/** 拉取全站统计数据（仅首次打开 Tab 时请求） */
async function fetchSiteStats() {
  try {
    const res = await request.get('/monitor/site-stats')
    const d = res.data.data || res.data
    siteStats.value = d

    const caseRatio = Math.min(d.cases / 200, 1)
    const volumeRatio = Math.min(d.volumes / 500, 1)
    const lawyerRatio = Math.min(d.lawyers / 50, 1)

    caseLiquidChart?.setOption({
      series: [{ data: [caseRatio, caseRatio], label: { formatter: d.cases + '\n案件' } }],
    })
    volumeLiquidChart?.setOption({
      series: [{ data: [volumeRatio, volumeRatio], label: { formatter: d.volumes + '\n卷宗' } }],
    })
    lawyerLiquidChart?.setOption({
      series: [{ data: [lawyerRatio, lawyerRatio], label: { formatter: d.lawyers + '\n律师' } }],
    })
  } catch (e) {
    console.error('获取全站统计失败:', e)
  }
}

/** 拉取监控数据并更新所有图表 */
async function fetchMonitorData() {
  try {
    const res = await request.get('/monitor/system-info')
    const d = res.data.data || res.data
    monitorData.value = d

    const nd = calcNetworkDelta(d.network)
    networkDelta.value = nd

    const now = new Date().toLocaleTimeString('zh-CN', { hour12: false })

    // 维护历史数据队列
    const h = history.value
    h.cpu.push(d.cpu.percent)
    h.mem.push(d.memory.percent)
    h.disk_c.push(d.disk_c.percent)
    h.disk_d.push(d.disk_d.percent)
    h.recv.push(nd.recv)
    h.sent.push(nd.sent)
    h.disk_read.push(d.disk_io.read_kbps)
    h.disk_write.push(d.disk_io.write_kbps)
    h.timestamps.push(now)
    if (h.cpu.length > MAX_HISTORY) {
      ;[
        'cpu',
        'mem',
        'disk_c',
        'disk_d',
        'recv',
        'sent',
        'disk_read',
        'disk_write',
        'timestamps',
      ].forEach((k) => h[k].shift())
    }

    // 更新迷你 sparklines
    cpuSparkChart?.setOption(makeSparkOption(h.cpu, cpuColor.value))
    memSparkChart?.setOption(makeSparkOption(h.mem, memColor.value))
    diskCSparkChart?.setOption(makeSparkOption(h.disk_c, diskCColor.value))
    diskDSparkChart?.setOption(makeSparkOption(h.disk_d, diskDColor.value))

    const ts = h.timestamps

    // 更新 CPU 趋势大图（颜色随负载动态变化）
    cpuChart?.setOption({
      xAxis: { data: ts },
      series: [
        {
          data: h.cpu,
          lineStyle: { color: cpuColor.value },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: cpuColor.value + '40' },
              { offset: 1, color: cpuColor.value + '05' },
            ]),
          },
        },
      ],
    })

    // 更新内存趋势大图
    memChart?.setOption({ xAxis: { data: ts }, series: [{ data: h.mem }] })

    // 更新磁盘 I/O 图表
    diskIOChart?.setOption({
      xAxis: { data: ts },
      series: [{ data: h.disk_read }, { data: h.disk_write }],
    })

    // 更新网络趋势大图
    netChart?.setOption({ xAxis: { data: ts }, series: [{ data: h.recv }, { data: h.sent }] })

    // 更新 C 盘环形图
    diskCChart?.setOption({
      series: [
        {
          data: [
            { value: d.disk_c.used_gb, name: '已用' },
            { value: d.disk_c.free_gb, name: '可用' },
          ],
        },
      ],
    })

    // 更新 D 盘环形图
    diskDChart?.setOption({
      series: [
        {
          data: [
            { value: d.disk_d.used_gb, name: '已用' },
            { value: d.disk_d.free_gb, name: '可用' },
          ],
        },
      ],
    })
  } catch (e) {
    console.error('获取监控数据失败:', e)
  }
}

/** 启动或重置监控定时器 */
function startMonitorTimer() {
  if (monitorTimer.value) {
    clearInterval(monitorTimer.value)
    monitorTimer.value = null
  }
  if (refreshInterval.value > 0) {
    monitorTimer.value = setInterval(fetchMonitorData, refreshInterval.value)
  }
}

/** 用户手动切换频率时的处理函数 */
function handleIntervalChange(val) {
  startMonitorTimer()
  if (val > 0) {
    fetchMonitorData()
    ElMessage.success(`刷新频率已切换为 ${val / 1000} 秒`)
  } else {
    ElMessage.warning('数据自动刷新已暂停')
  }
}

/** 销毁所有 ECharts 实例并清除定时器 */
function destroyMonitor() {
  clearInterval(monitorTimer.value)
  monitorTimer.value = null
  prevNetwork = null
  history.value = {
    cpu: [],
    mem: [],
    disk_c: [],
    disk_d: [],
    recv: [],
    sent: [],
    disk_read: [],
    disk_write: [],
    timestamps: [],
  }
  const charts = [
    cpuSparkChart,
    memSparkChart,
    diskCSparkChart,
    diskDSparkChart,
    cpuChart,
    memChart,
    diskIOChart,
    netChart,
    diskCChart,
    diskDChart,
    caseLiquidChart,
    volumeLiquidChart,
    lawyerLiquidChart,
  ]
  charts.forEach((c) => c?.dispose())
  cpuSparkChart = memSparkChart = diskCSparkChart = diskDSparkChart = null
  cpuChart = memChart = diskIOChart = netChart = diskCChart = diskDChart = null
  caseLiquidChart = volumeLiquidChart = lawyerLiquidChart = null
}

onMounted(() => {
  nextTick(() => {
    initSparkCharts()
    initCpuChart()
    initMemChart()
    initDiskIOChart()
    initNetChart()
    initDiskCChart()
    initDiskDChart()
    initLiquidCharts()
    fetchMonitorData()
    fetchSiteStats()
    startMonitorTimer()
  })
})

onUnmounted(() => {
  destroyMonitor()
})
</script>

<style scoped>
/* ========================================
   Grafana 风格监控面板样式
   ======================================== */
.monitor-dashboard {
  background: #1a1c23;
  border-radius: 8px;
  padding: 20px;
  min-height: 600px;
}

/* 刷新频率控制栏 */
.refresh-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.refresh-label {
  font-size: 13px;
  color: #a0a4b0;
}

/* 统计卡片行 */
.stat-row {
  margin-bottom: 0;
}
.grafana-stat-card {
  background: #21232b;
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: box-shadow 0.3s;
  min-height: 140px;
}
.grafana-stat-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}
/* 紧凑模式（第二行 QPS/活跃用户/网络） */
.grafana-stat-card.compact {
  min-height: auto;
  padding: 14px 20px;
}
.grafana-stat-card .stat-label {
  font-size: 12px;
  color: #8e929a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.grafana-stat-card .stat-value-wrap {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 4px;
}
.grafana-stat-card .stat-big-num {
  font-size: 36px;
  font-weight: 700;
  font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
  line-height: 1;
}
.grafana-stat-card .stat-unit {
  font-size: 16px;
  color: #8e929a;
  font-weight: 500;
}
.grafana-stat-card .stat-detail {
  font-size: 12px;
  color: #8e929a;
  margin-bottom: 8px;
}
.grafana-stat-card .stat-sparkline {
  width: 100%;
  height: 35px;
}

/* 主面板 */
.grafana-panel {
  background: #21232b;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  height: 100%;
}
.grafana-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #2a2d35;
}
.grafana-panel .panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #d0d2d8;
}
.grafana-panel .panel-subtitle {
  font-size: 11px;
  color: #6b6f78;
}
.grafana-panel .panel-chart {
  width: 100%;
  height: 280px;
}
/* 较矮的图表容器（环形图 / 水波球） */
.grafana-panel .panel-chart-sm {
  width: 100%;
  height: 220px;
}

/* ── 移动端适配 ── */
@media (max-width: 768px) {
  .monitor-dashboard {
    padding: 12px 8px;
  }
  .grafana-stat-card {
    padding: 12px 14px;
    margin-bottom: 10px;
    min-height: auto;
  }
  .grafana-stat-card .stat-big-num {
    font-size: 26px;
  }
  .grafana-stat-card .stat-sparkline {
    height: 28px;
  }
  .grafana-panel .panel-chart {
    height: 220px;
  }
  .refresh-bar {
    justify-content: flex-start;
  }
  .refresh-label {
    font-size: 12px;
  }
}
</style>
