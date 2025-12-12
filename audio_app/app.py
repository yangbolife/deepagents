from flask import Flask, render_template
from flask_socketio import SocketIO
import os
import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult
import threading
import queue

name="main"
app = Flask(name)
socketio = SocketIO(app, cors_allowed_origins="*")
audio_queue = queue.Queue()
recognition_instance = None


def validate_audio_data(audio_data):
    """
    验证音频数据的有效性
    """
    # 检查音频数据是否为空
    if audio_data is None or len(audio_data) == 0:
        print("警告：音频数据为空")
        return False

    # 检查音频数据长度是否符合要求
    if len(audio_data) < 320:  # 最小音频帧长度
        print(f"警告：音频数据过短，长度：{len(audio_data)}")
        return False

    # 检查音频数据是否为静音（可选）
    if is_silence(audio_data):
        print("警告：检测到静音数据")
        return False

    # 检查音频数据格式（PCM int16）
    try:
        # 将音频数据转换为numpy数组进行验证
        import numpy as np
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # 检查音频幅值范围
        max_amplitude = np.max(np.abs(audio_array))
        if max_amplitude < 100:  # 幅值过小可能是静音
            print(f"警告：音频幅值过小，最大值：{max_amplitude}")
        return True

    except Exception as e:
        print(f"音频数据格式验证失败：{e}")
        return False


def is_silence(audio_data, threshold=500):
    """
    检测是否为静音
    threshold: 静音检测阈值，可根据实际情况调整
    """
    import numpy as np
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    rms = np.sqrt(np.mean(audio_array ** 2))
    return rms < threshold


class AudioValidator:
    def __init__(self):
        self.total_packets = 0
        self.valid_packets = 0
        self.invalid_packets = 0

    def validate(self, audio_data):
        self.total_packets += 1

        if validate_audio_data(audio_data):
            self.valid_packets += 1
            return True
        else:
            self.invalid_packets += 1
            return False

    def get_stats(self):
        valid_rate = (self.valid_packets / self.total_packets * 100) if self.total_packets > 0 else 0
        return {
            'total_packets': self.total_packets,
            'valid_packets': self.valid_packets,
            'invalid_packets': self.invalid_packets,
            'valid_rate': f"{valid_rate:.2f}%"
        }


# 创建全局验证器实例
audio_validator = AudioValidator()


class WebCallback(RecognitionCallback):
    def on_open(self):
        print('语音识别服务已启动')
        socketio.emit('status', {'message': '语音识别服务已启动'})


    def on_close(self):
        print('语音识别服务已关闭')
        socketio.emit('status', {'message': '语音识别服务已关闭'})


    def on_complete(self):
        print('识别完成')
        socketio.emit('status', {'message': '识别完成'})

    def on_error(self, message):
        error_msg = f'识别错误: {message.message}'
        print(error_msg)

        # 根据错误类型进行不同处理
        if 'NO_VALID_AUDIO' in message.message:
            self.handle_audio_error()
        socketio.emit('error', {'message': error_msg})

    def handle_audio_error(self):
        """处理音频数据错误"""
        print("音频数据错误处理：检查麦克风、音频格式和网络连接")

        # 可以在这里添加重连逻辑或用户提示
        socketio.emit('audio_error', {
            'message': '音频数据无效，请检查麦克风设置'
        })
    def on_event(self, result: RecognitionResult):
        sentence = result.get_sentence()
        if 'text' in sentence:
            text = sentence['text']
            print(f'识别结果: {text}')
            # 实时发送识别结果到前端
            socketio.emit('recognition_result', {'text': text})

            if RecognitionResult.is_sentence_end(sentence):
                print('句子结束')
                socketio.emit('sentence_end', {
                    'request_id': result.get_request_id(),
                    'usage': result.get_usage(sentence)
                })
def init_dashscope_api_key():
    if 'DASHSCOPE_API_KEY' in os.environ:
        dashscope.api_key = os.environ['DASHSCOPE_API_KEY']
    else:
        dashscope.api_key = '<your-dashscope-api-key>'

def recognition_worker():
    global recognition_instance
    init_dashscope_api_key()
    callback = WebCallback()
    recognition_instance = Recognition(
        model='paraformer-realtime-v2',
        format='pcm',
        sample_rate=16000,
        semantic_punctuation_enabled=False,
        callback=callback
    )

    recognition_instance.start()

    while True:
        try:
            audio_data = audio_queue.get(timeout=1)
            if audio_data and validate_audio_data(audio_data):
                recognition_instance.send_audio_frame(audio_data)
            else:
                print("工作线程：音频数据验证失败，跳过处理")
        except queue.Empty:
            continue

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    socketio.emit('status', {'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开')
    if recognition_instance:
        recognition_instance.stop()


@socketio.on('audio_data')
def handle_audio_data(data):
    """接收前端发送的音频数据"""

    # 在发送前进行音频数据验证
    if validate_audio_data(data):
        # 只有验证通过的音频数据才发送到识别服务
        audio_queue.put(data)
    else:
        # 记录验证失败的日志
        print(f"音频数据验证失败，丢弃数据包，长度：{len(data)}")


if name == 'main':
    # 启动语音识别工作线程
    thread = threading.Thread(target=recognition_worker, daemon=True)
    thread.start()
    socketio.run(app, debug=True, port=5000)
