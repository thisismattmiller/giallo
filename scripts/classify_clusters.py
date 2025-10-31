#!/usr/bin/env python3
"""
Classify clusters using Gemini LLM based on screenshot descriptions.
Reads from data_clusters/clusters_with_descriptions.json and outputs to data_clusters/cluster_llm_labels.json
"""

from glob import escape
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types


def load_clusters_data(filepath):
    """Load the clusters with descriptions data."""
    print(f"Loading clusters from {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"  Loaded {len(data)} clusters")

    # Show summary
    total_screenshots = sum(len(cluster) for cluster in data.values())
    print(f"  Total screenshots: {total_screenshots:,}")

    return data


def classify_cluster(cluster_id, cluster_data, client, model="gemini-2.5-flash", max_descriptions=500):
    """Send cluster descriptions to LLM for classification."""

    descriptions = [item['description'] for item in cluster_data[:max_descriptions] if item.get('description')]

    if not descriptions:
        return "No descriptions available"

    # Prepare the prompt
    prompt = """Here is a sample of screenshot descriptions from a cluster of similar movie frames from Italian giallo films. I want you to return in one sentence the type of scenes they represent, a classification of sorts. The category should be specific to what the descriptions seem to all have in common the most. If there seems to be multiple categories that are very different go with the one that is more prevalent. Just return the classification, no other descriptor or reasoning text please. Here are the descriptions:

"""

    # Add each description on a new line
    for description in descriptions:
        # Clean description text (remove excessive whitespace)
        cleaned_description = ' '.join(description.split())
        # Escape any HTML code in the description
        cleaned_description = cleaned_description.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

        if cleaned_description:
            prompt += cleaned_description + "\n"

    print("SENDING")
    print(f"Cluster {cluster_id}: {len(descriptions)} descriptions")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=24576,
        ),
    )

    classification_results = ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print("Getting response...", flush=True)
        if chunk != None and chunk.text:
            classification_results += chunk.text

    # Extract the classification
    classification_results = classification_results.strip()

    # Clean up the classification (remove any extra text if present)
    # Take only the first line if multiple lines
    if '\n' in classification_results:
        classification_results = classification_results.split('\n')[0].strip()

    return classification_results


def load_existing_results(output_file):
    """Load existing results if available."""
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            return results
        except Exception as e:
            print(f"Warning: Could not load existing results: {e}")
    return None


