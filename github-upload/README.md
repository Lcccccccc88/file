# AutoClicker — Browser Anti-Idle Popup Auto-Clicker

A lightweight desktop utility that automatically detects and clicks popup buttons on your screen. It was built to handle browser **anti-idle / keep-alive verification** popups — the ones that ask you to confirm you're still there by clicking a button like "确定" (Confirm) — so you don't have to watch the screen and click manually.

## How it works

- Every few seconds, it takes a screenshot of your entire screen.
- Using OpenCV template matching, it looks for a reference image of the target button (a small picture you provide) anywhere on screen.
- As soon as the button is found — no matter where the popup appears — it moves the mouse there and clicks it.
- The button is found by **image matching (not fixed coordinates)**, so it works even if the popup moves or the screen resolution / size changes.

## Key features

- **Multi-scale matching**: recognizes the button even when it's rendered at a different size (high-DPI / browser zoom).
- **Easy to configure**: detection interval, match sensitivity, click cooldown, and click limit are all set at the top of the script.
- **No disk usage while running**: screenshots live in memory only, so nothing is written to disk during normal operation.
- **Graceful exit**: stop anytime with `Ctrl+C`.

## Requirements

- Python 3.13+ (Windows)
- Packages: `pillow`, `numpy`, `opencv-python`

Install dependencies:

```
pip install -r requirements.txt
```

## Quick start

1. Provide a small reference image of the button, saved as `button.png` next to the script.
   - On Windows: press `Win + Shift + S`, select only the button itself, save as `button.png`.
2. Verify setup (no clicking):

   ```
   python auto_click_popup.py --check
   ```

3. Test a single click:

   ```
   python auto_click_popup.py --test
   ```

4. Run continuously:

   ```
   python auto_click_popup.py
   ```

   Stop anytime with `Ctrl+C`.

## Configuration

Edit the config block at the top of `auto_click_popup.py`:

| Setting           | Default | Meaning                                   |
|-------------------|---------|-------------------------------------------|
| `CHECK_INTERVAL`  | `3`     | Seconds between screenshot checks          |
| `CONFIDENCE`      | `0.85`  | Match threshold 0–1 (higher = stricter)    |
| `CLICK_COOLDOWN`  | `8`     | Seconds to wait after a click              |
| `MAX_CLICKS`      | `0`     | Max clicks (0 = unlimited)                 |
| `SCALE_RANGE`     | `0.5–2.0` | Template scale search range              |
| `SCALE_STEPS`     | `12`    | Number of scale steps to try               |
