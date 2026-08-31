import json
import os
import difflib

def generate_visual_diff():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jsonl_path = os.path.join(base_dir, 'evaluation_results.jsonl')

    if not os.path.exists(jsonl_path):
        print(f"Error: {jsonl_path} not found.")
        return

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=60)
    drift_count = 0

    for line in lines:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            print("WARNING: Skipping corrupted JSON line")
            continue
        if r.get('sentinel_status') == 'DRIFT DETECTED':
            drift_count += 1
            url = r.get('citation_url', 'Unknown URL')
            
            # Safely fallback to full text if snippets aren't explicitly keyed
            archived = r.get('archived_text_snippet', r.get('archived_text', ''))
            live = r.get('live_text_snippet', r.get('live_text', ''))

            # make_file includes the native CSS required for red/green highlighting
            html_content = differ.make_file(
                archived.splitlines(), 
                live.splitlines(), 
                fromdesc=f"Archived Snapshot (Historical): {url}", 
                todesc=f"Live Web Text (Current): {url}", 
                context=True, 
                numlines=3
            )

            html_path = os.path.join(base_dir, f'drift_visualization_{drift_count}.html')
            with open(html_path, 'w', encoding='utf-8') as out_f:
                out_f.write(html_content)
            
            print(f"Generated {html_path} for {url}")

    if drift_count == 0:
        print("No DRIFT DETECTED cases found in the dataset.")

if __name__ == '__main__':
    generate_visual_diff()
