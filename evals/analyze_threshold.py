import json

with open('evals/results.json') as f:
    data = json.load(f)

print("Top similarity per post (regardless of guard):")
print("-" * 65)
for r in data['results']:
    top = r['matches'][0] if r['matches'] else None
    status_mark = "[matched] " if r['status'] == 'matched' else "[no match]"
    top_sim = top['similarity'] if top else 0
    top_cat = top['category'] if top else '?'
    top_file = top['filename'] if top else '?'
    post_title_short = r['post_title'][:40]
    print(f"{status_mark} Post {r['post_id']}: top={top_sim:.4f} ({top_file}/{top_cat}) | {post_title_short}")

# Would the system work with a lower threshold?
print()
print("What would happen with threshold = 0.40?")
print("-" * 65)
for r in data['results']:
    candidates_above_40 = [m for m in r['matches'] if m['similarity'] >= 0.40]
    correct_cats = r.get('expected_categories', [])
    best_above_40 = candidates_above_40[0] if candidates_above_40 else None
    if best_above_40:
        match_label = "CORRECT" if best_above_40.get('category') in correct_cats else f"WRONG ({best_above_40.get('category')})"
        print(f"  Post {r['post_id']}: {best_above_40['filename']} sim={best_above_40['similarity']:.4f} [{match_label}]")
    else:
        print(f"  Post {r['post_id']}: still no match above 0.40")
