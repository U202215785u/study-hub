/**
 * Hero — Second Self 全息粒子头像引擎
 *
 * 零依赖（加载时从 CDN 取 Three.js）。
 * 提供：
 *   - 程序化人形点云（默认）
 *   - GLB/GLTF 模型上传 → 点云转换
 *   - 全息光环 + 粒子场
 *   - 四种动画状态：idle / listening / thinking / speaking
 *   - 鼠标交互（旋转、点击脉冲）
 *   - 录音波形可视化
 */

// ── 全局状态 ─────────────────────────────────────────────────
const STATE = {
  mode: 'idle',        // idle | listening | thinking | speaking
  avatarType: 'procedural',  // procedural | uploaded
  targetRotationY: 0,
  pulseStrength: 0,
  waveformData: new Array(64).fill(0),
  audioContext: null,
  analyser: null,
};

// 从全局获取 Three.js（index.html 中通过 <script> 加载）
const THREE = window.THREE || {};
const GLTFLoader = window.THREE?.GLTFLoader;

let scene, camera, renderer, avatarGroup, ringGroup, particleField;
let defaultPointCloud, uploadedPointCloud;
let clock = null;  // 在 initHero 中初始化

// ── 初始化 ───────────────────────────────────────────────────

export async function initHero(containerId, apiBase = 'http://localhost:8420/api') {
  // Three.js 由 index.html 中的 <script> 标签加载
  if (!window.THREE) {
    console.error('Three.js 未加载，请检查 CDN 连接');
    return null;
  }
  const T = window.THREE;

  const container = document.getElementById(containerId);
  if (!container) return console.error('Hero container not found:', containerId);

  // 初始化时钟
  clock = new T.Clock();

  // 场景
  scene = new T.Scene();

  // 相机
  camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(0, 1.2, 5);
  camera.lookAt(0, 0.8, 0);

  // 渲染器
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  // 灯光
  scene.add(new THREE.AmbientLight(0x001122, 0.5));
  const pointLight = new THREE.PointLight(0x00aaff, 2, 10);
  pointLight.position.set(0, 2, 3);
  scene.add(pointLight);

  // 创建场景元素
  createParticleField();
  createRingGroup();
  createDefaultAvatar();
  createGridFloor();

  // 事件
  renderer.domElement.addEventListener('click', onAvatarClick);
  renderer.domElement.addEventListener('mousemove', onAvatarMouseMove);
  window.addEventListener('resize', () => onResize(container));

  // 暴露 API
  window.__heroAPI = {
    setMode: (m) => { STATE.mode = m; },
    setWaveform: (data) => { STATE.waveformData = data; },
    pulse: () => { STATE.pulseStrength = 1.0; },
    loadModel: loadUploadedModel,
    resetAvatar: createDefaultAvatar,
    getState: () => STATE,
  };

  // 渲染循环
  function animate() {
    requestAnimationFrame(animate);
    updateAvatar();
    renderer.render(scene, camera);
  }
  animate();

  return window.__heroAPI;
}

// ── Three.js CDN 加载（多源回退 + 超时）─────────────────────

const CDN_SOURCES = [
  'https://cdn.jsdelivr.net/npm/three@0.140.0/build/three.min.js',
  'https://unpkg.com/three@0.140.0/build/three.min.js',
];
const GLTF_CDN_SOURCES = [
  'https://cdn.jsdelivr.net/npm/three@0.140.0/examples/js/loaders/GLTFLoader.js',
  'https://unpkg.com/three@0.140.0/examples/js/loaders/GLTFLoader.js',
];

