import sounddevice as sd
import wave

def record_audio(duration, filename):
    # 录制音频
    print(f"开始录制 {duration} 秒的音频...")
    sample_rate = 44100  # 采样率
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype='int16')
    sd.wait()  # 等待录音完成
    print("录制完成，正在保存文件...")

    # 保存音频文件
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(2)  # 立体声
        wf.setsampwidth(2)  # 16 位
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    
    print(f"音频文件已保存为 {filename}")

if __name__ == "__main__":
    duration = int(input("请输入录制时间（秒）："))
    filename = input("请输入保存文件名（例如 output.wav）：")
    record_audio(duration, filename)
