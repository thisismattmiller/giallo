#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from google import genai
from google.genai import types
import time

def load_data(filepath):
    """Load the screenshot data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_existing_embeddings(embeddings_filepath):
    """Load already processed embeddings from file."""
    if embeddings_filepath.exists():
        with open(embeddings_filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_embeddings(filepath, embeddings_data):
    """Save embeddings to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(embeddings_data, f, indent=2, ensure_ascii=False)
        f.write('\n')

def create_text_for_embedding(screenshot_data):
    """Create text string from tags and description."""
    tags_text = ', '.join(screenshot_data.get('tags', []))
    description = screenshot_data.get('description', '')

    # Combine tags and description
    text = f"{tags_text}. {description}".strip()
    return text if text else None

def get_unprocessed_screenshots(data, existing_embeddings):
    """Get list of screenshots that don't have embeddings yet and have content."""
    unprocessed = []
    for key, screenshot in data.items():
        if key not in existing_embeddings:
            text = create_text_for_embedding(screenshot)
            if text:
                unprocessed.append((key, screenshot, text))
    return unprocessed

def process_batch(client, batch_data):
    """Process a batch of screenshots and get their embeddings."""
    try:
        batch_texts = [text for _, _, text in batch_data]
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=batch_texts,
            config=types.EmbedContentConfig(task_type="CLUSTERING")
        )

        # Create dict of keys to embeddings
        embeddings_dict = {}
        for (key, _, _), embedding in zip(batch_data, result.embeddings):
            embeddings_dict[key] = embedding.values

        return embeddings_dict
    except Exception as e:
        print(f"Error processing batch: {e}")
        return None

def process_file(client, data_file, embeddings_dir):
    """Process a single data file."""
    print(f"\n{'='*80}")
    print(f"Processing: {data_file.name}")
    print(f"{'='*80}")

    # Set up output path
    embeddings_file = embeddings_dir / data_file.name

    # Load data
    print(f"Loading data from {data_file}...")
    data = load_data(data_file)
    total_screenshots = len(data)
    print(f"Total screenshots: {total_screenshots}")

    # Load existing embeddings if any
    print(f"Checking for existing embeddings in {embeddings_file}...")
    existing_embeddings = load_existing_embeddings(embeddings_file)
    print(f"Screenshots already processed: {len(existing_embeddings)}")

    # Get unprocessed screenshots
    unprocessed = get_unprocessed_screenshots(data, existing_embeddings)

    # Count how many were skipped due to empty content
    total_unprocessed = len([k for k in data.keys() if k not in existing_embeddings])
    empty_skipped = total_unprocessed - len(unprocessed)

    print(f"Screenshots to process: {len(unprocessed)}")
    if empty_skipped > 0:
        print(f"Skipping {empty_skipped} screenshots with empty content")

    if not unprocessed:
        print("All screenshots already have embeddings!")
        return True

    # Process in batches of 100
    batch_size = 100
    total_batches = (len(unprocessed) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(unprocessed))

        # Get current batch
        batch = unprocessed[start_idx:end_idx]

        print(f"\nProcessing batch {batch_num + 1}/{total_batches} ({len(batch)} screenshots)...")

        # Process the batch
        batch_embeddings = process_batch(client, batch)

        if batch_embeddings:
            # Merge with existing embeddings
            existing_embeddings.update(batch_embeddings)

            # Save to file after each batch
            print(f"Saving batch {batch_num + 1} to {embeddings_file}...")
            save_embeddings(embeddings_file, existing_embeddings)
            print(f"Batch {batch_num + 1} completed and saved.")

            # Small delay to avoid rate limiting
            if batch_num < total_batches - 1:
                time.sleep(1)
        else:
            print(f"Failed to process batch {batch_num + 1}. You can restart the script to continue.")
            return False

    print(f"\n✓ File completed! Total screenshots with embeddings: {len(existing_embeddings)}")
    return True

def main():
    # Set up paths
    data_dir = Path(__file__).parent.parent / 'data'
    embeddings_dir = Path(__file__).parent.parent / 'data_embeddings'

    if not data_dir.exists():
        print(f"Error: {data_dir} not found")
        sys.exit(1)

    # Create embeddings directory if it doesn't exist
    embeddings_dir.mkdir(exist_ok=True)
    print(f"Embeddings will be saved to: {embeddings_dir}")

    # Get all JSON files in data directory
    json_files = sorted([f for f in data_dir.glob('*.json')])

    if not json_files:
        print(f"No JSON files found in {data_dir}")
        sys.exit(1)

    print(f"\nFound {len(json_files)} JSON files to process")

    # Initialize Google AI client
    print("\nInitializing Google AI client...")
    api_key = os.environ.get("GOOGLE_GENAI")
    if not api_key:
        print("Error: GOOGLE_GENAI environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Process each file
    failed_files = []
    for i, data_file in enumerate(json_files, 1):
        print(f"\n[File {i}/{len(json_files)}]")
        success = process_file(client, data_file, embeddings_dir)
        if not success:
            failed_files.append(data_file.name)
            print(f"Failed to complete {data_file.name}. Continuing to next file...")

    # Final summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total files: {len(json_files)}")
    print(f"Successfully completed: {len(json_files) - len(failed_files)}")
    if failed_files:
        print(f"Failed: {len(failed_files)}")
        print("Failed files:")
        for filename in failed_files:
            print(f"  - {filename}")
    else:
        print("✓ All files processed successfully!")
    print(f"\nEmbeddings saved to: {embeddings_dir}")

if __name__ == "__main__":
    main()