async function loadThreeJS() {
  if (window.THREE) return;

  // 尝试多个 CDN 源，每个 8 秒超时
  for (const url of CDN_SOURCES) {
    try {
      await loadScriptWithTimeout(url, 8000);
      // 验证 THREE 真的加载了
      if (!window.THREE) {
        console.warn('CDN 脚本加载完成但 THREE 全局未定义:', url);
        continue;
      }
      // 加载 GLTFLoader
      for (const gltfUrl of GLTF_CDN_SOURCES) {
        try {
          await loadScriptWithTimeout(gltfUrl, 5000);
          return;
        } catch(e) { /* 下一个 */ }
      }
      return; // Three 好了但 GLTFLoader 失败 — 仍可运行（只是不能上传模型）
    } catch(e) { /* 下一个 CDN */ }
  }
  throw new Error('所有 Three.js CDN 源加载失败，请检查网络');
}

function loadScriptWithTimeout(url, ms) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    const timer = setTimeout(() => {
      script.onload = script.onerror = null;
      script.remove();
      reject(new Error(`CDN 超时: ${url}`));
    }, ms);
    script.onload = () => { clearTimeout(timer); resolve(); };
    script.onerror = () => { clearTimeout(timer); script.remove(); reject(new Error(`CDN 错误: ${url}`)); };
    document.head.appendChild(script);
  });
}

// ── 默认头像：程序化人形点云 ──────────────────────────────────

function createDefaultAvatar() {
  if (defaultPointCloud) {
    avatarGroup.remove(defaultPointCloud);
    defaultPointCloud = null;
  }
  if (uploadedPointCloud) {
    avatarGroup.remove(uploadedPointCloud);
    uploadedPointCloud = null;
  }
  STATE.avatarType = 'procedural';

  if (!avatarGroup) {
    avatarGroup = new THREE.Group();
    scene.add(avatarGroup);
  }

  const particles = buildHumanoidParticles();
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(particles, 3));

  // 为每个粒子分配颜色（蓝→青渐变）
  const colors = new Float32Array(particles.length);
  for (let i = 0; i < particles.length / 3; i++) {
    const y = particles[i * 3 + 1];
    const t = (y + 1) / 3; // 归一化高度
    colors[i * 3]     = 0.05 + t * 0.05;   // R
    colors[i * 3 + 1] = 0.4 + t * 0.6;     // G
    colors[i * 3 + 2] = 0.6 + t * 0.4;     // B
  }
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.025,
    vertexColors: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    transparent: true,
    opacity: 0.85,
  });

  defaultPointCloud = new THREE.Points(geometry, material);
  avatarGroup.add(defaultPointCloud);
}

function buildHumanoidParticles() {
  const particles = [];
  const height = 2.2;
  const segments = 60;

  // 头部（球体）
  const headCenter = [0, height * 0.82, 0];
  const headRadius = 0.22;
  for (let i = 0; i < 800; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const r = headRadius * (0.85 + Math.random() * 0.15);
    particles.push(
      headCenter[0] + r * Math.sin(phi) * Math.cos(theta),
      headCenter[1] + r * Math.sin(phi) * Math.sin(theta) * 0.9,
      headCenter[2] + r * Math.cos(phi)
    );
  }

  // 脖子
  for (let i = 0; i < 100; i++) {
    const y = height * 0.6 + Math.random() * height * 0.08;
    const r = 0.08 + Math.random() * 0.02;
    const angle = Math.random() * Math.PI * 2;
    particles.push(Math.cos(angle) * r, y, Math.sin(angle) * r);
  }

  // 躯干
  for (let i = 0; i < 600; i++) {
    const y = height * 0.25 + Math.random() * height * 0.36;
    const t = (y - height * 0.25) / (height * 0.36);
    const r = 0.25 + Math.sin(t * Math.PI) * 0.18;
    const angle = Math.random() * Math.PI * 2;
    particles.push(
      Math.cos(angle) * r * (0.7 + Math.random() * 0.3),
      y,
      Math.sin(angle) * r * (0.7 + Math.random() * 0.3)
    );
  }

  // 肩膀
  for (let side = -1; side <= 1; side += 2) {
    for (let i = 0; i < 200; i++) {
      const y = height * 0.56 + Math.random() * height * 0.06;
      const r = 0.06 + Math.random() * 0.04;
      const baseX = side * 0.35;
      const angle = Math.random() * Math.PI * 2;
      particles.push(baseX + Math.cos(angle) * r, y, Math.sin(angle) * r);
    }
  }

  // 手臂
  for (let side = -1; side <= 1; side += 2) {
    for (let i = 0; i < 400; i++) {
      const t = Math.random();
      const y = height * 0.28 + t * height * 0.3;
      const r = 0.05 + (1 - t) * 0.03;
      const baseX = side * (0.4 + t * 0.1);
      const angle = Math.random() * Math.PI * 2;
      particles.push(baseX + Math.cos(angle) * r, y, Math.sin(angle) * r);
    }
  }

  return particles;
}

