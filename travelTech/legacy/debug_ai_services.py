import image_generator
import requests
import time

def test_pollinations():
    print("--- Testing Image Generation Robustness ---")
    prompts = [
        "apple",
        "isometric 3d illustration of a neural network node glowing in neon blue, dark navy background, minimalist tech style, no text"
    ]

    for p in prompts:
        print(f"Testing Prompt: {p[:30]}...")
        save_path = f"test_image_{int(time.time())}.webp"

        success = image_generator.generate_image(p, save_path)
        print(f"Success: {success}")

        if success:
            import os
            size = os.path.getsize(save_path)
            print(f"File Size: {size} bytes")
            # Cleanup
            try:
                os.remove(save_path)
            except:
                pass
        print("-" * 20)

if __name__ == "__main__":
    test_pollinations()
