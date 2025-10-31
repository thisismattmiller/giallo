import os
import json
import base64
from pathlib import Path
from openai import OpenAI
from multiprocessing import Pool
from functools import partial

SCREENSHOTS_DIR = "/Volumes/NextGlum/giallo/screenshots/"
DATA_DIR = "data"
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

def load_progress(output_file):
    """Load existing progress from output file."""
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            return json.load(f)
    return {}

def save_progress(output_file, data):
    """Save progress to output file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

def process_image(image_path, client):
    """Send image to LLM and get response."""
    encoded_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-VL-72B-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """We are making a visual index of every frame of a movie., these movies are Giallo Horror 1970s movies. Reply as a JSON object. Describe contents of  main visual components as a array, use terms that are general that would be the same across multiple movies like "woman, dress, knife" etc. Do not use complete sentences just return terms, subjects, tags. 
Also list out any visually striking images that have dynamic color or other visually striking aspects such as "vivid color" or "fog" or "closeup of eyes" etc. 
Also return up to three sentences describing the scene depicted.
Return it as JSON in this format: { "tags": [], "striking": [], "description": "xxxx"}"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
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
        return json.loads(cleaned)

def process_directory(dir_info):
    """Process all jpg images in a directory (worker function)."""
    dir_path, dir_name = dir_info
    output_file = os.path.join(DATA_DIR, f"{dir_name}.json")

    # Create client for this worker process
    client = get_client()

    # Load existing progress
    results = load_progress(output_file)

    # Get all jpg files
    jpg_files = sorted([f for f in os.listdir(dir_path) if f.lower().endswith('.jpg')])

    print(f"[{dir_name}] Processing directory")
    print(f"[{dir_name}] Found {len(jpg_files)} images, {len(results)} already processed")

    processed = 0
    errors = 0

    for jpg_file in jpg_files:
        # Skip if already processed
        if jpg_file in results:
            continue

        image_path = os.path.join(dir_path, jpg_file)

        try:
            result = process_image(image_path, client)
            result['file_name'] = jpg_file
            results[jpg_file] = result

            # Save progress after each image
            save_progress(output_file, results)
            processed += 1

            if processed % 10 == 0:
                print(f"[{dir_name}] Processed {processed}/{len(jpg_files) - len(results) + processed}")
        except Exception as e:
            print(f"[{dir_name}] Error processing {jpg_file}: {e}")
            errors += 1
            continue

    print(f"[{dir_name}] Completed: {len(results)}/{len(jpg_files)} total ({processed} new, {errors} errors)\n")
    return dir_name

def main():
    """Main function to process all directories."""
    if not os.path.exists(SCREENSHOTS_DIR):
        print(f"Error: Screenshots directory not found: {SCREENSHOTS_DIR}")
        return

    # Get all subdirectories
    directories = [d for d in os.listdir(SCREENSHOTS_DIR)
                   if os.path.isdir(os.path.join(SCREENSHOTS_DIR, d))]

    print(f"Found {len(directories)} directories to process")
    print(f"Using {MAX_WORKERS} worker processes\n")

    # Prepare directory info tuples
    dir_infos = [(os.path.join(SCREENSHOTS_DIR, d), d) for d in sorted(directories)]

    # Process directories in parallel using multiprocessing pool
    with Pool(processes=MAX_WORKERS) as pool:
        completed = pool.map(process_directory, dir_infos)

    print(f"\nAll directories processed! Completed: {len(completed)}")

if __name__ == "__main__":
    main()
