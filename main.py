#!/usr/bin/env python3
"""
Toast API Client - Main CLI Entry Point

Usage:
    python main.py list-groups              # List all menu groups
    python main.py scan-groups              # Scan all groups (calls external script)
    python main.py generate-menu [options]  # Generate takeout menu
    python main.py generate-reports         # Generate analysis reports
    python main.py search-items <term>      # Search for menu items
    python main.py pricing-analysis         # Show pricing statistics
    python main.py extract-images [options] # Extract menu item names and images
    python main.py clear-cache              # Clear all cached data
    
Options for generate-menu:
    --with-price    Include prices in output
    --filter-3pd    Include only 3rd party delivery items
    --format        Output format: pdf, html, txt (default: all)

Options for extract-images:
    --filter-3pd    Include only 3rd party delivery items
    --format        Output format: text, json, csv (default: text)
                   Note: All formats download images to images/ directory, generate CSV,
                   and create missing_pictures.txt for items without images
"""

import sys
import argparse
from typing import List

from toast_api.services.menu_service import MenuService
from toast_api.services.report_service import ReportService
from toast_api.utils.logger import logger, setup_logger
from toast_api.utils.formatters import format_currency, format_menu_item_display
from toast_api.client.exceptions import ToastAPIError


def list_groups() -> int:
    """List all available menu groups."""
    try:
        menu_service = MenuService()
        groups = menu_service.get_all_menu_groups()
        
        print("\n📚 Available Menu Groups:\n")
        for name in groups:
            print(f"• {name}")
        
        print(f"\nTotal: {len(groups)} groups")
        return 0
    except ToastAPIError as e:
        logger.error(f"Toast API error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


def scan_groups() -> int:
    """Scan all menu groups."""
    try:
        import subprocess
        menu_service = MenuService()
        groups = menu_service.get_all_menu_groups()
        
        for group in groups:
            logger.info(f"🔍 Scanning group: '{group}'")
            # Call external script if it exists
            try:
                subprocess.run(["python", "menu_group_items.py", group, ""], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.warning(f"Could not process group '{group}': {e}")
        
        logger.info(f"✅ Processed {len(groups)} menu groups")
        return 0
    except Exception as e:
        logger.error(f"Error scanning groups: {e}")
        return 1


def generate_menu(args: argparse.Namespace) -> int:
    """Generate takeout menu."""
    try:
        from toast_api.utils.file_utils import read_lines_file
        
        # Load group order
        group_order = read_lines_file("group_order.txt")
        if not group_order:
            logger.error("group_order.txt not found or empty")
            return 1
        
        # Generate menu using service
        menu_service = MenuService()
        report_service = ReportService()
        
        grouped_items = menu_service.get_grouped_menu_items(
            group_order=group_order,
            include_3pd=args.filter_3pd,
            include_prices=args.with_price
        )
        
        formats = [args.format] if args.format != 'all' else ['txt', 'html', 'pdf']
        
        for fmt in formats:
            if fmt == 'pdf':
                try:
                    extension = "_with3pd" if args.filter_3pd else ""
                    output_file = f"takeout_menu{extension}.pdf"
                    report_service.generate_takeout_menu_pdf(
                        group_order=group_order,
                        include_prices=args.with_price,
                        include_3pd=args.filter_3pd,
                        output_file=output_file,
                        logo_path="restaurant_logo.jpeg" if args.logo else None
                    )
                except ImportError:
                    logger.warning("PDF generation requires reportlab. Install with: pip install reportlab")
                    continue
            
            elif fmt == 'html':
                _generate_html_menu(grouped_items, group_order, args)
            
            elif fmt == 'txt':
                _generate_text_menu(grouped_items, group_order, args)
        
        return 0
    except Exception as e:
        logger.error(f"Error generating menu: {e}")
        return 1


def _generate_text_menu(grouped_items, group_order, args):
    """Generate text format menu."""
    from toast_api.config.settings import config
    from toast_api.utils.file_utils import write_text_file
    
    extension = "_with3pd" if args.filter_3pd else ""
    output_file = f"takeout_menu{extension}.txt"
    
    content = []
    content.append(f"{config.restaurant_name} – Takeout Menu")
    content.append(f"{config.restaurant_address}")
    content.append(f"{config.restaurant_phone} • {config.restaurant_website}")
    content.append("")
    
    for group in group_order:
        items = grouped_items.get(group, [])
        if not items:
            continue
            
        content.append(f"🌟 {group}")
        for item in items:
            if args.with_price and item['formatted_price']:
                content.append(f"  • {item['name']:<50} {item['formatted_price']}")
            else:
                content.append(f"  • {item['name']}")
        content.append("")
    
    content.append("Hours: Monday Closed • Tuesday–Sunday 11:00am–2:00pm and 5:00pm–9:00pm")
    content.append("Menu items and prices subject to change.")
    
    write_text_file(output_file, "\n".join(content))


def _generate_html_menu(grouped_items, group_order, args):
    """Generate HTML format menu."""
    from toast_api.config.settings import config
    from toast_api.utils.file_utils import write_text_file
    
    extension = "_with3pd" if args.filter_3pd else ""
    output_file = f"preview_menu{extension}.html"
    
    html_content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{config.restaurant_name} – Takeout Menu</title>
<style>
body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding:2em; background:#fffefb }}
h1 {{ text-align: center; }}
.group {{ margin-top: 2em; }}
.item {{ display: flex; justify-content: space-between; padding: 4px 0; }}
footer {{ margin-top: 3em; font-size: 0.9em; text-align: center; }}
</style></head><body>
<h1>{config.restaurant_name} – Takeout Menu</h1>
<p style="text-align:right">{config.restaurant_address}<br>
{config.restaurant_phone} • <a href="https://{config.restaurant_website}">{config.restaurant_website}</a></p>
"""
    
    for group in group_order:
        items = grouped_items.get(group, [])
        if not items:
            continue
            
        html_content += f'<div class="group"><h2>{group}</h2>\n'
        for item in items:
            if args.with_price and item['formatted_price']:
                html_content += f'<div class="item"><span>{item["name"]}</span><span>{item["formatted_price"]}</span></div>\n'
            else:
                html_content += f'<div class="item"><span>{item["name"]}</span></div>\n'
        html_content += '</div>\n'
    
    html_content += """
<footer>
<p>Hours: Monday Closed • Tuesday–Sunday 11:00am–2:00pm and 5:00pm–9:00pm</p>
<p>Menu items and prices subject to change.</p>
</footer>
</body></html>"""
    
    write_text_file(output_file, html_content)


def generate_reports() -> int:
    """Generate analysis reports."""
    try:
        report_service = ReportService()
        
        print("📊 Generating reports...")
        
        # Generate all reports
        summary_file = report_service.generate_menu_summary_report()
        group_file = report_service.generate_group_analysis_report()
        pricing_file = report_service.generate_pricing_report()
        
        print(f"✅ Reports generated:")
        print(f"  • Menu Summary: {summary_file}")
        print(f"  • Group Analysis: {group_file}")
        print(f"  • Pricing Analysis: {pricing_file}")
        
        return 0
    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        return 1

def search_items(search_term: str) -> int:
    """Search for menu items."""
    try:
        menu_service = MenuService()
        results = menu_service.search_items_by_name(search_term)
        
        if not results:
            print(f"No items found matching '{search_term}'")
            return 0
        
        print(f"\n🔍 Found {len(results)} items matching '{search_term}':\n")
        
        for item_data in results:
            # Use the actual keys from menu_service.py
            name = item_data['name']
            price = item_data['price']
            group_name = item_data['group']
            menu_name = item_data['menu']
            
            print(f"✓ {name}")
            print(f"  Price: {price}")
            print(f"  Category: {group_name}")
            print(f"  Menu: {menu_name}")
            print()
        
        return 0
    except Exception as e:
        logger.error(f"Error searching items: {e}")
        return 1

def pricing_analysis() -> int:
    """Show pricing analysis."""
    try:
        menu_service = MenuService()
        items_with_prices = menu_service.get_items_with_prices()
        
        if not items_with_prices:
            print("No items with prices found")
            return 0
        
        prices = [item['price'] for item in items_with_prices]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        print(f"\n💰 Pricing Analysis:")
        print(f"  Total Items with Prices: {len(items_with_prices)}")
        print(f"  Average Price: {format_currency(avg_price)}")
        print(f"  Price Range: {format_currency(min_price)} - {format_currency(max_price)}")
        
        # Price distribution
        ranges = [(0, 10), (10, 20), (20, 30), (30, float('inf'))]
        range_labels = ["Under $10", "$10-$20", "$20-$30", "Over $30"]
        
        print(f"\n  Price Distribution:")
        for (min_p, max_p), label in zip(ranges, range_labels):
            count = len([p for p in prices if min_p <= p < max_p])
            percentage = (count / len(prices)) * 100
            print(f"    {label}: {count} items ({percentage:.1f}%)")
        
        return 0
    except Exception as e:
        logger.error(f"Error in pricing analysis: {e}")
        return 1


def clear_cache() -> int:
    """Clear all cached data."""
    try:
        menu_service = MenuService()
        menu_service.clear_cache()

        # Also clear token cache
        from toast_api.utils.cache import TokenCache
        from toast_api.config.settings import config

        token_cache = TokenCache(config.token_cache_file)
        # Clear by saving empty token (hacky but works)
        from datetime import datetime
        token_cache.save_token("", datetime.now())

        print("🗑️ All caches cleared")
        return 0
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return 1


def extract_images(args: argparse.Namespace) -> int:
    """Extract menu item names and images from Toast POS."""
    try:
        import os
        import requests
        import csv
        from urllib.parse import urlparse

        menu_service = MenuService()

        print("🖼️ Extracting menu items and images from Toast POS...")

        # Create images directory
        images_dir = "images"
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            print(f"📁 Created directory: {images_dir}")

        # Get all menu items with images
        items_with_images = menu_service.get_items_with_images(
            include_3pd=args.filter_3pd,
            format=args.format
        )

        if not items_with_images:
            print("❌ No menu items with images found")
            return 0

        total_items = len(items_with_images)
        items_with_images_count = len([item for item in items_with_images if item.get('images')])

        print(f"\n📊 Image Extraction Results:")
        print(f"  Total Items: {total_items}")
        print(f"  Items with Images: {items_with_images_count}")
        print(f"  Items without Images: {total_items - items_with_images_count}")

        # Download images and prepare data for CSV
        csv_data = []
        downloaded_count = 0
        missing_pictures = []

        for item in items_with_images:
            images = item.get('images', [])
            item_name = item['name']

            # Clean item name for filename
            safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')

            local_image_files = []

            for i, img_url in enumerate(images):
                try:
                    # Parse URL to get file extension
                    parsed_url = urlparse(img_url)
                    file_ext = os.path.splitext(parsed_url.path)[1] or '.jpg'

                    # Create filename
                    if len(images) > 1:
                        filename = f"{safe_name}_{i+1}{file_ext}"
                    else:
                        filename = f"{safe_name}{file_ext}"

                    filepath = os.path.join(images_dir, filename)

                    # Download image
                    response = requests.get(img_url, timeout=30)
                    response.raise_for_status()

                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    local_image_files.append(filename)
                    downloaded_count += 1
                    print(f"📥 Downloaded: {filename}")

                except Exception as e:
                    logger.warning(f"Failed to download image for {item_name}: {e}")
                    continue

            # Track items missing pictures
            if not images:
                missing_pictures.append({
                    'name': item_name,
                    'group': item.get('group', ''),
                    'price': item.get('formatted_price', '')
                })

            # Add to CSV data
            csv_data.append({
                'item_name': item_name,
                'group': item.get('group', ''),
                'price': item.get('formatted_price', ''),
                'image_files': '|'.join(local_image_files) if local_image_files else '',
                'image_count': len(local_image_files),
                'has_images': 'Yes' if local_image_files else 'No'
            })

        # Generate CSV with local image filenames
        output_file = "menu_items_with_local_images.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['item_name', 'group', 'price', 'image_files', 'image_count', 'has_images']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for row in csv_data:
                writer.writerow(row)

        # Generate missing pictures file
        missing_file = "missing_pictures.txt"
        with open(missing_file, 'w', encoding='utf-8') as f:
            f.write("Menu Items Missing Pictures\n")
            f.write("=" * 50 + "\n\n")

            if missing_pictures:
                # Group by category
                from collections import defaultdict
                by_group = defaultdict(list)

                for item in missing_pictures:
                    group = item['group'] or 'No Category'
                    by_group[group].append(item)

                # Write grouped items
                for group, items in sorted(by_group.items()):
                    f.write(f"{group}:\n")
                    f.write("-" * len(group) + "\n")
                    for item in sorted(items, key=lambda x: x['name']):
                        price_info = f" ({item['price']})" if item['price'] else ""
                        f.write(f"  • {item['name']}{price_info}\n")
                    f.write("\n")

                f.write(f"Total items missing pictures: {len(missing_pictures)}\n")
            else:
                f.write("All menu items have pictures!\n")

        print(f"\n✅ Download Summary:")
        print(f"  Images Downloaded: {downloaded_count}")
        print(f"  Items Missing Pictures: {len(missing_pictures)}")
        print(f"  CSV Generated: {output_file}")
        print(f"  Missing Pictures List: {missing_file}")
        print(f"  Images Directory: {images_dir}/")

        if args.format == 'json':
            import json
            from toast_api.utils.file_utils import write_text_file

            json_output_file = "menu_items_with_images.json"
            write_text_file(json_output_file, json.dumps(items_with_images, indent=2))
            print(f"  JSON Output: {json_output_file}")

        elif args.format == 'text':
            print(f"\n🍽️ Menu Items with Downloaded Images:\n")

            for item in csv_data:
                print(f"✓ {item['item_name']}")
                if item['group']:
                    print(f"  Category: {item['group']}")
                if item['price']:
                    print(f"  Price: {item['price']}")
                if item['image_files']:
                    files = item['image_files'].split('|')
                    print(f"  Local Images ({len(files)}):")
                    for i, filename in enumerate(files, 1):
                        print(f"    {i}. images/{filename}")
                else:
                    print(f"  Images: None")
                print()

        return 0
    except Exception as e:
        logger.error(f"Error extracting images: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Toast API Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List groups command
    subparsers.add_parser("list-groups", help="List all menu groups")
    
    # Scan groups command  
    subparsers.add_parser("scan-groups", help="Scan all menu groups")
    
    # Generate menu command
    menu_parser = subparsers.add_parser("generate-menu", help="Generate takeout menu")
    menu_parser.add_argument("--with-price", action="store_true", help="Include prices")
    menu_parser.add_argument("--filter-3pd", action="store_true", help="Filter for 3rd party delivery")
    menu_parser.add_argument("--format", choices=["pdf", "html", "txt", "all"], default="all", help="Output format")
    menu_parser.add_argument("--logo", action="store_true", help="Include logo in PDF")
    
    # Generate reports command
    subparsers.add_parser("generate-reports", help="Generate analysis reports")
    
    # Search items command
    search_parser = subparsers.add_parser("search-items", help="Search for menu items")
    search_parser.add_argument("term", help="Search term")
    
    # Pricing analysis command
    subparsers.add_parser("pricing-analysis", help="Show pricing statistics")
    
    # Clear cache command
    subparsers.add_parser("clear-cache", help="Clear all cached data")

    # Extract images command
    images_parser = subparsers.add_parser("extract-images", help="Extract menu item names and images")
    images_parser.add_argument("--filter-3pd", action="store_true", help="Filter for 3rd party delivery items")
    images_parser.add_argument("--format", choices=["text", "json", "csv"], default="text", help="Output format")

    args = parser.parse_args()
    
    # Setup logging
    setup_logger("toast_api", level=args.log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate function
    if args.command == "list-groups":
        return list_groups()
    elif args.command == "scan-groups":
        return scan_groups()
    elif args.command == "generate-menu":
        return generate_menu(args)
    elif args.command == "generate-reports":
        return generate_reports()
    elif args.command == "search-items":
        return search_items(args.term)
    elif args.command == "pricing-analysis":
        return pricing_analysis()
    elif args.command == "clear-cache":
        return clear_cache()
    elif args.command == "extract-images":
        return extract_images(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())
