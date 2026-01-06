import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

// 1. 引入 Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css' // 引入样式文件

createApp(App).use(ElementPlus).mount('#app')
