from moviepy.editor import ImageClip, AudioFileClip, VideoClip
from PIL import Image
import os
import numpy as np

# Paths
INPUT_IMAGE = "assets/input.jpg"
AUDIO_PATH = "assets/audio.mp3"
OUTPUT_PATH = "output/result.mp4"

# Settings
DEFAULT_DURATION = 10
FPS = 24
ZOOM_START = 1.0
ZOOM_END = 1.2
TARGET_HEIGHT = 1080

# Step 1: Prepare clean RGB input and 16:9 crop
img = Image.open(INPUT_IMAGE).convert("RGB")
w, h = img.size
target_ratio = 16 / 9

if w / h > target_ratio:
    new_w = int(h * target_ratio) // 2 * 2
    left = (w - new_w) // 2
    img = img.crop((left, 0, left + new_w, h))
else:
    new_h = int(w / target_ratio) // 2 * 2
    top = (h - new_h) // 2
    img = img.crop((0, top, w, top + new_h))

img = img.crop((0, 0, img.width // 2 * 2, img.height // 2 * 2))
clean_path = "assets/temp_clean.jpg"
img.save(clean_path, format="JPEG")

# Step 2: Load static image as clip (without duration yet)
base_clip = ImageClip(clean_path)

# Step 3: Determine final duration
if os.path.exists(AUDIO_PATH):
    audio = AudioFileClip(AUDIO_PATH)
    final_duration = min(DEFAULT_DURATION, audio.duration)
else:
    audio = None
    final_duration = DEFAULT_DURATION

# Step 4: Build zoom effect with dynamic frame generation
def make_zoom(get_frame, width, height):
    def frame(t):
        scale = ZOOM_START + (ZOOM_END - ZOOM_START) * (t / final_duration)
        img = get_frame(0)
        new_w = int(width / scale)
        new_h = int(height / scale)
        x1 = (width - new_w) // 2
        y1 = (height - new_h) // 2
        cropped = img[y1:y1+new_h, x1:x1+new_w]
        resized = np.array(Image.fromarray(cropped).resize((width, height), Image.LANCZOS))
        return resized
    return frame

zoomed = VideoClip(
    make_zoom(base_clip.get_frame, base_clip.w, base_clip.h),
    duration=final_duration
).set_fps(FPS)

# Step 5: Add audio if available
if audio:
    zoomed = zoomed.set_audio(audio.subclip(0, final_duration))

# Step 6: Export safely
os.makedirs("output", exist_ok=True)
zoomed.write_videofile(
    OUTPUT_PATH,
    fps=FPS,
    codec="libx264",
    audio_codec="aac",
    bitrate="5000k",
    preset="medium",
    ffmpeg_params=["-pix_fmt", "yuv420p"]
)