// ── 全息光环 ──────────────────────────────────────────────────

function createRingGroup() {
  ringGroup = new THREE.Group();
  scene.add(ringGroup);

  // 主光环（脚下旋转环）
  for (let i = 0; i < 3; i++) {
    const radius = 0.8 + i * 0.25;
    const geometry = new THREE.TorusGeometry(radius, 0.008, 16, 80);
    const material = new THREE.MeshBasicMaterial({
      color: new THREE.Color().setHSL(0.55 + i * 0.05, 0.8, 0.5 + i * 0.2),
      transparent: true,
      opacity: 0.5 - i * 0.12,
    });
    const ring = new THREE.Mesh(geometry, material);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = -0.15;
    ring.userData = { rotSpeed: 0.3 + i * 0.15, tilt: i * 0.15 };
    ringGroup.add(ring);
  }

  // 垂直光环（背后的能量环）
  const vRingGeo = new THREE.TorusGeometry(1.1, 0.006, 16, 100);
  const vRingMat = new THREE.MeshBasicMaterial({
    color: 0x2288cc,
    transparent: true,
    opacity: 0.3,
  });
  const vRing = new THREE.Mesh(vRingGeo, vRingMat);
  vRing.position.y = 0.8;
  vRing.userData = { rotSpeed: 0.1, tilt: 0 };
  ringGroup.add(vRing);
}

// ── 粒子场 ───────────────────────────────────────────────────

function createParticleField() {
  const count = 500;
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 6;
    positions[i * 3 + 1] = Math.random() * 4 - 0.5;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 4;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    size: 0.015,
    color: 0x3388cc,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    transparent: true,
    opacity: 0.4,
  });
  particleField = new THREE.Points(geometry, material);
  scene.add(particleField);
}

// ── 地面网格 ──────────────────────────────────────────────────

function createGridFloor() {
  const gridHelper = new THREE.PolarGridHelper(2.5, 32, 20, 64, 0x114466, 0x114466);
  gridHelper.position.y = -0.6;
  scene.add(gridHelper);
}

// ── 每帧更新 ──────────────────────────────────────────────────

function updateAvatar() {
  const dt = Math.min(clock.getDelta(), 0.1);
  const time = performance.now() * 0.001;

  // 头像旋转
  if (avatarGroup) {
    const targetY = STATE.mode === 'listening' ? STATE.targetRotationY + Math.sin(time * 2) * 0.2
                  : STATE.mode === 'thinking' ? time * 0.5
                  : STATE.targetRotationY;
    avatarGroup.rotation.y += (targetY - avatarGroup.rotation.y) * 0.05;

    // 呼吸缩放
    const breathe = 1 + Math.sin(time * 0.8) * 0.02;
    const listeningScale = STATE.mode === 'listening' ? 1 + Math.sin(time * 4) * 0.03 : 0;
    const thinkingScale = STATE.mode === 'thinking' ? 1 + Math.sin(time * 2.5) * 0.04 : 0;
    const pulseScale = STATE.pulseStrength;
    const scale = breathe + listeningScale + thinkingScale + pulseScale;
    avatarGroup.scale.setScalar(scale);

    // 脉冲衰减
    STATE.pulseStrength *= 0.9;
  }

  // 粒子场旋转
  if (particleField) {
    particleField.rotation.y += dt * 0.05;
    particleField.rotation.x += dt * 0.02;
    // 粒子随状态变化
    const opacity = STATE.mode === 'speaking' ? 0.6 + Math.sin(time * 8) * 0.1
                  : STATE.mode === 'thinking' ? 0.5 + Math.sin(time * 3) * 0.1
                  : 0.35;
    particleField.material.opacity = opacity;
  }

  // 光环动画
  if (ringGroup) {
    ringGroup.children.forEach(ring => {
      const { rotSpeed, tilt } = ring.userData || {};
      ring.rotation.z += dt * (rotSpeed || 0.3);
      if (tilt) ring.rotation.x = Math.PI / 2 + Math.sin(time * 0.5) * tilt;
    });
    ringGroup.position.y = -0.15 + Math.sin(time * 0.6) * 0.05;
  }

  // 录音波形可视化
  if (STATE.mode === 'listening' || STATE.mode === 'speaking') {
    updateWaveformVisual(dt);
  }
}

