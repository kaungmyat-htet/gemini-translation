import os
import sys
import argparse
import csv
import pandas as pd
from google import genai

from dotenv import load_dotenv

load_dotenv()

def clean_text(text: str):
    """Remove newlines and extra spaces from text"""
    if not text:
        return text

    # Replace newlines with space
    text = text.replace('\r', ' ').replace('\n', ' ')
    return ' '.join(text.split())

def translate(api_key: str, text: str, source: str, target: str) -> str:
    """Translate text from source language into target language"""
    client = genai.Client(api_key=api_key)

    prompt = f"Translate the following {source} text to {target}:\n\n\"{text}\""
    token_usage = 0
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        translation = response.text.strip()
        translation = clean_text(text=translation)
        if hasattr(response, 'usage_metadata'):
            token_usage = response.usage_metadata.total_token_count
        else:
            token_usage = 0
            print("Warning: usage_metadata not found in response. Token usage might not be available for this request.")

    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            print("\nError: Daily quota exceeded (HTTP 429 - RESOURCE_EXHAUSTED).")
            print("You’ve hit the 500 requests/day limit for your Gemini API free tier.")
            print("More info: https://ai.google.dev/gemini-api/docs/rate-limits")
            sys.exit(1)
        else:
            print(f"Error during translation: {e}")
            sys.exit(1)
    return translation, token_usage


def main():
    parser = argparse.ArgumentParser(description='Translate from one language to another using Gemini API')

    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('output_file', help='Path to output CSV file')
    parser.add_argument('--api-key', default=None, help='Gemini API key (optional, will fallback to GEMINI_API_KEY from .env)')
    parser.add_argument('--start', type=int, default=0, help='Start row index (inclusive)')
    parser.add_argument('--end', type=int, default=None, help='End row index (exclusive)')
    parser.add_argument('--source', default='English', help='Source Language')
    parser.add_argument('--target', default='Myanmar', help='Target Language')

    args = parser.parse_args() 

    input_filepath = args.input_file
    output_filepath = args.output_file

    api_key = args.api_key or os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Error: Gemini API key not provided. Use --api-key or set GEMINI_API_KEY in .env file.")
        sys.exit(1)

    # check if input filepath exists
    if not os.path.exists(input_filepath):
        print(f"Error: Input file 'f{input_filepath}' does not exists.")
        sys.exit(1)

    try:
        df = pd.read_csv(input_filepath)
        print(f"Loaded {len(df)} rows from {input_filepath}")
    except Exception as e:
        print(f"Error reading input file: {e}. Please make sure it is csv file.")
        sys.exit(1)

    if os.path.exists(output_filepath):
        try:
            translated_df = pd.read_csv(output_filepath)
            translated_ids = set(translated_df['context'])
            print(f'Found existing output file with {len(translated_ids)}')
        except Exception as e:
            print(f"Error reading existing output file: {e}")
            translated_ids = set()

    else:
        # Create new output file with header
        try:
            with open(output_filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['context', 'id', 'context_my'])
            translated_ids = set()
            print(f"Created new output file: {output_filepath}")
        except Exception as e:
            print(f"Error creating output file: {e}")
            sys.exit(1)

    start = args.start
    end = args.end if args.end is not None else len(df)

    total_rows = len(df)
    processed_count = 0
    skipped_count = 0
    total_token_usage = 0

    for index in range(start, min(end, total_rows)):
        row = df.iloc[index]
        context = row['context']

        if context in translated_ids:
            skipped_count += 1
            continue
        
        token_usage = 0
        try:
            translated_context, token_usage = translate(api_key=api_key, text=context, source=args.source, target=args.target)
            processed_count += 1
            total_token_usage += token_usage
        except Exception as e:
            print(f"Error translating row {index}: {e}")
            print(f"Might out of request per day")
            sys.exit(1)

        try:
            with open(output_filepath, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    row['context'],
                    row['ids'],
                    str(translated_context)
                ])
            print(f"Row {index+1}/{total_rows} translated and written. Token Usage: {token_usage}. Total Token Usage: {total_token_usage} (Processed: {processed_count}, Skipped: {skipped_count})")

        except Exception as e:
            print(f"Error writing row {index}: {e}")

    print(f"\nTranslation complete!")
    print(f"Total rows: {total_rows}")
    print(f"Newly processed: {processed_count}")
    print(f"Skipped (already processed): {skipped_count}")
    print(f"Output saved to: {output_filepath}")
    
    
if __name__ == "__main__":
    main()
