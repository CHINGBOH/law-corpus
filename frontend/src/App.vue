<script setup lang="ts"></script>

<template>
  <router-view />
</template>

<style>
:root {
  color-scheme: light;
  --bg: #f5f7fa;
  --surface: #ffffff;
  --border: #d9e0e8;
  --border-soft: #edf1f5;
  --text: #1d2430;
  --text-muted: #627084;
  --link: #225ea8;
  --accent: #1f6feb;
  --badge-bg: #e8f0fe;
  --badge-text: #244f9e;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.6;
}

a {
  color: var(--link);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

button {
  font: inherit;
  cursor: pointer;
}
</style>
