#!/usr/bin/env python3
"""
Changelog Migration Script: ReadMe to Mintlify
Extracts changelog entries from RSS and fetches markdown content
"""

import xml.etree.ElementTree as ET
import requests
from urllib.parse import urlparse
from pathlib import Path
import re
import sys
import time


def parse_rss_feed(rss_file_path):
    """Parse the RSS feed and extract link and pubDate for each item."""
    try:
        tree = ET.parse(rss_file_path)
        root = tree.getroot()

        items = []
        for item in root.findall(".//item"):
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")

            if link_elem is not None and pub_date_elem is not None:
                link = link_elem.text.strip()
                pub_date = pub_date_elem.text.strip()

                items.append({"link": link, "pub_date": pub_date})

        print(f"✅ Successfully parsed {len(items)} changelog items from RSS feed")
        return items

    except ET.ParseError as e:
        print(f"❌ Error parsing RSS feed: {e}")
        return []
    except FileNotFoundError:
        print(f"❌ RSS feed file not found: {rss_file_path}")
        return []


def extract_slug_from_url(url):
    """Extract the slug from the changelog URL."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")

    if path_parts:
        slug = path_parts[-1]
        slug = re.sub(r"[^\w\-]", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug

    return "unknown-changelog"


def fetch_markdown_content(url):
    """Fetch the markdown version of the changelog by appending .md to the URL."""
    markdown_url = url + ".md"

    try:
        print(f"📥 Fetching: {markdown_url}")
        response = requests.get(markdown_url, timeout=30)
        response.raise_for_status()

        return response.text

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {markdown_url}: {e}")
        return None


def convert_to_mdx(content):
    """Convert markdown content to MDX format."""
    if not content:
        return content

    # Replace <br /> tags
    # content = content.replace("<br />", "")

    return content


def save_mdx_file(content, slug, output_dir):
    """Save the content as MDX file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Convert to MDX format
    mdx_content = convert_to_mdx(content)

    filename = f"{slug}.mdx"
    file_path = output_path / filename

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(mdx_content)

        print(f"✅ Saved: {file_path}")
        return str(file_path)

    except IOError as e:
        print(f"❌ Error saving file {file_path}: {e}")
        return None


def main():
    """Main migration process."""
    print("🚀 Starting changelog migration from ReadMe to Mintlify")
    print("=" * 60)

    # Configuration
    rss_file = "./changelog.rss"
    output_dir = "./markdown"

    # Step 1: Parse RSS feed
    print("📋 Step 1: Parsing RSS feed...")
    changelog_items = parse_rss_feed(rss_file)

    if not changelog_items:
        print("❌ No changelog items found. Exiting.")
        return 1

    # Step 2: Process each changelog item
    print(f"\n📝 Step 2: Processing {len(changelog_items)} changelog items...")
    print("-" * 60)

    successful_downloads = 0
    failed_downloads = 0

    for i, item in enumerate(changelog_items, 1):
        print(f"\n[{i}/{len(changelog_items)}] Processing item {i}")
        print(f"🔗 URL: {item['link']}")

        # Extract slug from URL
        slug = extract_slug_from_url(item["link"])
        print(f"🏷️  Slug: {slug}")

        # Fetch markdown content
        markdown_content = fetch_markdown_content(item["link"])

        if markdown_content:
            # Save to MDX file
            saved_path = save_mdx_file(markdown_content, slug, output_dir)
            if saved_path:
                successful_downloads += 1
            else:
                failed_downloads += 1
        else:
            failed_downloads += 1

        # Add delay between requests
        if i < len(changelog_items):
            time.sleep(1)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Migration Summary:")
    print(f"✅ Successfully downloaded: {successful_downloads}")
    print(f"❌ Failed downloads: {failed_downloads}")
    print(f"📁 Output directory: {Path(output_dir).absolute()}")

    if successful_downloads > 0:
        print(
            f"\n🎉 Migration completed! Check the '{output_dir}' folder for your MDX files."
        )
        return 0
    else:
        print("\n😞 No files were successfully downloaded.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
