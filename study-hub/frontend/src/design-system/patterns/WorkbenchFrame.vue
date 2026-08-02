<template>
  <div class="workbench-frame">
    <slot name="navigation" />
    <main class="workbench-frame__main">
      <slot name="greeting" />
      <slot />
    </main>
    <slot name="footer" />
  </div>
</template>

<style scoped>
.workbench-frame {
  min-height: 100vh;
  box-sizing: border-box;
  overflow-x: hidden;
  background: #10130f;
  color: var(--ui-color-text-strong);
}
.workbench-frame__main {
  width: min(1356px, calc(100vw - 84px));
  margin: 0 auto;
  padding-top: 50px;
}
@media (max-width: 1100px) {
  .workbench-frame__main { width: calc(100vw - 48px); min-width: 1010px; margin-left: 24px; }
}
@media (max-width: 767px) {
  .workbench-frame { overflow-x: auto; }
  .workbench-frame__main { width: 1356px; margin-left: 24px; }
}
</style>
