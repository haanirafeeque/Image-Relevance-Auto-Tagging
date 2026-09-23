"""
Verification script for Phase 4: Text Embeddings, Matching Engine, and Mismatch Guard.
"""

from app.embeddings import embed_all_posts, get_or_create_image_embedding
from app.matching import match_images_for_post
from app.database import run_query

print("1. Embedding all posts in database...")
count = embed_all_posts()
print(f"Posts embedded: {count}")

print("\n2. Ensuring processed images have embeddings...")
processed_imgs = run_query("SELECT id, filename FROM images WHERE status = 'processed'")
for img in processed_imgs:
    emb = get_or_create_image_embedding(img["id"])
    print(f" -> {img['filename']} embedded: {emb is not None} (len={len(emb) if emb else 0})")

print("\n3. Testing matching for Post 37 (The Behavior of Red Foxes in the Wild)...")
res_fox = match_images_for_post(37, top_k=5)
print(f"Post Title: {res_fox['post']['title']}")
print(f"Status: {res_fox['status']}")
if res_fox['best_match']:
    print(f"Best Match: {res_fox['best_match']['image']['filename']} (Similarity: {res_fox['best_match']['similarity']})")
for m in res_fox['matches']:
    print(f" -> Rank {m['rank']}: {m['image']['filename']} | Sim: {m['similarity']} | Guard: {m['guard_status']} | Reason: {m['reason']}")

print("\n4. Testing matching for Post 39 (Gray Wolves: Pack Dynamics and Hunting Strategies)...")
res_wolf = match_images_for_post(39, top_k=5)
print(f"Post Title: {res_wolf['post']['title']}")
print(f"Status: {res_wolf['status']}")
if res_wolf['best_match']:
    print(f"Best Match: {res_wolf['best_match']['image']['filename']} (Similarity: {res_wolf['best_match']['similarity']})")
else:
    print("Best Match: None (no candidate passed the guard)")
for m in res_wolf['matches']:
    print(f" -> Rank {m['rank']}: {m['image']['filename']} | Sim: {m['similarity']} | Guard: {m['guard_status']} | Reason: {m['reason']}")

print("\n5. Checking suggestions table in PostgreSQL...")
suggestions = run_query("SELECT id, post_id, image_id, similarity, guard_status, review_status FROM suggestions ORDER BY id DESC LIMIT 5")
for s in suggestions:
    print(f" -> Suggestion #{s['id']}: Post {s['post_id']} -> Image {s['image_id']} (Sim: {s['similarity']}) Guard: {s['guard_status']}, Review: {s['review_status']}")
