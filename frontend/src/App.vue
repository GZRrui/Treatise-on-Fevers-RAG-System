<template>
  <div class="app">
    <header class="header">
      <div class="header-content">
        <h1>《伤寒论》智能问答系统</h1>
        <p class="subtitle">基于 RAG 的中医经典条文问答助手</p>
      </div>
    </header>

    <main class="main">
      <ChatWindow />
    </main>

    <footer class="footer">
      <p>《伤寒论》RAG 问答系统 · LlamaIndex + 通义千问</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import ChatWindow from './components/ChatWindow.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.header h1 {
  color: #2c3e50;
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 0.95rem;
}

.main {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.footer {
  background: rgba(255, 255, 255, 0.9);
  padding: 1rem;
  text-align: center;
  color: #666;
  font-size: 0.85rem;
}
</style>
