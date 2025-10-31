#!/usr/bin/env python3

import json
import re
import base64
from pathlib import Path
from collections import Counter, defaultdict

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
SCREENSHOTS_DIR = Path("/Volumes/NextGlum/giallo/screenshots")
OUTPUT_JSON = Path(__file__).parent.parent / "apps" / "dupe-descriptions" / "duplicates.json"

def load_all_descriptions():
    """Load all descriptions from data/*.json files"""
    descriptions = []

    json_files = sorted(DATA_DIR.glob("*.json"))

    print(f"Loading descriptions from {len(json_files)} files...\n")

    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)

        for screenshot_name, screenshot_data in data.items():
            if 'description' in screenshot_data and screenshot_data['description']:
                descriptions.append({
                    'text': screenshot_data['description'],
                    'filename': screenshot_name,
                    'movie': json_file.stem
                })

    return descriptions

def clean_description(text):
    """Normalize description text for comparison"""
    # Convert to lowercase and strip whitespace
    text = text.lower().strip()
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text

def get_screenshot_path(filename):
    """Get full path to screenshot file"""
    if '__' not in filename:
        return None
    video_name = filename.rsplit('__', 1)[0]
    screenshot_path = SCREENSHOTS_DIR / video_name / filename
    if screenshot_path.exists():
        return screenshot_path
    return None

def encode_screenshot(filename):
    """Encode screenshot as base64"""
    screenshot_path = get_screenshot_path(filename)
    if not screenshot_path:
        return None
    try:
        with open(screenshot_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"  Error encoding {filename}: {e}")
        return None

def generate_duplicates_json(descriptions, duplicates):
    """Generate JSON file with top 20 duplicates and base64 encoded screenshots"""
    print(f"\n📝 Generating duplicates JSON with screenshots...")

    top_20_duplicates = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:20]

    output_data = []

    for i, (desc_text, count) in enumerate(top_20_duplicates, 1):
        print(f"  Processing duplicate {i}/20 ({count} instances)...")

        # Find all screenshots with this description
        matching_screenshots = []
        for d in descriptions:
            if clean_description(d['text']) == desc_text:
                encoded = encode_screenshot(d['filename'])
                if encoded:
                    matching_screenshots.append({
                        'filename': d['filename'],
                        'movie': d['movie'],
                        'image_data': encoded
                    })

        output_data.append({
            'rank': i,
            'description': desc_text,
            'count': count,
            'screenshots': matching_screenshots
        })

    # Save to JSON file
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"  ✅ Saved to {OUTPUT_JSON}")
    print(f"  Total file size: {OUTPUT_JSON.stat().st_size / 1024 / 1024:.2f} MB")

def extract_sentences(description):
    """Split description into individual sentences"""
    # Split on period, exclamation, or question mark
    sentences = re.split(r'[.!?]+', description)
    # Clean and filter empty sentences
    return [s.strip() for s in sentences if s.strip()]

def extract_key_phrases(description):
    """Extract key phrases/patterns from description"""
    text = description.lower()

    # Common patterns to look for
    patterns = {
        'color_descriptions': r'\b(vivid|bright|dark|shadowy|colorful|monochrome|sepia)\b',
        'emotions': r'\b(terror|fear|scream|cry|smile|laugh|shock|surprise|anxious|worried|tense)\b',
        'violence': r'\b(blood|knife|gun|murder|kill|stab|shoot|attack|wound|injury|dead|body)\b',
        'lighting': r'\b(shadow|darkness|light|lamp|candle|moonlight|sunlight|dim|bright)\b',
        'clothing': r'\b(dress|coat|suit|shirt|mask|gloves|hat|shoes|naked|nude)\b',
        'locations': r'\b(room|house|street|forest|beach|church|hotel|apartment|corridor|stairs)\b',
        'actions': r'\b(running|walking|standing|sitting|lying|holding|grabbing|pointing|looking|watching)\b',
        'characters': r'\b(woman|man|girl|boy|child|person|figure|stranger|victim|killer)\b'
    }

    found = defaultdict(list)
    for category, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            found[category].extend(matches)

    return found

