import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles.css'

const app = createApp(App)

// 全局注册所有图标
for (const [name, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, comp)
}

app.use(ElementPlus).use(router).mount('#app')
