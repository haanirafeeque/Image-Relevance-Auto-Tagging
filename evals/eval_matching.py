"""
Evaluation suite — runs the matching engine across all blog posts and
produces a structured report of match rates, guard rejections, and
subject accuracy.

Output:
  - Per-post table printed to stdout
  - evals/results.json for further analysis
"""

import json
import os
import sys
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import run_query
from app.matching import match_images_for_post
from app.config import settings

# Keywords that define each category, used for subject accuracy scoring
CATEGORY_KEYWORDS = {
    "fox": ["fox", "foxes", "vixen"],
    "wolf": ["wolf", "wolves"],
    "dog": ["dog", "dogs", "puppy", "puppies", "canine", "retriever"],
    "bear": ["bear", "bears", "cub", "polar bear", "grizzly"],
}

OUTPUT_PATH = Path(__file__).resolve().parent / "results.json"


def expected_categories_for_post(title: str) -> set[str]:
    """Extract expected animal categories from a post title."""
    title_lower = title.lower()
    return {
        cat for cat, kws in CATEGORY_KEYWORDS.items()
        if any(kw in title_lower for kw in kws)
    }


def run_evaluation():
    posts = run_query("SELECT id, title FROM posts ORDER BY id")
    total_posts = len(posts)

    results = []
    matched_count = 0
    no_match_count = 0
    subject_correct = 0
    subject_evaluated = 0

    all_approved_similarities = []
    total_candidates = 0
    total_rejected = 0

    print("=" * 72)
    print(f"{'AI Image Matching Evaluation':^72}")
    print(f"{'Similarity threshold: ' + str(settings.similarity_threshold):^72}")
    print("=" * 72)
    print()

    for post in posts:
        post_id = post["id"]
        post_title = post["title"]

        result = match_images_for_post(post_id, top_k=10)

        matches = result["matches"]
        best_match = result["best_match"]
        status = result["status"]

        n_candidates = len(matches)
        n_rejected = sum(1 for m in matches if m["guard_status"] == "rejected")
        n_approved = n_candidates - n_rejected

        total_candidates += n_candidates
        total_rejected += n_rejected

        if best_match:
            matched_count += 1
            all_approved_similarities.append(best_match["similarity"])

            # Check subject accuracy
            expected_cats = expected_categories_for_post(post_title)
            if expected_cats:
                subject_evaluated += 1
                img_category = (best_match["image"].get("category") or "").lower()
                if img_category in expected_cats:
                    subject_correct += 1
                    accuracy_label = "[CORRECT]"
                else:
                    accuracy_label = f"[WRONG: got {img_category}]"
            else:
                accuracy_label = "[general]"
        else:
            no_match_count += 1
            accuracy_label = ""

        # Format per-post output
        best_info = (
            f"{best_match['image']['filename']} (sim={best_match['similarity']:.4f})"
            if best_match else "None"
        )
        print(f"Post {post_id}: {post_title}")
        print(f"  Status    : {status}")
        print(f"  Best match: {best_info} {accuracy_label}")
        print(f"  Candidates: {n_candidates} total, {n_rejected} rejected, {n_approved} approved")
        if matches:
            print(f"  Top ranked:")
            for m in matches[:3]:
                icon = "[OK]" if m["guard_status"] == "approved" else "[!!]"
                print(
                    f"    {icon} Rank {m['rank']}: {m['image']['filename']} "
                    f"({m['image'].get('category','?')}) sim={m['similarity']:.4f} "
                    f"| {m['reason'][:60]}"
                )
        print()

        results.append({
            "post_id": post_id,
            "post_title": post_title,
            "status": status,
            "best_match_filename": best_match["image"]["filename"] if best_match else None,
            "best_match_similarity": best_match["similarity"] if best_match else None,
            "best_match_category": best_match["image"].get("category") if best_match else None,
            "expected_categories": sorted(expected_categories_for_post(post_title)),
            "n_candidates": n_candidates,
            "n_rejected": n_rejected,
            "n_approved": n_approved,
            "matches": [
                {
                    "rank": m["rank"],
                    "filename": m["image"]["filename"],
                    "category": m["image"].get("category"),
                    "similarity": m["similarity"],
                    "guard_status": m["guard_status"],
                    "reason": m["reason"],
                }
                for m in matches
            ],
        })

    # Summary statistics
    match_rate = matched_count / total_posts * 100
    rejection_rate = total_rejected / total_candidates * 100 if total_candidates else 0
    subject_accuracy = subject_correct / subject_evaluated * 100 if subject_evaluated else 0
    avg_sim = sum(all_approved_similarities) / len(all_approved_similarities) if all_approved_similarities else 0
    min_sim = min(all_approved_similarities) if all_approved_similarities else 0
    max_sim = max(all_approved_similarities) if all_approved_similarities else 0

    print("=" * 72)
    print("EVALUATION SUMMARY")
    print("=" * 72)
    print(f"  Posts evaluated        : {total_posts}")
    print(f"  Matched (confident)    : {matched_count}  ({match_rate:.1f}%)")
    print(f"  No confident match     : {no_match_count}")
    print(f"  Subject accuracy       : {subject_correct}/{subject_evaluated} ({subject_accuracy:.1f}%)")
    print(f"  Guard rejection rate   : {total_rejected}/{total_candidates} ({rejection_rate:.1f}%)")
    print(f"  Similarity (approved)  : min={min_sim:.4f}, avg={avg_sim:.4f}, max={max_sim:.4f}")
    print("=" * 72)

    # Save JSON results
    output = {
        "summary": {
            "total_posts": total_posts,
            "matched": matched_count,
            "no_confident_match": no_match_count,
            "match_rate_pct": round(match_rate, 2),
            "subject_accuracy_pct": round(subject_accuracy, 2),
            "guard_rejection_rate_pct": round(rejection_rate, 2),
            "similarity_min": round(min_sim, 4),
            "similarity_avg": round(avg_sim, 4),
            "similarity_max": round(max_sim, 4),
            "similarity_threshold": settings.similarity_threshold,
            "min_vision_confidence": settings.min_vision_confidence,
        },
        "results": results,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed results written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_evaluation()
