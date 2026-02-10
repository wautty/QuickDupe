import keyboard
import time

running = False
start_time = None

def on_del():
    global running, start_time
    if not running:
        start_time = time.time()
        running = True
        print("Timer started...")

def on_esc():
    global running, start_time
    if running:
        elapsed = time.time() - start_time # pyright: ignore[reportOperatorIssue]
        running = False
        print(f"Elapsed: {elapsed:.3f} seconds")

keyboard.on_press_key("delete", lambda _: on_del())
keyboard.on_press_key("esc", lambda _: on_esc())
print("Press DEL to start, ESC to stop. Ctrl+C to quit.")
keyboard.wait()
