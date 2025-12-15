// --- MediaPipe 和摄像头设置 ---

const videoElement = document.getElementById('video');
const camStatusEl = document.getElementById('cam-status');
const distanceDisplayEl = document.getElementById('distance-display');
const controlStatusEl = document.getElementById('control-status');

// 摄像头分辨率设置
const videoConfig = {
    audio: false,
    video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: "user"
    }
};

// 爆炸阈值 (双手张开距离超过此值触发爆炸)
const EXPLODE_THRESHOLD = 8;

// 初始化 MediaPipe Hands
const hands = new Hands({locateFile: (file) => {
  return `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675466861/${file}`;
}});

hands.setOptions({
    maxNumHands: 2,
    modelComplexity: 1, // 0 速度快，1 准确率高
    minDetectionConfidence: 0.7,
    minTrackingConfidence: 0.5
});

hands.onResults(onResults);

/**
 * 计算两个点之间的欧几里得距离
 * @param {object} p1 - {x, y, z} 点
 * @param {object} p2 - {x, y, z} 点
 * @returns {number} 距离
 */
function calculateDistance(p1, p2) {
    const dx = p1.x - p2.x;
    const dy = p1.y - p2.y;
    const dz = p1.z - p2.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

/**
 * MediaPipe 结果回调函数
 * @param {object} results - MediaPipe Hand 结果
 */
function onResults(results) {
    if (!results.multiHandLandmarks || results.multiHandedness.length === 0) {
        // 未检测到手
        window.handDistance = 0;
        distanceDisplayEl.innerText = '0.00';
        controlStatusEl.innerText = '等待双手...';

        // 确保粒子系统收缩
        if (window.updateParticleScale) {
            window.updateParticleScale(0);
        }
        return;
    }

    const numHands = results.multiHandLandmarks.length;

    if (numHands === 2) {
        // ----------------------------------------
        // 双手控制逻辑：计算双手距离
        // ----------------------------------------

        // 假设 Hand 0 的中指根部 (索引 9)
        const hand1Point = results.multiHandLandmarks[0][9];
        // 假设 Hand 1 的中指根部 (索引 9)
        const hand2Point = results.multiHandLandmarks[1][9];

        // 计算距离 (归一化到 0-1 的 MediaPipe 坐标系)
        const distance = calculateDistance(hand1Point, hand2Point);

        // 将 0-1 的距离值映射到 0-10 的范围，用于 Three.js 缩放控制
        // 假设最大有效距离约为 0.5 (取决于摄像机和手势)
        const maxExpectedDistance = 0.5;
        let normalizedDistance = (distance / maxExpectedDistance) * 10;

        // 限制在 0-10 范围内
        normalizedDistance = Math.max(0, Math.min(10, normalizedDistance));

        // 更新全局变量和 UI
        window.handDistance = normalizedDistance;
        distanceDisplayEl.innerText = normalizedDistance.toFixed(2);

        if (window.updateParticleScale) {
            window.updateParticleScale(normalizedDistance);
        }

        // 爆炸手势判断 (双手张开达到阈值)
        if (normalizedDistance >= EXPLODE_THRESHOLD) {
            controlStatusEl.innerText = '💥 爆炸手势!';
            if (window.explodeChristmasTree) {
                 window.explodeChristmasTree();
            }
        } else {
            controlStatusEl.innerText = `缩放/扩散 (双手距离 ${normalizedDistance.toFixed(1)}/10)`;
        }

    } else if (numHands === 1) {
        // ----------------------------------------
        // 单手控制逻辑：可以根据手掌开合控制，但此处仅处理双手
        // ----------------------------------------
        window.handDistance = 0; // 避免单手时意外缩放
        distanceDisplayEl.innerText = '0.00';
        controlStatusEl.innerText = '只检测到一只手。';
    }
}


// --- 启动摄像头 ---
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia(videoConfig)
        .then(stream => {
            camStatusEl.innerText = '成功';
            videoElement.srcObject = stream;
            videoElement.addEventListener('loadeddata', () => {
                // MediaPipe CameraUtil 替代手动循环，进行连续处理
                const camera = new Camera(videoElement, {
                    onFrame: async () => {
                        await hands.send({image: videoElement});
                    },
                    width: videoElement.videoWidth,
                    height: videoElement.videoHeight
                });
                camera.start();
            });
        })
        .catch(err => {
            console.error('无法访问摄像头:', err);
            camStatusEl.innerText = `失败: ${err.name}`;
            controlStatusEl.innerText = '请允许访问摄像头！';
        });
} else {
    camStatusEl.innerText = '失败: 浏览器不支持 MediaDevices API';
}