def analyze_descriptions(descriptions):
    """Perform comprehensive analysis on descriptions"""

    print("=" * 80)
    print("DESCRIPTION ANALYSIS REPORT")
    print("=" * 80)
    print()

    # Basic statistics
    print(f"📊 BASIC STATISTICS")
    print(f"{'─' * 80}")
    print(f"Total descriptions: {len(descriptions)}")

    # Length statistics
    lengths = [len(d['text']) for d in descriptions]
    word_counts = [len(d['text'].split()) for d in descriptions]

    print(f"Average description length: {sum(lengths) / len(lengths):.1f} characters")
    print(f"Average word count: {sum(word_counts) / len(word_counts):.1f} words")
    print(f"Shortest description: {min(lengths)} characters")
    print(f"Longest description: {max(lengths)} characters")
    print()

    # Exact duplicates
    print(f"🔁 EXACT DUPLICATE DESCRIPTIONS")
    print(f"{'─' * 80}")
    cleaned_descriptions = [clean_description(d['text']) for d in descriptions]
    duplicate_counts = Counter(cleaned_descriptions)
    duplicates = {desc: count for desc, count in duplicate_counts.items() if count > 1}

    print(f"Unique descriptions: {len(duplicate_counts)}")
    print(f"Duplicate descriptions: {len(duplicates)}")
    print(f"Total duplicate instances: {sum(duplicates.values()) - len(duplicates)}")

    if duplicates:
        print(f"\nTop 20 most repeated descriptions:")
        for i, (desc, count) in enumerate(sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:20], 1):
            print(f"  {i:2d}. [{count:3d}x] {desc}")

        # Generate JSON file with screenshots
        generate_duplicates_json(descriptions, duplicates)
    print()

    # Sentence analysis
    print(f"📝 SENTENCE ANALYSIS")
    print(f"{'─' * 80}")
    all_sentences = []
    for d in descriptions:
        sentences = extract_sentences(d['text'])
        all_sentences.extend([s.lower().strip() for s in sentences])

    sentence_counts = Counter(all_sentences)
    repeated_sentences = {sent: count for sent, count in sentence_counts.items() if count > 5}

    print(f"Total sentences: {len(all_sentences)}")
    print(f"Unique sentences: {len(sentence_counts)}")
    print(f"Sentences repeated 5+ times: {len(repeated_sentences)}")

    if repeated_sentences:
        print(f"\nTop 20 most common sentences:")
        for i, (sent, count) in enumerate(sorted(repeated_sentences.items(), key=lambda x: x[1], reverse=True)[:20], 1):
            preview = sent[:80] + "..." if len(sent) > 80 else sent
            print(f"  {i:2d}. [{count:3d}x] {preview}")
    print()

    # Key phrase analysis
    print(f"🔍 KEY PHRASE ANALYSIS")
    print(f"{'─' * 80}")

    all_phrases = defaultdict(Counter)
    for d in descriptions:
        phrases = extract_key_phrases(d['text'])
        for category, words in phrases.items():
            all_phrases[category].update(words)

    for category in sorted(all_phrases.keys()):
        word_counts = all_phrases[category]
        total = sum(word_counts.values())
        print(f"\n{category.upper().replace('_', ' ')} (total mentions: {total}):")
        top_10 = word_counts.most_common(10)
        for word, count in top_10:
            percentage = (count / len(descriptions)) * 100
            print(f"  {word:15s}: {count:4d} ({percentage:5.1f}% of descriptions)")
    print()

    # Common word pairs (bigrams)
    print(f"🔤 COMMON WORD PAIRS")
    print(f"{'─' * 80}")

    all_words = []
    for d in descriptions:
        words = re.findall(r'\b[a-z]+\b', d['text'].lower())
        all_words.extend(words)

    # Create bigrams
    bigrams = [(all_words[i], all_words[i+1]) for i in range(len(all_words)-1)]
    bigram_counts = Counter(bigrams)

    # Filter out common stop words pairs
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has',
                  'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
                  'might', 'must', 'can', 'it', 'this', 'that', 'these', 'those'}

    filtered_bigrams = {bg: count for bg, count in bigram_counts.items()
                        if count > 5 and bg[0] not in stop_words and bg[1] not in stop_words}

    print(f"Top 30 most common word pairs (excluding stop words):")
    for i, (bigram, count) in enumerate(sorted(filtered_bigrams.items(), key=lambda x: x[1], reverse=True)[:30], 1):
        print(f"  {i:2d}. [{count:4d}x] {bigram[0]} {bigram[1]}")
    print()

    # Descriptions by movie
    print(f"🎬 DESCRIPTIONS BY MOVIE")
    print(f"{'─' * 80}")

    movie_counts = Counter([d['movie'] for d in descriptions])
    print(f"Movies with most descriptions:")
    for i, (movie, count) in enumerate(movie_counts.most_common(20), 1):
        print(f"  {i:2d}. {movie:60s}: {count:4d} descriptions")
    print()

    # Pattern frequency
    print(f"📈 PATTERN FREQUENCY SUMMARY")
    print(f"{'─' * 80}")

    pattern_stats = []
    for category, word_counts in all_phrases.items():
        total_mentions = sum(word_counts.values())
        descriptions_with_pattern = sum(1 for d in descriptions if any(w in d['text'].lower() for w in word_counts.keys()))
        percentage = (descriptions_with_pattern / len(descriptions)) * 100
        pattern_stats.append((category, total_mentions, descriptions_with_pattern, percentage))

    pattern_stats.sort(key=lambda x: x[3], reverse=True)

    print(f"{'Category':<25} {'Total Mentions':<15} {'Descriptions':<15} {'Percentage'}")
    print(f"{'-'*25} {'-'*15} {'-'*15} {'-'*10}")
    for category, mentions, desc_count, percentage in pattern_stats:
        cat_name = category.replace('_', ' ').title()
        print(f"{cat_name:<25} {mentions:<15} {desc_count:<15} {percentage:>6.1f}%")

    print()
    print("=" * 80)
    print("END OF REPORT")
    print("=" * 80)

def main():
    descriptions = load_all_descriptions()

    if not descriptions:
        print("No descriptions found!")
        return

    analyze_descriptions(descriptions)

if __name__ == "__main__":
    main()
