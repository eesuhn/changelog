import re
import xml.etree.ElementTree as ET
import justsdk

from pathlib import Path


ROOT_DIR = Path.cwd()
CHANGELOG_RSS = ROOT_DIR / "changelog.rss"


def get_changelog_rss() -> list:
    tree = ET.parse(CHANGELOG_RSS)
    root = tree.getroot()

    items: list = []
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

            items.append({"slug": slug, "pub_date": pub_date})
    return items


def main():
    changelog_items = get_changelog_rss()
    justsdk.print_data(changelog_items, colorize=True)


if __name__ == "__main__":
    main()