// ── 波形可视化 ───────────────────────────────────────────────

let waveformBars = [];

function updateWaveformVisual(dt) {
  const data = STATE.waveformData;
  const count = data.length;

  // 动态创建/更新波形粒子条
  if (waveformBars.length === 0) {
    const barGeo = new THREE.SphereGeometry(0.015, 4, 4);
    for (let i = 0; i < count; i++) {
      const barMat = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setHSL(0.55 + i / count * 0.1, 0.9, 0.5),
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        transparent: true,
      });
      const bar = new THREE.Mesh(barGeo, barMat);
      bar.visible = false;
      ringGroup.add(bar);
      waveformBars.push(bar);
    }
  }

  const radius = 1.3;
  for (let i = 0; i < waveformBars.length; i++) {
    const bar = waveformBars[i];
    const val = data[i] || 0;
    const angle = (i / count) * Math.PI * 2;
    const height = val * 0.8;

    bar.position.set(
      Math.cos(angle) * radius,
      -0.15 + height,
      Math.sin(angle) * radius
    );
    bar.visible = val > 0.02;
    bar.material.opacity = 0.4 + val * 0.6;
    bar.scale.setScalar(0.6 + val * 0.8);
  }
}

// ── 3D 模型上传 → 点云转换 ───────────────────────────────────

export async function loadUploadedModel(file) {
  if (!window.THREE || !window.THREE.GLTFLoader) {
    throw new Error('Three.js GLTFLoader not loaded');
  }

  const url = URL.createObjectURL(file);
  const loader = new THREE.GLTFLoader();

  return new Promise((resolve, reject) => {
    loader.load(url, (gltf) => {
      URL.revokeObjectURL(url);

      // 提取所有顶点
      const allVertices = [];
      gltf.scene.traverse((child) => {
        if (child.isMesh && child.geometry.attributes.position) {
          const pos = child.geometry.attributes.position;
          // 采样以避免过多顶点
          const step = Math.max(1, Math.floor(pos.count / 15000));
          for (let i = 0; i < pos.count; i += step) {
            allVertices.push(pos.getX(i), pos.getY(i), pos.getZ(i));
          }
        }
      });

      if (allVertices.length === 0) {
        reject(new Error('模型中没有找到顶点数据'));
        return;
      }

      // 归一化到 [-1, 1] 范围
      const normalized = normalizeVertices(allVertices, 2.0);

      // 替换头像
      if (defaultPointCloud) {
        avatarGroup.remove(defaultPointCloud);
        defaultPointCloud = null;
      }
      if (uploadedPointCloud) {
        avatarGroup.remove(uploadedPointCloud);
        uploadedPointCloud = null;
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(normalized, 3));

      // 上传模型的颜色：蓝白点云
      const colors = new Float32Array(normalized.length);
      for (let i = 0; i < normalized.length / 3; i++) {
        const y = normalized[i * 3 + 1];
        const t = (y + 1) / 2;
        colors[i * 3]     = 0.1 + t * 0.2;
        colors[i * 3 + 1] = 0.5 + t * 0.5;
        colors[i * 3 + 2] = 0.6 + t * 0.4;
      }
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

      const material = new THREE.PointsMaterial({
        size: 0.018,
        vertexColors: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        transparent: true,
        opacity: 0.9,
      });

      uploadedPointCloud = new THREE.Points(geometry, material);
      avatarGroup.add(uploadedPointCloud);
      STATE.avatarType = 'uploaded';
      STATE.pulseStrength = 0.6;

      resolve({ vertexCount: allVertices.length / 3 });
    }, undefined, reject);
  });
}

