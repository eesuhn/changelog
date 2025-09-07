import re
import xml.etree.ElementTree as ET
import requests
import sys
import time

from pathlib import Path
from datetime import datetime
from collections import defaultdict


ROOT_DIR = Path.cwd()
CHANGELOG_RSS = ROOT_DIR / "changelog.rss"
MARKDOWN_DIR = ROOT_DIR / "markdown"
OUTPUT_FILE = ROOT_DIR / "changelog.mdx"


def get_changelog_rss() -> list:
    tree = ET.parse(CHANGELOG_RSS)
    root = tree.getroot()

    items = []
    for item in root.findall(".//item"):
        link_elem = item.find("link")
        pub_date_elem = item.find("pubDate")

        if link_elem is not None and pub_date_elem is not None:
            link = link_elem.text.strip()
            pub_date = pub_date_elem.text.strip()

            parsed_path = link.strip("/").split("/")
            slug = parsed_path[-1] if parsed_path else "unknown"
            slug = re.sub(r"[^\w\-]", "-", slug)
            slug = re.sub(r"-+", "-", slug).strip("-")

            items.append({"link": link, "slug": slug, "pub_date": pub_date})
    return items


def fetch_markdown_content(url):
    markdown_url = url + ".md"
    response = requests.get(markdown_url, timeout=30)
    response.raise_for_status()
    return response.text


def save_mdx_file(content, slug):
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    file_path = MARKDOWN_DIR / f"{slug}.mdx"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def format_date_for_label(pub_date_str):
    dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
    return dt.strftime("%B %Y")


def format_full_date(pub_date_str):
    dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
    return dt.strftime("%B %d, %Y")


def group_items_by_month(rss_items):
    grouped = defaultdict(list)

    for item in rss_items:
        dt = datetime.strptime(item["pub_date"], "%a, %d %b %Y %H:%M:%S %Z")
        month_year_key = dt.strftime("%Y-%m")
        item["datetime"] = dt
        grouped[month_year_key].append(item)

    sorted_groups = sorted(grouped.items(), key=lambda x: x[0], reverse=True)

    for month_year, items in sorted_groups:
        items.sort(key=lambda x: x.get("datetime", datetime.min), reverse=True)

    return sorted_groups


def add_heading_level_and_date(content, pub_date, spaces=2):
    lines = content.split("\n")
    processed_lines = []
    first_heading_found = False

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("#"):
            heading_level = len(stripped_line) - len(stripped_line.lstrip("#"))
            heading_text = stripped_line[heading_level:].strip()
            new_heading = "#" * (heading_level + 1) + " " + heading_text

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


def read_mdx_file(slug):
    file_path = MARKDOWN_DIR / f"{slug}.mdx"
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def fetch_all_markdown():
    changelog_items = get_changelog_rss()
    successful = 0

    for item in changelog_items:
        content = fetch_markdown_content(item["link"])
        if content and save_mdx_file(content, item["slug"]):
            successful += 1
        time.sleep(1)

    return successful > 0


def combine_changelog():
    changelog_items = get_changelog_rss()

    changelog_content = """---
title: "Changelog"
description: "Product updates and announcements"
---

"""

    grouped_items = group_items_by_month(changelog_items)
    successful = 0

    for month_year_key, items in grouped_items:
        if month_year_key == "unknown":
            continue

        if items:
            month_label = format_date_for_label(items[0]["pub_date"])
            changelog_content += f'<Update label="{month_label}">\n'

            for item in items:
                mdx_content = read_mdx_file(item["slug"])
                if mdx_content:
                    processed_content = add_heading_level_and_date(
                        mdx_content, item["pub_date"]
                    )
                    changelog_content += processed_content + "\n\n"
                    successful += 1

            changelog_content += "</Update>\n\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(changelog_content)
    return True


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "fetch":
            fetch_all_markdown()
        elif command == "combine":
            combine_changelog()
        elif command == "all":
            if fetch_all_markdown():
                combine_changelog()
        else:
            print("Usage: python main.py [fetch|combine|all]")
    else:
        changelog_items = get_changelog_rss()
        print(f"Found {len(changelog_items)} changelog items.")
        print("Usage: python main.py [fetch|combine|all]")


if __name__ == "__main__":
    main()
