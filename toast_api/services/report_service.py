# toast_api/services/report_service.py
"""Report generation service for menus and analytics."""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from ..models.menu import Menu, MenuGroup, MenuItem
from ..models.restaurant import Restaurant
from ..services.menu_service import MenuService
from ..config.settings import config
from ..utils.logger import logger

class ReportService:
    """Service for generating various reports and documents."""
    
    def __init__(self):
        self.menu_service = MenuService()
        self.restaurant = Restaurant.from_config(config)
        self.logo_path = self._find_logo_path()
    
    def _find_logo_path(self) -> Optional[str]:
        """Automatically find the restaurant logo file."""
        # Get the project root directory (go up from current file location)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..', '..')
        
        # Common logo locations to check
        logo_locations = [
            os.path.join(project_root, 'restaurant_logo.jpeg'),
            os.path.join(project_root, 'assets', 'restaurant_logo.jpeg'),
            os.path.join(project_root, 'static', 'restaurant_logo.jpeg'),
            os.path.join(project_root, 'images', 'restaurant_logo.jpeg'),
            os.path.join(current_dir, '..', 'assets', 'restaurant_logo.jpeg'),
        ]
        
        for logo_path in logo_locations:
            abs_path = os.path.abspath(logo_path)
            if os.path.exists(abs_path):
                logger.info(f"Found restaurant logo at: {abs_path}")
                return abs_path
        
        logger.warning("Restaurant logo not found. PDF will be generated without logo.")
        return None
    
    def generate_menu_summary_report(self, output_file: str = "menu_summary.txt") -> str:
        """Generate a text summary report of all menus."""
        menus = self.menu_service.get_parsed_menus()
        
        with open(output_file, 'w') as f:
            f.write(f"MENU SUMMARY REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Restaurant: {self.restaurant.name}\n")
            f.write("=" * 50 + "\n\n")
            
            for menu in menus:
                f.write(f"📋 MENU: {menu.name}\n")
                f.write(f"   GUID: {menu.guid}\n")
                f.write(f"   Groups: {len(menu.groups)}\n")
                f.write(f"   3rd Party: {'Yes' if menu.is_third_party_menu else 'No'}\n")
                f.write(f"   Should Skip: {'Yes' if menu.should_skip_menu else 'No'}\n")
                
                total_items = sum(len(group.items) for group in menu.groups)
                f.write(f"   Total Items: {total_items}\n\n")
                
                for group in menu.groups:
                    f.write(f"   🏷️  GROUP: {group.name} ({len(group.items)} items)\n")
                    f.write(f"      Visible to Partners: {'Yes' if group.is_visible_to_partners else 'No'}\n")
                    
                    for item in group.items[:3]:  # Show first 3 items
                        price_str = f" - {item.formatted_price}" if item.price else ""
                        f.write(f"      • {item.name}{price_str}\n")
                    
                    if len(group.items) > 3:
                        f.write(f"      ... and {len(group.items) - 3} more items\n")
                    f.write("\n")
                
                f.write("-" * 40 + "\n\n")
        
        logger.info(f"📊 Menu summary report saved to {output_file}")
        return output_file
    
    def generate_group_analysis_report(self, output_file: str = "group_analysis.txt") -> str:
        """Generate analysis of menu groups across all menus."""
        menus = self.menu_service.get_parsed_menus()
        
        # Collect group statistics
        group_stats = {}
        
        for menu in menus:
            for group in menu.groups:
                if group.name not in group_stats:
                    group_stats[group.name] = {
                        'total_items': 0,
                        'menus': [],
                        'avg_price': 0,
                        'price_count': 0,
                        'partner_visible': False
                    }
                
                stats = group_stats[group.name]
                stats['total_items'] += len(group.items)
                stats['menus'].append(menu.name)
                stats['partner_visible'] = stats['partner_visible'] or group.is_visible_to_partners
                
                # Calculate average price
                for item in group.items:
                    if item.price is not None:
                        stats['avg_price'] = (stats['avg_price'] * stats['price_count'] + item.price) / (stats['price_count'] + 1)
                        stats['price_count'] += 1
        
        # Write report
        with open(output_file, 'w') as f:
            f.write(f"GROUP ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Restaurant: {self.restaurant.name}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total Unique Groups: {len(group_stats)}\n\n")
            
            # Sort by total items
            sorted_groups = sorted(group_stats.items(), key=lambda x: x[1]['total_items'], reverse=True)
            
            for group_name, stats in sorted_groups:
                f.write(f"🏷️  {group_name}\n")
                f.write(f"   Total Items: {stats['total_items']}\n")
                f.write(f"   Appears in {len(set(stats['menus']))} menus\n")
                f.write(f"   Partner Visible: {'Yes' if stats['partner_visible'] else 'No'}\n")
                
                if stats['price_count'] > 0:
                    f.write(f"   Average Price: ${stats['avg_price']:.2f}\n")
                
                f.write(f"   Menus: {', '.join(set(stats['menus']))}\n")
                f.write("\n")
        
        logger.info(f"📊 Group analysis report saved to {output_file}")
        return output_file
    
    def generate_pricing_report(self, output_file: str = "pricing_report.txt") -> str:
        """Generate pricing analysis report."""
        menus = self.menu_service.get_parsed_menus()
        
        all_items = []
        for menu in menus:
            if menu.should_skip_menu:
                continue
            for group in menu.groups:
                for item in group.items:
                    if item.price is not None:
                        all_items.append({
                            'name': item.name,
                            'price': item.price,
                            'group': group.name,
                            'menu': menu.name,
                            'is_3pd': menu.is_third_party_menu
                        })
        
        if not all_items:
            logger.warning("No items with prices found")
            return output_file
        
        # Calculate statistics
        prices = [item['price'] for item in all_items]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        with open(output_file, 'w') as f:
            f.write(f"PRICING ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Restaurant: {self.restaurant.name}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"OVERALL STATISTICS\n")
            f.write(f"Total Items with Prices: {len(all_items)}\n")
            f.write(f"Average Price: ${avg_price:.2f}\n")
            f.write(f"Minimum Price: ${min_price:.2f}\n")
            f.write(f"Maximum Price: ${max_price:.2f}\n\n")
            
            # Price ranges
            ranges = [
                (0, 10, "Under $10"),
                (10, 20, "$10 - $20"),
                (20, 30, "$20 - $30"),
                (30, float('inf'), "Over $30")
            ]
            
            f.write("PRICE DISTRIBUTION\n")
            for min_p, max_p, label in ranges:
                count = len([item for item in all_items if min_p <= item['price'] < max_p])
                percentage = (count / len(all_items)) * 100
                f.write(f"{label}: {count} items ({percentage:.1f}%)\n")
            
            f.write("\n")
            
            # Most expensive items
            f.write("TOP 10 MOST EXPENSIVE ITEMS\n")
            sorted_items = sorted(all_items, key=lambda x: x['price'], reverse=True)
            for i, item in enumerate(sorted_items[:10], 1):
                f.write(f"{i:2d}. {item['name']} - ${item['price']:.2f} ({item['group']})\n")
            
            f.write("\n")
            
            # Cheapest items
            f.write("TOP 10 LEAST EXPENSIVE ITEMS\n")
            for i, item in enumerate(sorted_items[-10:], 1):
                f.write(f"{i:2d}. {item['name']} - ${item['price']:.2f} ({item['group']})\n")
        
        logger.info(f"💰 Pricing report saved to {output_file}")
        return output_file
    
    def generate_takeout_menu_pdf(self, 
                                 group_order: List[str],
                                 include_prices: bool = False,
                                 include_3pd: bool = False,
                                 output_file: str = "takeout_menu.pdf",
                                 logo_path: Optional[str] = None) -> str:
        """Generate a professional PDF takeout menu."""
        
        grouped_items = self.menu_service.get_grouped_menu_items(
            group_order=group_order,
            include_3pd=include_3pd,
            include_prices=include_prices
        )
        
        # Use provided logo path or automatically detected one
        logo_to_use = logo_path or self.logo_path
        
        # Create PDF
        c = canvas.Canvas(output_file, pagesize=letter)
        w, h = letter
        
        # Layout settings
        col_x = [inch * 0.5, w / 2 + inch * 0.2]
        price_x = [col_x[0] + 200, w - inch * 0.5]
        col_y_start = h - inch * 2.0
        line_height = 14
        column = 0
        y = col_y_start
        
        # Header with logo
        if logo_to_use and os.path.exists(logo_to_use):
            try:
                logo_width = 2.5 * inch
                logo_height = 0.9 * inch
                logo_x = (w - logo_width) / 2
                logo_y = h - inch * 1.0
                c.drawImage(logo_to_use, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True)
                header_y = logo_y - 30
                logger.info(f"✅ Logo added to PDF from: {logo_to_use}")
            except Exception as e:
                logger.error(f"❌ Failed to add logo to PDF: {e}")
                header_y = h - inch * 1.0
        else:
            header_y = h - inch * 1.0
            if logo_to_use:
                logger.warning(f"Logo file not found at: {logo_to_use}")
        
        # Restaurant name
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(w / 2, header_y, self.restaurant.name)
        
        # Tagline
        c.setFont("Helvetica-Oblique", 12)
        c.drawCentredString(w / 2, header_y - 25, "Reinvent the Taste of India")
        
        # Menu content
        c.setFont("Helvetica", 10)
        
        for group_name in group_order:
            items = grouped_items.get(group_name, [])
            if not items:
                continue
            
            # Check if we need a new column
            if y < inch + 80:
                column += 1
                if column >= len(col_x):
                    break
                y = col_y_start
            
            # Group header
            y -= line_height
            c.setFont("Helvetica-Bold", 11)
            c.drawString(col_x[column], y, group_name)
            y -= line_height
            
            # Items
            c.setFont("Helvetica", 9)
            for item in items:
                if y < inch + 60:
                    column += 1
                    if column >= len(col_x):
                        break
                    y = col_y_start
                    # Redraw group header
                    y -= line_height
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(col_x[column], y, group_name)
                    y -= line_height
                    c.setFont("Helvetica", 9)
                
                c.drawString(col_x[column], y, f"• {item['name']}")
                
                if include_prices and item['formatted_price']:
                    c.drawRightString(price_x[column], y, item['formatted_price'])
                
                y -= line_height
        
        # Footer
        c.setFont("Helvetica", 8)
        footer_y = inch * 0.6
        
        if self.restaurant.phone or self.restaurant.website:
            c.drawString(inch * 0.5, footer_y + 28, f"Contact: {self.restaurant.formatted_contact}")
        
        if self.restaurant.address:
            c.drawString(inch * 0.5, footer_y + 14, f"Address: {self.restaurant.address}")
        
        c.drawString(inch * 0.5, footer_y, "Menu items and prices subject to change.")
        
        c.save()
        logger.info(f"📄 PDF menu saved to {output_file}")
        return output_file
