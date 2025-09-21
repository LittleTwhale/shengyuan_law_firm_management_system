<template>
  <div class="particle-test">
    <!-- vue3-particles 粒子背景 -->
    <Particles
      id="tsparticles"
      :options="particlesOptions"
    />
    <div class="content">
      <h1>粒子特效测试</h1>
      <button @click="changeEffect">切换效果</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const effects = [
  {
    background: { color: { value: "#000" } },
    particles: {
      number: { value: 80 },
      color: { value: "#ffffff" },
      shape: { type: "circle" },
      opacity: { value: 0.5 },
      size: { value: { min: 1, max: 5 } },
      move: { enable: true, speed: 2 },
    },
    interactivity: {
      events: { onHover: { enable: true, mode: "repulse" } },
    },
  },
  {
    background: { color: { value: "#1a1a2e" } },
    particles: {
      number: { value: 50 },
      color: { value: "#00ffcc" },
      shape: { type: "star" },
      move: { enable: true, speed: 1 },
    },
    interactivity: {
      events: { onClick: { enable: true, mode: "push" } },
    },
  },
];

const particlesOptions = ref(effects[0]);
let index = 0;

function changeEffect() {
  index = (index + 1) % effects.length;
  particlesOptions.value = effects[index];
}
</script>

<style scoped>
.particle-test {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
.content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  text-align: center;
}
button {
  margin-top: 20px;
  padding: 10px 20px;
  background: #ff6600;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
}
</style>
