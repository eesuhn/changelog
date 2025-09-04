#!/usr/bin/env python3
"""
Consolidate Changelog Script
Combines individual .mdx files into a single changelog.mdx with Update components
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys
import re


def parse_rss_feed(rss_file_path):
    """Parse the RSS feed and extract metadata for each item."""
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

                # Extract slug from URL
                parsed_path = link.strip("/").split("/")
                slug = parsed_path[-1] if parsed_path else "unknown"
                slug = re.sub(r"[^\w\-]", "-", slug)
                slug = re.sub(r"-+", "-", slug).strip("-")

                items.append({"slug": slug, "pub_date": pub_date})

        print(f"✅ Parsed {len(items)} items from RSS feed")
        return items

    except ET.ParseError as e:
        print(f"❌ Error parsing RSS feed: {e}")
        return []
    except FileNotFoundError:
        print(f"❌ RSS feed file not found: {rss_file_path}")
        return []


def format_date_for_label(pub_date_str):
    """Format publication date for Update label (month year only)."""
    try:
        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%B %Y")
    except ValueError:
        return pub_date_str


def format_full_date(pub_date_str):
    """Format publication date for display in content."""
    try:
        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%B %d, %Y")
    except ValueError:
        return pub_date_str


def group_items_by_month(rss_items):
    """Group RSS items by month and year, sorted by date descending."""
    grouped = defaultdict(list)

    for item in rss_items:
        try:
            dt = datetime.strptime(item["pub_date"], "%a, %d %b %Y %H:%M:%S %Z")
            month_year_key = dt.strftime("%Y-%m")
            item["datetime"] = dt
            grouped[month_year_key].append(item)
        except ValueError:
            # If date parsing fails, put in a fallback group
            grouped["unknown"].append(item)

    # Sort groups by month/year (descending)
    sorted_groups = sorted(grouped.items(), key=lambda x: x[0], reverse=True)

    # Sort items within each group by date (descending)
    for month_year, items in sorted_groups:
        items.sort(key=lambda x: x.get("datetime", datetime.min), reverse=True)

    return sorted_groups


def add_heading_level_and_date(content, pub_date, spaces=2):
    """Add one # to all headings and include pubDate, then indent."""
    lines = content.split("\n")
    processed_lines = []
    first_heading_found = False

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("#"):
            # Add one more # to the heading
            heading_level = len(stripped_line) - len(stripped_line.lstrip("#"))
            heading_text = stripped_line[heading_level:].strip()
            new_heading = "#" * (heading_level + 1) + " " + heading_text

            # Add date after the first heading
            if not first_heading_found:
                processed_lines.append(" " * spaces + new_heading)
                processed_lines.append("")
                processed_lines.append(
                    " " * spaces + f"🗓️ **{format_full_date(pub_date)}**"
                )
                processed_lines.append("")
                first_heading_found = True
            else:
                processed_lines.append(" " * spaces + new_heading)
        elif stripped_line:
            processed_lines.append(" " * spaces + line)
        else:
            processed_lines.append(line)

    return "\n".join(processed_lines)


def read_mdx_file(slug, markdown_dir):
    """Read the content of an .mdx file."""
    file_path = Path(markdown_dir) / f"{slug}.mdx"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"✅ Read: {file_path}")
        return content

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except IOError as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None


def consolidate_changelog(rss_items, markdown_dir, output_file):
    """Consolidate all .mdx files into a single changelog.mdx grouped by month."""

    # Start with frontmatter
    changelog_content = """---
title: "Changelog"
description: "Product updates and announcements"
---

"""

    # Group items by month and year
    grouped_items = group_items_by_month(rss_items)

    successful_reads = 0

    for month_year_key, items in grouped_items:
        if month_year_key == "unknown":
            continue

        # Create Update component for the entire month
        if items:
            month_label = format_date_for_label(items[0]["pub_date"])
            changelog_content += f'<Update label="{month_label}">\n'

            for item in items:
                slug = item["slug"]
                pub_date = item["pub_date"]

                print(f"🔄 Processing: {slug}")

                # Read the .mdx file content
                mdx_content = read_mdx_file(slug, markdown_dir)

                if mdx_content:
                    # Add heading level and date, then indent
                    processed_content = add_heading_level_and_date(
                        mdx_content, pub_date
                    )

                    # Add to changelog (content already has proper indentation)
                    changelog_content += processed_content + "\n\n"
                    successful_reads += 1

            changelog_content += "</Update>\n\n"

    # Write the consolidated changelog
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(changelog_content)

        print(f"✅ Consolidated changelog saved: {output_file}")
        print(f"📊 Successfully processed {successful_reads} changelog entries")
        return True

    except IOError as e:
        print(f"❌ Error writing consolidated changelog: {e}")
        return False


def main():
    """Main consolidation process."""
    print("🚀 Consolidating changelog files")
    print("=" * 50)

    # Configuration
    rss_file = "./changelog.rss"
    markdown_dir = "./markdown"
    output_file = "./changelog.mdx"

    # Step 1: Parse RSS feed for metadata
    print("📋 Step 1: Parsing RSS feed for metadata...")
    rss_items = parse_rss_feed(rss_file)

    if not rss_items:
        print("❌ No RSS items found. Exiting.")
        return 1

    # Step 2: Consolidate changelog files
    print(f"\n📝 Step 2: Consolidating {len(rss_items)} changelog files...")
    print("-" * 50)

    success = consolidate_changelog(rss_items, markdown_dir, output_file)

    if success:
        print(f"\n🎉 Consolidation completed! Check {output_file}")
        return 0
    else:
        print("\n😞 Consolidation failed.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
