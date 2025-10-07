import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'


const app = createApp(App)

app.use(router)
// 配置 Element Plus 全局使用中文
app.use(ElementPlus, {
  locale: zhCn  // 设置语言为中文
})

app.mount('#app')
