#!/usr/bin/env python3

import os
import json
import base64
from pathlib import Path
from openai import OpenAI
from multiprocessing import Pool

# Paths
SCREENSHOTS_DIR = "/Volumes/NextGlum/giallo/screenshots/"
CLUSTERS_FILE = Path(__file__).parent.parent / "data_clusters" / "clusters.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data_clusters" / "content_check.json"
MAX_WORKERS = 3

def get_client():
    """Create OpenAI client (called per process)."""
    return OpenAI(
        base_url="https://api.studio.nebius.com/v1/",
        api_key=os.environ.get("NEBIUS_API_KEY")
    )

def encode_image(image_path):
    """Read and base64 encode an image file."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def load_progress():
    """Load existing progress from output file."""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(data):
    """Save progress to output file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def check_image_content(image_path, client):
    """Send image to LLM to check for nudity."""
    encoded_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-VL-72B-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Analyze this image and determine if it contains any nudity.

Nudity includes:
- Bare breasts (exposed nipples)
- Bare buttocks
- Exposed genitalia
- Full frontal nudity

Does NOT include:
- Cleavage or revealing clothing
- Shirtless men
- Implied nudity (covered by sheets, shadows, etc.)
- Artistic statues or paintings

Reply ONLY with valid JSON in this exact format:
{"nudity": true} or {"nudity": false}

Be conservative - only mark as true if there is clear, unambiguous nudity visible."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content

    try:
        result = json.loads(content)
        return result
    except json.JSONDecodeError:
        # Try removing markdown code block syntax
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)
            return result
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response: {content}")
            return {"nudity": False}  # Default to false if parsing fails

def get_screenshot_path(filename):
    """Get full path to screenshot file."""
    # Format: videoname__0001.jpg
    if '__' not in filename:
        return None

    video_name = filename.rsplit('__', 1)[0]
    screenshot_path = Path(SCREENSHOTS_DIR) / video_name / filename

    if screenshot_path.exists():
        return screenshot_path

    return None

def process_screenshot(args):
    """Process a single screenshot (worker function)."""
    filename, client = args

    screenshot_path = get_screenshot_path(filename)
    if not screenshot_path:
        print(f"  ⚠️  Screenshot not found: {filename}")
        return filename, {"nudity": False, "error": "file_not_found"}

    try:
        result = check_image_content(screenshot_path, client)
        return filename, result
    except Exception as e:
        print(f"  ✗ Error processing {filename}: {e}")
        return filename, {"nudity": False, "error": str(e)}

def process_batch(screenshots_batch):
    """Process a batch of screenshots in a single worker process."""
    client = get_client()
    results = {}

    for i, filename in enumerate(screenshots_batch, 1):
        screenshot_path = get_screenshot_path(filename)
        if not screenshot_path:
            print(f"  ⚠️  Screenshot not found: {filename}")
            results[filename] = {"nudity": False, "error": "file_not_found"}
            continue

        try:
            result = check_image_content(screenshot_path, client)
            results[filename] = result

            if i % 10 == 0:
                print(f"  Processed {i}/{len(screenshots_batch)} in this batch")
        except Exception as e:
            print(f"  ✗ Error processing {filename}: {e}")
            results[filename] = {"nudity": False, "error": str(e)}

    return results

def main():
    print("=" * 70)
    print("Cluster Screenshot Content Checker")
    print("=" * 70)
    print("\nThis script checks all screenshots in clusters for nudity content.\n")

    # Load clusters
    print("Loading clusters...")
    with open(CLUSTERS_FILE) as f:
        clusters = json.load(f)

    # Get all unique screenshots (excluding cluster -1)
    all_screenshots = set()
    for cluster_id, screenshots in clusters.items():
        if cluster_id != "-1":
            all_screenshots.update(screenshots)

    print(f"Found {len(all_screenshots)} unique screenshots in clusters\n")

    # Load existing progress
    results = load_progress()
    already_processed = len(results)

    if already_processed > 0:
        print(f"Already processed: {already_processed} screenshots")
        print(f"Remaining: {len(all_screenshots) - already_processed} screenshots\n")

    # Filter out already processed screenshots
    to_process = [s for s in sorted(all_screenshots) if s not in results]

    if not to_process:
        print("✅ All screenshots already processed!")
        return

    print(f"Processing {len(to_process)} screenshots with {MAX_WORKERS} workers...\n")

    # Split screenshots into batches for each worker
    batch_size = len(to_process) // MAX_WORKERS + 1
    batches = [to_process[i:i + batch_size] for i in range(0, len(to_process), batch_size)]

    print(f"Split into {len(batches)} batches of ~{batch_size} screenshots each\n")

    # Process batches in parallel
    with Pool(processes=MAX_WORKERS) as pool:
        batch_results = pool.map(process_batch, batches)

    # Merge results
    for batch_result in batch_results:
        results.update(batch_result)
        # Save after each batch completes
        save_progress(results)

    print(f"\n✅ Processing complete!")
    print(f"Total screenshots checked: {len(results)}")

    # Count nudity
    nudity_count = sum(1 for v in results.values() if v.get("nudity", False))
    print(f"Screenshots with nudity: {nudity_count}")
    print(f"Screenshots without nudity: {len(results) - nudity_count}")
    print(f"\nResults saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
