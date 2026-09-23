"""
Seed script — downloads sample images and populates the database.

Downloads 40 images (10 per category: fox, wolf, dog, bear) from Pexels/Pixabay
(free-to-use, no attribution required) and creates 10+ blog posts.

Usage: python -m scripts.seed_data
"""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from app.database import get_connection, run_query, run_migration

# --- Image URLs ---
# All from Pexels (free license) — small size for fast download
# Each tuple: (filename, url, category_hint)

IMAGES = [
    # ---- FOX (10 images) ----
    ("fox_01.jpg", "https://images.pexels.com/photos/247399/pexels-photo-247399.jpeg?w=400", "fox"),
    ("fox_02.jpg", "https://images.pexels.com/photos/271932/pexels-photo-271932.jpeg?w=400", "fox"),
    ("fox_03.jpg", "https://images.pexels.com/photos/1587840/pexels-photo-1587840.jpeg?w=400", "fox"),
    ("fox_04.jpg", "https://images.pexels.com/photos/2295744/pexels-photo-2295744.jpeg?w=400", "fox"),
    ("fox_05.jpg", "https://images.pexels.com/photos/1172000/pexels-photo-1172000.jpeg?w=400", "fox"),
    ("fox_06.jpg", "https://images.pexels.com/photos/5774645/pexels-photo-5774645.jpeg?w=400", "fox"),
    ("fox_07.jpg", "https://images.pexels.com/photos/6431298/pexels-photo-6431298.jpeg?w=400", "fox"),
    ("fox_08.jpg", "https://images.pexels.com/photos/1661535/pexels-photo-1661535.jpeg?w=400", "fox"),
    ("fox_09.jpg", "https://images.pexels.com/photos/2661859/pexels-photo-2661859.jpeg?w=400", "fox"),
    ("fox_10.jpg", "https://images.pexels.com/photos/5732513/pexels-photo-5732513.jpeg?w=400", "fox"),

    # ---- WOLF (10 images) ----
    ("wolf_01.jpg", "https://images.pexels.com/photos/1420440/pexels-photo-1420440.jpeg?w=400", "wolf"),
    ("wolf_02.jpg", "https://images.pexels.com/photos/2361/nature-animal-wolf-wilderness.jpg?w=400", "wolf"),
    ("wolf_03.jpg", "https://images.pexels.com/photos/4932520/pexels-photo-4932520.jpeg?w=400", "wolf"),
    ("wolf_04.jpg", "https://images.pexels.com/photos/56866/garden-rose-red-pink-56866.jpeg?w=400", "wolf"),
    ("wolf_05.jpg", "https://images.pexels.com/photos/4588435/pexels-photo-4588435.jpeg?w=400", "wolf"),
    ("wolf_06.jpg", "https://images.pexels.com/photos/4555468/pexels-photo-4555468.jpeg?w=400", "wolf"),
    ("wolf_07.jpg", "https://images.pexels.com/photos/3396657/pexels-photo-3396657.jpeg?w=400", "wolf"),
    ("wolf_08.jpg", "https://images.pexels.com/photos/1592377/pexels-photo-1592377.jpeg?w=400", "wolf"),
    ("wolf_09.jpg", "https://images.pexels.com/photos/4947734/pexels-photo-4947734.jpeg?w=400", "wolf"),
    ("wolf_10.jpg", "https://images.pexels.com/photos/4932541/pexels-photo-4932541.jpeg?w=400", "wolf"),

    # ---- DOG (10 images) ----
    ("dog_01.jpg", "https://images.pexels.com/photos/1108099/pexels-photo-1108099.jpeg?w=400", "dog"),
    ("dog_02.jpg", "https://images.pexels.com/photos/1805164/pexels-photo-1805164.jpeg?w=400", "dog"),
    ("dog_03.jpg", "https://images.pexels.com/photos/2253275/pexels-photo-2253275.jpeg?w=400", "dog"),
    ("dog_04.jpg", "https://images.pexels.com/photos/1254140/pexels-photo-1254140.jpeg?w=400", "dog"),
    ("dog_05.jpg", "https://images.pexels.com/photos/58997/pexels-photo-58997.jpeg?w=400", "dog"),
    ("dog_06.jpg", "https://images.pexels.com/photos/406014/pexels-photo-406014.jpeg?w=400", "dog"),
    ("dog_07.jpg", "https://images.pexels.com/photos/1629781/pexels-photo-1629781.jpeg?w=400", "dog"),
    ("dog_08.jpg", "https://images.pexels.com/photos/2607544/pexels-photo-2607544.jpeg?w=400", "dog"),
    ("dog_09.jpg", "https://images.pexels.com/photos/825947/pexels-photo-825947.jpeg?w=400", "dog"),
    ("dog_10.jpg", "https://images.pexels.com/photos/160846/french-bulldog-summer-smile-joy-160846.jpeg?w=400", "dog"),

    # ---- BEAR (10 images) ----
    ("bear_01.jpg", "https://images.pexels.com/photos/164474/pexels-photo-164474.jpeg?w=400", "bear"),
    ("bear_02.jpg", "https://images.pexels.com/photos/35435/pexels-photo.jpg?w=400", "bear"),
    ("bear_03.jpg", "https://images.pexels.com/photos/3551498/pexels-photo-3551498.jpeg?w=400", "bear"),
    ("bear_04.jpg", "https://images.pexels.com/photos/1068554/pexels-photo-1068554.jpeg?w=400", "bear"),
    ("bear_05.jpg", "https://images.pexels.com/photos/2113940/pexels-photo-2113940.jpeg?w=400", "bear"),
    ("bear_06.jpg", "https://images.pexels.com/photos/1068557/pexels-photo-1068557.jpeg?w=400", "bear"),
    ("bear_07.jpg", "https://images.pexels.com/photos/3689532/pexels-photo-3689532.jpeg?w=400", "bear"),
    ("bear_08.jpg", "https://images.pexels.com/photos/357159/pexels-photo-357159.jpeg?w=400", "bear"),
    ("bear_09.jpg", "https://images.pexels.com/photos/1265893/pexels-photo-1265893.jpeg?w=400", "bear"),
    ("bear_10.jpg", "https://images.pexels.com/photos/2668606/pexels-photo-2668606.jpeg?w=400", "bear"),
]


