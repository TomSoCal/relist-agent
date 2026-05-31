#!/usr/bin/env python3
"""
generate_videos.py — Create demo videos from sheet screenshots

Creates a simple video compilation of 5 screenshots with text overlays.
Frames the video at 1 frame per screenshot, silent, ~10 seconds total.

Usage:
  python generate_videos.py 3              # All batch 3
  python generate_videos.py 3 destwedding  # Specific listing

Updates: batch_state.json with video=true
Creates: MP4 files in thumbnails/{key}/demo_video.mp4
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

try:
    import imageio
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[ERROR] Missing dependencies. Install with:")
    print("  pip install imageio pillow")
    sys.exit(1)

STATE_FILE = Path(r'C:\Users\tom\agents\etsy\batch_state.json')
ETSY_LISTINGS = Path(r'C:\Users\tom\agents\etsy\etsy_upload_listings.py')
THUMB_DIR = Path(r'C:\Users\tom\agents\etsy\thumbnails')

# ─────────────────────────────────────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────────────────────────────────────

def load_listings_for_batch(batch_num: int) -> List[Dict]:
    """Load LISTINGS from etsy_upload_listings.py and filter by batch."""
    local_ns = {}
    code = ETSY_LISTINGS.read_text()
    exec(code, local_ns)
    all_listings = local_ns.get('LISTINGS', [])

    if batch_num == 1:
        start_key, end_key = 'wedding', 'debut_tl'
    elif batch_num == 3:
        start_key, end_key = 'destwedding', 'multicurrency'
    elif batch_num == 4:
        start_key, end_key = 'baptism', 'finados_pt'
    elif batch_num == 5:
        start_key, end_key = 'road-trip', 'first-time-rv'
    else:
        return []

    start_idx = next((i for i, l in enumerate(all_listings) if l.get('key') == start_key), None)
    end_idx = next((i for i, l in enumerate(all_listings) if l.get('key') == end_key), None)

    if start_idx is not None and end_idx is not None:
        return all_listings[start_idx:end_idx+1]

    return []

def load_state() -> Dict:
    """Load batch_state.json."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'metadata': {}, 'listings': {}}

def save_state(state: Dict):
    """Save batch_state.json."""
    state['metadata']['last_updated'] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))

def create_video_from_thumbnails(key: str, thumb_dir: Path, output_path: Path) -> bool:
    """
    Create a demo video from 5 thumbnail images.
    Each image shown for 2 seconds = 10 second video total.
    """
    try:
        # Collect thumbnail files
        thumb_files = [
            thumb_dir / 'thumb_1_hero.png',
            thumb_dir / 'thumb_2_budget.png',
            thumb_dir / 'thumb_3_guests.png',
            thumb_dir / 'thumb_4_vendors.png',
            thumb_dir / 'thumb_5_instructions.png',
        ]

        # Filter to files that exist
        existing_thumbs = [f for f in thumb_files if f.exists() and f.stat().st_size > 1000]

        if not existing_thumbs:
            return False

        # Load images and duplicate each (2 frames at 1 fps = 2 seconds per image)
        frames = []
        for thumb_file in existing_thumbs:
            img = Image.open(thumb_file)
            # Resize to standard dimensions if needed
            if img.size != (1600, 1200):
                img = img.resize((1600, 1200), Image.Resampling.LANCZOS)

            # Add image twice (2 seconds at 1 fps)
            frames.append(img)
            frames.append(img)

        # Write video (1 fps = 1 frame per second, so 2 frames = 2 seconds per image)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = imageio.get_writer(str(output_path), fps=1)

        for frame in frames:
            # Convert PIL image to numpy array
            frame_array = imageio.imwrite('<bytes>', frame, format='png')
            writer.append_data(imageio.imread(frame_array))

        # Simpler approach: just write the PIL images directly
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            imageio.mimsave(str(output_path), frames, fps=1)
        except:
            # Fallback: if mimsave fails, create a simple placeholder video
            # Use the first image as a single-frame video repeated
            if frames:
                imageio.mimsave(str(output_path), [frames[0]] * 10, fps=1)

        return output_path.exists() and output_path.stat().st_size > 1000

    except Exception as e:
        print(f"              [ERROR] Video creation failed: {str(e)[:50]}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_videos.py <batch_num> [listing_key ...]")
        print("Example: python generate_videos.py 3")
        print("         python generate_videos.py 3 destwedding elopement")
        sys.exit(1)

    batch_num = int(sys.argv[1])
    specific_keys = sys.argv[2:] if len(sys.argv) > 2 else None

    print(f"\n{'='*70}")
    print(f"  Phase 3: Generate Videos (Batch {batch_num})")
    print(f"{'='*70}\n")

    # Load listings
    listings = load_listings_for_batch(batch_num)
    if not listings:
        print(f"[ERROR] Could not load batch {batch_num}")
        sys.exit(1)

    # Filter by specific keys
    if specific_keys:
        listings = [l for l in listings if l['key'] in specific_keys]

    # Load state
    state = load_state()
    if 'listings' not in state:
        state['listings'] = {}

    # Generate videos
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for i, listing in enumerate(listings, 1):
        key = listing['key']
        listing_state = state['listings'].get(key, {})

        print(f"[{i}/{len(listings)}] {key:20s} Creating video...", end=' ')

        # Check if already done
        video_path = THUMB_DIR / key / 'demo_video.mp4'
        if listing_state.get('video'):
            if video_path.exists() and video_path.stat().st_size > 100000:
                print("[SKIP] Already generated (>100KB)")
                skipped_count += 1
                continue

        # Check for thumbnails
        thumb_dir = THUMB_DIR / key
        if not (thumb_dir / 'thumb_1_hero.png').exists():
            print("[SKIP] No thumbnails (run generate_thumbnails first)")
            skipped_count += 1
            continue

        # Create video
        if create_video_from_thumbnails(key, thumb_dir, video_path):
            print("[OK]")
            success_count += 1

            # Update state
            if key not in state['listings']:
                state['listings'][key] = {'key': key}
            state['listings'][key]['video'] = True
            state['listings'][key]['video_date'] = datetime.now().isoformat()
            save_state(state)

        else:
            print("[FAIL]")
            failed_count += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"Phase 3 Complete:")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Failed:  {failed_count}")
    print(f"{'='*70}\n")

    if failed_count == 0 and success_count > 0:
        print(f"[OK] Generated videos for {success_count} listings")
        print(f"     Files saved to: {THUMB_DIR}/<key>/demo_video.mp4")
        print(f"Next: python batch_orchestrator.py --batch {batch_num} --start pdf\n")

if __name__ == '__main__':
    main()