def save_results(results, output_file):
    """Save results to file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def classify_all_clusters(data, output_file, delay=1.0):
    """Classify all clusters and save results incrementally."""

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set it with: export GEMINI_API_KEY='your-api-key'")
        sys.exit(1)

    print("\nInitializing Gemini client...")
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    # Check for existing results to resume from
    results = load_existing_results(output_file)

    if results and 'classifications' in results:
        existing_count = len(results['classifications'])
        if existing_count > 0:
            print(f"Found existing results with {existing_count} classifications")
            response = input("Resume from existing progress? (y/n): ")
            if response.lower() != 'y':
                results = None

    # Initialize results if not resuming
    if not results:
        results = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source_file': 'clusters_with_descriptions.json',
                'model': 'gemini-2.5-flash',
                'total_clusters': len(data),
                'max_descriptions_per_cluster': 500,
                'last_updated': datetime.now().isoformat()
            },
            'classifications': {}
        }
        print(f"Starting fresh classification of {len(data)} clusters...")
    else:
        # Update metadata for resumed run
        results['metadata']['last_updated'] = datetime.now().isoformat()
        print(f"Resuming classification...")

    print(f"Using {delay} second delay between API calls\n")

    # Track progress
    cluster_ids = sorted(data.keys(), key=lambda x: int(x))
    total_to_process = len(cluster_ids)
    already_processed = set(results['classifications'].keys())
    processed_count = len(already_processed)

    for i, cluster_id in enumerate(cluster_ids, 1):
        # Check if already processed and has a valid classification
        if cluster_id in already_processed:
            existing_classification = results['classifications'][cluster_id].get('classification', '')
            if existing_classification and existing_classification.strip():
                print(f"[{i}/{total_to_process}] Cluster {cluster_id} already classified: '{existing_classification}'")
                continue
            else:
                print(f"[{i}/{total_to_process}] Cluster {cluster_id} has empty classification, retrying...")

        cluster_data = data[cluster_id]
        num_screenshots = len(cluster_data)
        num_descriptions = sum(1 for item in cluster_data if item.get('description'))

        print(f"[{i}/{total_to_process}] Classifying cluster {cluster_id} ({num_screenshots} screenshots, {num_descriptions} descriptions)...", end=' ')

        try:
            # Get classification
            classification = classify_cluster(cluster_id, cluster_data, client)

            # Store result
            results['classifications'][cluster_id] = {
                'cluster_id': int(cluster_id),
                'classification': classification,
                'num_screenshots': num_screenshots,
                'num_descriptions': num_descriptions,
                'sample_descriptions': [item['description'] for item in cluster_data[:3] if item.get('description')],
                'classified_at': datetime.now().isoformat()
            }

            print(f"→ '{classification}'")

            # Save after each successful classification
            results['metadata']['last_updated'] = datetime.now().isoformat()
            save_results(results, output_file)

            # Only increment processed_count if this was a new classification (not a retry)
            if cluster_id not in already_processed:
                processed_count += 1

        except Exception as e:
            print(f"→ Error: {e}")
            # Save even on error to preserve progress
            save_results(results, output_file)

        # Rate limiting delay (except for last item)
        if i < total_to_process:
            time.sleep(delay)

    print(f"\nClassification complete! Processed {processed_count} clusters.")
    return results


def print_summary(results):
    """Print a summary of the classifications."""
    print("\n" + "="*60)
    print("CLUSTER CLASSIFICATION SUMMARY")
    print("="*60)

    classifications = results['classifications']

    # Get all unique classifications
    unique_classifications = {}
    for cluster_id, data in classifications.items():
        classification = data['classification']
        if classification not in unique_classifications:
            unique_classifications[classification] = []
        unique_classifications[classification].append(int(cluster_id))

    print(f"\n📊 Statistics:")
    print(f"  • Total clusters classified: {len(classifications)}")
    print(f"  • Unique classifications: {len(unique_classifications)}")

    print(f"\n🏷️  Top 10 Clusters by Size:")
    sorted_clusters = sorted(classifications.items(), key=lambda x: x[1]['num_screenshots'], reverse=True)[:10]
    for cluster_id, data in sorted_clusters:
        print(f"  Cluster {int(cluster_id):3d} ({data['num_screenshots']:3d} screenshots): {data['classification']}")

    print(f"\n📑 Grouped by Classification (showing groups with multiple clusters):")
    for classification, cluster_ids in sorted(unique_classifications.items()):
        if len(cluster_ids) > 1:
            print(f"  '{classification}': {len(cluster_ids)} clusters - {sorted(cluster_ids)}")

    # Check for errors
    error_count = sum(1 for data in classifications.values() if data['classification'].startswith('Error:') or data['classification'] == 'No descriptions available')
    if error_count > 0:
        print(f"\n⚠️  Warning: {error_count} clusters had classification errors or no descriptions")


def main():
    # Set up paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    input_file = base_dir / 'data_clusters' / 'clusters_with_descriptions.json'
    output_file = base_dir / 'data_clusters' / 'cluster_llm_labels.json'

    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        print("Please run extract_cluster_desc.py first.")
        sys.exit(1)

    # Parse command line arguments
    delay = 1.0  # Default delay between API calls
    if len(sys.argv) > 1:
        try:
            delay = float(sys.argv[1])
            print(f"📌 Using custom delay: {delay} seconds between API calls")
        except ValueError:
            print(f"Warning: Invalid delay '{sys.argv[1]}', using default: 1.0 seconds")

    try:
        print("="*60)
        print("LLM CLUSTER CLASSIFICATION")
        print("="*60)

        # Load data
        data = load_clusters_data(input_file)

        # Classify all clusters
        results = classify_all_clusters(data, output_file, delay=delay)

        # Print summary
        print_summary(results)

        print(f"\n✅ Classification complete!")
        print(f"   Results saved to: {output_file}")

        print(f"\n💡 Usage notes:")
        print(f"  • Classifications are stored in 'classifications' field")
        print(f"  • Each classification includes the cluster ID and screenshot count")
        print(f"  • Sample descriptions are included for reference")

        print(f"\n🔧 Adjust API rate limiting:")
        print(f"   python {Path(__file__).name} <delay_seconds>")
        print(f"   Example: python {Path(__file__).name} 2.0  # 2 second delay")

    except KeyboardInterrupt:
        print("\n\n⚠️  Classification interrupted by user")
        print("   Partial results may have been saved")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