# --- Blog posts ---
POSTS = [
    {
        "title": "The Behavior of Red Foxes in the Wild",
        "content": "Red foxes are among the most adaptable wild animals. They thrive in forests, grasslands, and even urban areas. Their diet includes small mammals, birds, and berries. Foxes are known for their cunning hunting strategies and their ability to survive harsh winters by growing thick fur coats."
    },
    {
        "title": "Understanding Fox Communication and Social Habits",
        "content": "Foxes communicate through a range of vocalizations including barks, screams, and howls. They use scent marking to establish territory boundaries. Despite being perceived as solitary animals, foxes can form small family groups, especially during the breeding season."
    },
    {
        "title": "Gray Wolves: Pack Dynamics and Hunting Strategies",
        "content": "Gray wolves live in structured packs with a clear hierarchy. The alpha pair leads the group in hunting large prey like elk and deer. Pack cooperation allows wolves to take down animals much larger than themselves. Wolves can travel up to 30 miles in a single day while hunting."
    },
    {
        "title": "Wolf Conservation Efforts in North America",
        "content": "Wolf populations were nearly wiped out in the lower 48 states by the mid-20th century. Reintroduction programs, particularly in Yellowstone National Park, have been remarkably successful. The return of wolves has had cascading effects on the ecosystem, including changes in elk behavior and river patterns."
    },
    {
        "title": "Best Dog Breeds for Active Families",
        "content": "Active families benefit from energetic dog breeds like Labrador Retrievers, Border Collies, and Australian Shepherds. These breeds need daily exercise and mental stimulation. Regular walks, fetch games, and agility training keep them healthy and prevent behavioral issues."
    },
    {
        "title": "Training Your Puppy: A Complete Beginner's Guide",
        "content": "Puppy training should start early with basic commands like sit, stay, and come. Positive reinforcement with treats and praise works better than punishment. Consistency is key — all family members should use the same commands. Socialization with other dogs and people during the first few months is critical."
    },
    {
        "title": "Brown Bears: Giants of the Forest",
        "content": "Brown bears are among the largest land predators, with males weighing up to 1,500 pounds. They are omnivores that eat fish, berries, roots, and small mammals. During salmon runs, brown bears gather at rivers and can catch dozens of fish per day. In autumn, they enter a period of hyperphagia, eating constantly to prepare for hibernation."
    },
    {
        "title": "Bear Safety Tips for Hikers and Campers",
        "content": "When hiking in bear country, always carry bear spray and know how to use it. Store food in bear-proof containers or hang it from a tree at least 10 feet high. Make noise while hiking to avoid surprising a bear. If you encounter a bear, stay calm, speak in a low voice, and slowly back away without running."
    },
    {
        "title": "The Differences Between Wild Canids: Foxes, Wolves, and Dogs",
        "content": "Foxes, wolves, and domestic dogs all belong to the family Canidae but have evolved very differently. Wolves are the largest and live in packs. Foxes are smaller and typically solitary. Dogs were domesticated from wolves over 15,000 years ago and have been bred into hundreds of distinct breeds with wildly different traits."
    },
    {
        "title": "Wildlife Photography: Capturing Animals in Their Natural Habitat",
        "content": "Wildlife photography requires patience, the right equipment, and knowledge of animal behavior. A telephoto lens of at least 200mm is essential for keeping a safe distance. Early morning and late afternoon provide the best natural lighting. Understanding an animal's habits helps predict where and when to find them."
    },
    {
        "title": "How Polar Bears Adapt to Arctic Conditions",
        "content": "Polar bears have evolved remarkable adaptations for life in the Arctic. Their white fur provides camouflage against snow, while a thick layer of blubber insulates them from freezing temperatures. Their large paws act as snowshoes and paddles for swimming. Polar bears are the only bear species considered marine mammals."
    },
    {
        "title": "The Intelligence and Loyalty of Working Dogs",
        "content": "Working dogs serve in roles ranging from search and rescue to therapy and assistance. Breeds like German Shepherds, Golden Retrievers, and Belgian Malinois excel in these tasks due to their intelligence and trainability. The bond between a working dog and its handler is built on trust, consistent training, and mutual respect."
    },
]


