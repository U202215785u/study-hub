<template>
  <div
    class="bento-background"
    data-dashboard-background
    :class="{ 'bento-background--static': static }"
    aria-hidden="true"
  >
    <div class="bg-aurora">
      <span class="bg-aurora__orb bg-aurora__orb--lime" />
      <span class="bg-aurora__orb bg-aurora__orb--violet" />
      <span class="bg-aurora__orb bg-aurora__orb--blue" />
      <span class="bg-aurora__ring" />
    </div>
    <div class="bg-noise" />
  </div>
</template>

<script setup>
defineProps({ static: Boolean })
</script>

<style scoped>
.bento-background {
  position: absolute;
  z-index: 0;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.bg-aurora,
.bg-noise {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.bg-aurora { overflow: hidden; background: #10140f; }
.bg-aurora__orb {
  position: absolute;
  width: 42%;
  aspect-ratio: 1;
  border-radius: 50%;
  filter: blur(72px);
  opacity: .18;
  animation: bg-aurora-drift 68s ease-in-out infinite alternate;
}
.bg-aurora__orb--lime { top: -18%; left: -10%; background: #d7ff63; }
.bg-aurora__orb--violet { top: 8%; right: -14%; background: #8e7cff; animation-delay: -18s; }
.bg-aurora__orb--blue { bottom: -28%; left: 30%; background: #4e9dff; animation-delay: -34s; }
.bg-aurora__ring {
  position: absolute;
  inset: 12% 18%;
  border: 1px solid rgb(215 255 99 / 14%);
  border-radius: 50%;
  opacity: .7;
}
.bg-noise {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 .04 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  mix-blend-mode: screen;
}
.bento-background--static .bg-aurora__orb,
.bento-background--static .bg-aurora__ring,
.bento-background--static .bg-noise {
  animation-play-state: paused;
  will-change: auto;
}
@keyframes bg-aurora-drift {
  from { transform: translate3d(-2%, -1%, 0) scale(1); }
  to { transform: translate3d(2%, 1%, 0) scale(1.06); }
}
@media (prefers-reduced-motion: reduce) {
  .bg-aurora__orb { animation: none; }
}
</style>