function normalizeVertices(vertices, targetHeight) {
  // 找到包围盒
  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
  for (let i = 0; i < vertices.length; i += 3) {
    minX = Math.min(minX, vertices[i]);
    minY = Math.min(minY, vertices[i + 1]);
    minZ = Math.min(minZ, vertices[i + 2]);
    maxX = Math.max(maxX, vertices[i]);
    maxY = Math.max(maxY, vertices[i + 1]);
    maxZ = Math.max(maxZ, vertices[i + 2]);
  }

  const cx = (minX + maxX) / 2;
  const cy = minY;
  const cz = (minZ + maxZ) / 2;
  const h = maxY - minY || 1;
  const scale = targetHeight / h;

  const result = new Float32Array(vertices.length);
  for (let i = 0; i < vertices.length; i += 3) {
    result[i]     = (vertices[i] - cx) * scale;
    result[i + 1] = (vertices[i + 1] - cy) * scale;
    result[i + 2] = (vertices[i + 2] - cz) * scale;
  }
  return result;
}

// ── 交互：点击脉冲 ───────────────────────────────────────────

function onAvatarClick(e) {
  STATE.pulseStrength = 0.5;
  // 触发回调
  if (window.__heroAPI && window.__heroAPI._onClick) {
    window.__heroAPI._onClick();
  }
}

function onAvatarMouseMove(e) {
  const rect = renderer.domElement.getBoundingClientRect();
  const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  STATE.targetRotationY = x * 0.6;
}

function onResize(container) {
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
}

// ── 录音波形输入 ─────────────────────────────────────────────

export function startMicVisualization() {
  if (!STATE.audioContext) {
    STATE.audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (STATE.audioContext.state === 'suspended') {
    STATE.audioContext.resume();
  }

  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    const source = STATE.audioContext.createMediaStreamSource(stream);
    STATE.analyser = STATE.audioContext.createAnalyser();
    STATE.analyser.fftSize = 128;
    source.connect(STATE.analyser);

    const dataArray = new Uint8Array(STATE.analyser.frequencyBinCount);
    function updateWaveform() {
      if (!STATE.analyser) return;
      STATE.analyser.getByteFrequencyData(dataArray);
      const normalized = new Array(64).fill(0);
      const step = dataArray.length / 64;
      for (let i = 0; i < 64; i++) {
        normalized[i] = dataArray[Math.floor(i * step)] / 255;
      }
      STATE.waveformData = normalized;
      if (STATE.mode === 'listening' || STATE.mode === 'speaking') {
        requestAnimationFrame(updateWaveform);
      }
    }
    updateWaveform();
  }).catch(() => {
    // 模拟波形（无麦克风权限时）
    function simulateWaveform() {
      for (let i = 0; i < 64; i++) {
        STATE.waveformData[i] = Math.random() * 0.5 + Math.sin(Date.now() * 0.01 + i * 0.3) * 0.3;
      }
      if (STATE.mode === 'listening' || STATE.mode === 'speaking') {
        requestAnimationFrame(simulateWaveform);
      }
    }
    simulateWaveform();
  });
}

export function stopMicVisualization() {
  STATE.waveformData = new Array(64).fill(0);
  if (STATE.analyser) {
    STATE.analyser.disconnect();
    STATE.analyser = null;
  }
}