def download_images(image_dir):
    """Download all seed images to data/images/."""
    os.makedirs(image_dir, exist_ok=True)
    downloaded = 0
    failed = 0

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for filename, url, _category in IMAGES:
            filepath = os.path.join(image_dir, filename)

            # Skip if already downloaded
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                print(f"  Already exists: {filename}")
                downloaded += 1
                continue

            try:
                print(f"  Downloading: {filename}...", end=" ")
                response = client.get(url)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(response.content)

                size_kb = len(response.content) / 1024
                print(f"OK ({size_kb:.0f} KB)")
                downloaded += 1

            except Exception as e:
                print(f"FAILED: {e}")
                failed += 1

    return downloaded, failed


def seed_images(image_dir):
    """Insert image records into the database."""
    conn = get_connection()
    try:
        cur = conn.cursor()

        for filename, _url, _category in IMAGES:
            filepath = os.path.join(image_dir, filename)
            if not os.path.exists(filepath):
                continue

            # Check if already seeded
            cur.execute("SELECT id FROM images WHERE filename = %s", (filename,))
            if cur.fetchone():
                continue

            cur.execute(
                """INSERT INTO images (filename, path, status)
                   VALUES (%s, %s, 'pending')""",
                (filename, filepath)
            )

        conn.commit()
        print("Image records inserted.")
    finally:
        conn.close()


def seed_posts():
    """Insert blog posts into the database."""
    conn = get_connection()
    try:
        cur = conn.cursor()

        for post in POSTS:
            # Check if already seeded
            cur.execute("SELECT id FROM posts WHERE title = %s", (post["title"],))
            if cur.fetchone():
                continue

            cur.execute(
                "INSERT INTO posts (title, content) VALUES (%s, %s)",
                (post["title"], post["content"])
            )

        conn.commit()
        print("Post records inserted.")
    finally:
        conn.close()


def verify_seed():
    """Print counts to verify seeding worked."""
    images = run_query("SELECT COUNT(*) as count FROM images")
    posts = run_query("SELECT COUNT(*) as count FROM posts")

    img_count = images[0]["count"]
    post_count = posts[0]["count"]

    print(f"\nDatabase contents:")
    print(f"  Images: {img_count}")
    print(f"  Posts:  {post_count}")

    # Show category breakdown
    categories = run_query(
        """SELECT
             CASE
               WHEN filename LIKE 'fox%%' THEN 'fox'
               WHEN filename LIKE 'wolf%%' THEN 'wolf'
               WHEN filename LIKE 'dog%%' THEN 'dog'
               WHEN filename LIKE 'bear%%' THEN 'bear'
               ELSE 'other'
             END as category,
             COUNT(*) as count
           FROM images
           GROUP BY
             CASE
               WHEN filename LIKE 'fox%%' THEN 'fox'
               WHEN filename LIKE 'wolf%%' THEN 'wolf'
               WHEN filename LIKE 'dog%%' THEN 'dog'
               WHEN filename LIKE 'bear%%' THEN 'bear'
               ELSE 'other'
             END
           ORDER BY category"""
    )
    print(f"\n  By category:")
    for cat in categories:
        print(f"    {cat['category']}: {cat['count']}")

    if img_count >= 40 and post_count >= 10:
        print(f"\n[OK] Seed verified: {img_count} images, {post_count} posts")
    else:
        print(f"\n[!!] Seed incomplete: expected 40+ images and 10+ posts")

    return img_count, post_count


def main():
    image_dir = os.path.join(os.path.dirname(__file__), "..", "data", "images")
    image_dir = os.path.abspath(image_dir)

    print("=" * 50)
    print("SEED DATA SCRIPT")
    print("=" * 50)

    # Step 1: Run migration (safe to re-run with IF NOT EXISTS)
    migration_path = os.path.join(os.path.dirname(__file__), "..", "migrations", "001_create_tables.sql")
    print("\n1. Running migration...")
    run_migration(os.path.abspath(migration_path))

    # Step 2: Download images
    print(f"\n2. Downloading images to {image_dir}...")
    downloaded, failed = download_images(image_dir)
    print(f"   Downloaded: {downloaded}, Failed: {failed}")

    # Step 3: Seed database
    print("\n3. Seeding images...")
    seed_images(image_dir)

    print("\n4. Seeding posts...")
    seed_posts()

    # Step 4: Verify
    print("\n5. Verifying...")
    verify_seed()


if __name__ == "__main__":
    main()
