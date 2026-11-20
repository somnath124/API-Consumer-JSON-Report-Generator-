import json
from collections import Counter
from pathlib import Path

import requests

BASE_URL = "https://jsonplaceholder.typicode.com"
REPORT_PATH = Path(__file__).resolve().parent / "report.json"
TIMEOUT = 10


def fetch_data(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        content_type = response.headers.get("Content-Type", "unknown")
        print(f"GET /{endpoint:<8} {response.status_code}  {response.elapsed.total_seconds():.2f}s  {content_type}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Error: Request to /{endpoint} timed out.")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to /{endpoint}.")
    except requests.exceptions.HTTPError as error:
        print(f"Error: HTTP request failed: {error}")
    except requests.exceptions.RequestException as error:
        print(f"Error: Request failed: {error}")
    except ValueError:
        print(f"Error: /{endpoint} did not return valid JSON.")
    return None


def generate_report(users, posts, comments):
    if not all(isinstance(data, list) for data in (users, posts, comments)):
        raise ValueError("API responses must be JSON lists")

    posts_per_user = Counter(post.get("userId") for post in posts)
    post_owner = {post.get("id"): post.get("userId") for post in posts}
    comments_per_user = Counter(
        post_owner[comment.get("postId")]
        for comment in comments
        if comment.get("postId") in post_owner
    )
    top_user = max(users, key=lambda user: comments_per_user[user["id"]], default=None)
    average_length = (
        sum(len(post.get("body", "")) for post in posts) / len(posts)
        if posts else 0
    )

    return {
        "total_users": len(users),
        "total_posts": len(posts),
        "total_comments": len(comments),
        "posts_per_user": [
            {"user_id": user["id"], "name": user["name"], "post_count": posts_per_user[user["id"]]}
            for user in users
        ],
        "top_user_by_comments": (
            {
                "user_id": top_user["id"],
                "name": top_user["name"],
                "comment_count": comments_per_user[top_user["id"]],
            }
            if top_user else None
        ),
        "average_post_length_characters": round(average_length, 2),
    }


def main():
    print("API Consumer & JSON Report Generator")
    print("-" * 42)
    users = fetch_data("users")
    posts = fetch_data("posts")
    comments = fetch_data("comments")

    if users is None or posts is None or comments is None:
        print("Report not generated because one or more API requests failed.")
        return

    try:
        report = generate_report(users, posts, comments)
        with REPORT_PATH.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2, ensure_ascii=False)
        top = report["top_user_by_comments"]
        if top:
            print(f"\nTop user by comments: {top['name']} ({top['comment_count']} comments)")
        print(f"Average post length: {report['average_post_length_characters']} characters")
        print(f"Report saved to {REPORT_PATH.name}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error generating report: {error}")


if __name__ == "__main__":
    main()
