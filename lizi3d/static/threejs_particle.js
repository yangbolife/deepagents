// 全局变量，用于接收 MediaPipe 的距离数据
window.handDistance = 5.0; // 默认值
window.updateParticleScale = null; // 占位符，用于手势回调
window.explodeChristmasTree = null; // 占位符，用于手势回调

// --- 核心变量 ---
let scene, camera, renderer, particles, particleGeometry, particleMaterial, gui;
let particleCount = 20000;
let models = {};
let currentModel = 'ChristmasTree';
let isExploded = false;

// UI 控制对象
const settings = {
    particleColor: '#00ffaa',
    model: currentModel,
    explode: () => {
        explodeChristmasTreeInternal();
    },
    // 移除模拟距离，改用 MediaPipe 实际输入
};

// --- 预设模型点集函数 ---
function createModelPoints(geometry) {
    geometry.dispose();
    let positions = [];

    if (geometry.attributes.position) {
         positions = geometry.attributes.position.array;
    } else {
         geometry.computeVertexNormals();
         positions = geometry.attributes.position.array;
    }

    const len = positions.length / 3;
    const finalPositions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
        const originalIndex = (i % len) * 3;
        // 放大几何体，使粒子群更分散
        finalPositions[i * 3] = positions[originalIndex] * 5;
        finalPositions[i * 3 + 1] = positions[originalIndex + 1] * 5;
        finalPositions[i * 3 + 2] = positions[originalIndex + 2] * 5;
    }

    return finalPositions;
}

// 初始化预设模型
function initModels() {
    // 1. 圣诞树模型
    const cone = new THREE.ConeGeometry(5, 15, 32);
    cone.rotateX(-Math.PI / 2);
    cone.translate(0, 7.5, 0);
    models['ChristmasTree'] = createModelPoints(cone);

    // 2. 花朵/土星 (用圆环体近似)
    const torus = new THREE.TorusGeometry(10, 3, 16, 100);
    torus.rotateX(Math.PI / 2);
    models['Flower/Saturn'] = createModelPoints(torus);

    // 3. 爱心/球体
    const sphere = new THREE.SphereGeometry(10, 64, 64);
    models['Heart/Sphere'] = createModelPoints(sphere);

    // 4. 烟花 (初始为中心点)
    const center = new THREE.BufferGeometry();
    center.setAttribute('position', new THREE.BufferAttribute(new Float32Array(particleCount * 3), 3));
    models['Firework'] = center.attributes.position.array.fill(0); // 所有点在中心
}

// --- 初始化 Three.js 场景 ---
function initThreeJS() {
    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 50;

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); // alpha: true 允许透明背景
    renderer.setClearColor(0x000000, 0); // 背景透明
    renderer.setSize(window.innerWidth, window.innerHeight);

    const container = document.getElementById('video-container');
    container.appendChild(renderer.domElement);

    initModels();

    particleMaterial = new THREE.PointsMaterial({
        size: 0.2,
        color: new THREE.Color(settings.particleColor),
        blending: THREE.AdditiveBlending,
        transparent: true,
        depthWrite: false,
        sizeAttenuation: true
    });

    createParticles(currentModel);

    initGUI();

    window.addEventListener('resize', onWindowResize, false);

    // 将核心函数暴露给全局，供 MediaPipe 调用
    window.updateParticleScale = updateParticleScaleInternal;
    window.explodeChristmasTree = explodeChristmasTreeInternal;

    animate();
}

// --- 粒子系统创建/更新 ---
function createParticles(modelName) {
    if (particles) {
        scene.remove(particles);
        particleGeometry.dispose();
    }

    isExploded = false;
    currentModel = modelName;

    const positions = models[modelName];

    particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const initialPositions = positions.slice();
    particleGeometry.setAttribute('initialPosition', new THREE.BufferAttribute(initialPositions, 3));

    const velocities = new Float32Array(particleCount * 3);
    particleGeometry.setAttribute('velocity', new THREE.BufferAttribute(velocities, 3));

    particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);
}

// --- UI (dat.GUI) ---
function initGUI() {
    gui = new dat.GUI();

    gui.add(settings, 'model', ['ChristmasTree', 'Flower/Saturn', 'Heart/Sphere', 'Firework'])
       .name('选择模型')
       .onChange((value) => {
           createParticles(value);
       });

    gui.addColor(settings, 'particleColor')
       .name('粒子颜色')
       .onChange((value) => {
           particleMaterial.color.set(value);
       });

    gui.add(settings, 'explode').name('🎅 爆炸圣诞树');
}


// --- 核心交互逻辑 (内部实现) ---

/**
 * 实时更新粒子群的缩放和扩散 (由 MediaPipe 调用)
 * @param {number} distance - 双手之间的标准化距离 (0-10)
 */
function updateParticleScaleInternal(distance) {
    if (isExploded) return;

    // 距离 0 -> 缩放 0.5 (收缩)
    // 距离 10 -> 缩放 1.5 (扩散)
    const scaleFactor = THREE.MathUtils.lerp(0.5, 1.5, distance / 10);

    particles.scale.set(scaleFactor, scaleFactor, scaleFactor);
    particles.rotation.y += 0.005;
}

/**
 * 实现圣诞树/模型爆炸效果 (由 MediaPipe 或 GUI 调用)
 */
function explodeChristmasTreeInternal() {
    if (isExploded) return;
    if (currentModel !== 'ChristmasTree') {
        console.log("非圣诞树模型，无法执行爆炸效果。");
        return;
    }

    isExploded = true;
    console.log("💥 圣诞树爆炸了！");

    const initialPositions = particleGeometry.attributes.initialPosition.array;
    const velocities = particleGeometry.attributes.velocity.array;

    for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;

        // 目标中心点：圣诞树中心 (0, 7.5, 0)
        const direction = new THREE.Vector3(
            initialPositions[i3] - 0,
            initialPositions[i3 + 1] - 7.5,
            initialPositions[i3 + 2] - 0
        ).normalize();

        const speed = 1 + Math.random() * 5;

        velocities[i3] = direction.x * speed;
        velocities[i3 + 1] = direction.y * speed;
        velocities[i3 + 2] = direction.z * speed;
    }

    particleGeometry.attributes.velocity.needsUpdate = true;
}

// --- 动画循环 ---
function animate() {
    requestAnimationFrame(animate);

    // 1. 实时响应手势变化 (缩放/扩散)
    if (!isExploded) {
        // 使用来自 MediaPipe 的全局 handDistance
        updateParticleScaleInternal(window.handDistance);
    }

    // 2. 爆炸效果更新
    if (isExploded) {
        const positions = particleGeometry.attributes.position.array;
        const velocities = particleGeometry.attributes.velocity.array;
        const gravity = -0.05;

        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;

            // 速度 += 重力
            velocities[i3 + 1] += gravity;

            // 位置 += 速度
            positions[i3] += velocities[i3];
            positions[i3 + 1] += velocities[i3 + 1];
            positions[i3 + 2] += velocities[i3 + 2];
        }

        particleGeometry.attributes.position.needsUpdate = true;
    }

    renderer.render(scene, camera);
}

// --- 窗口大小调整 ---
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

// 启动 Three.js
document.addEventListener('DOMContentLoaded', initThreeJS);