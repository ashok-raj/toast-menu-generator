# scripts/generate_menu.py
"""Generate takeout menu in multiple formats."""
import sys
import os
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from toast_api.services.menu_service import MenuService  
from toast_api.config.settings import config
from toast_api.utils.logger import logger

class MenuGenerator:
    """Generate menus in various formats."""
    
    def __init__(self):
        self.menu_service = MenuService()
        
        # Parse command line arguments
        self.include_prices = "--with-price" in sys.argv
        self.include_3pd = "--filter-3pd" in sys.argv
        
        # File naming
        extension = "_with3pd" if self.include_3pd else ""
        self.pdf_file = f"takeout_menu{extension}.pdf"
        self.text_file = f"takeout_menu{extension}.txt"
        self.html_file = f"preview_menu{extension}.html"
        
        # Restaurant info
        self.restaurant_info = {
            'name': config.restaurant_name,
            'address': config.restaurant_address, 
            'phone': config.restaurant_phone,
            'website': config.restaurant_website,
            'hours': "Monday Closed\nTuesday–Sunday 11:00am–2:00pm and 5:00pm–9:00pm",
            'disclaimer': "Menu items and prices subject to change."
        }
    
    def load_group_order(self) -> List[str]:
        """Load group order from file."""
        group_file = "group_order.txt"
        if not os.path.exists(group_file):
            logger.error(f"❌ {group_file} not found")
            sys.exit(1)
            
        with open(group_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    
    def generate_all_formats(self) -> None:
        """Generate menu in all formats."""
        try:
            group_order = self.load_group_order()
            grouped_items = self.menu_service.get_grouped_menu_items(
                group_order=group_order,
                include_3pd=self.include_3pd,
                include_prices=self.include_prices
            )
            
            self._generate_text_menu(grouped_items, group_order)
            self._generate_pdf_menu(grouped_items, group_order)
            self._generate_html_menu(grouped_items, group_order)
            
            logger.info("✅ All menu formats generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating menus: {e}")
            raise
    
    def _generate_text_menu(self, grouped_items: Dict[str, List[Dict]], group_order: List[str]) -> None:
        """Generate text format menu."""
        with open(self.text_file, "w") as f:
            # Header
            f.write(f"{self.restaurant_info['name']} – Takeout Menu\n")
            f.write(f"{self.restaurant_info['address']}\n")
            f.write(f"{self.restaurant_info['phone']} • {self.restaurant_info['website']}\n\n")
            
            # Menu items
            for group in group_order:
                items = grouped_items.get(group, [])
                if not items:
                    continue
                    
                f.write(f"🌟 {group}\n")
                for item in items:
                    if self.include_prices and item['formatted_price']:
                        f.write(f"  • {item['name']:<50} {item['formatted_price']}\n")
                    else:
                        f.write(f"  • {item['name']}\n")
                f.write("\n")
            
            # Footer
            f.write(f"Hours:\n{self.restaurant_info['hours']}\n\n")
            f.write(f"{self.restaurant_info['disclaimer']}\n")
        
        logger.info(f"📝 Saved: {self.text_file}")
    
    def _generate_pdf_menu(self, grouped_items: Dict[str, List[Dict]], group_order: List[str]) -> None:
        """Generate PDF format menu."""
        # This is a simplified version - you can expand with your existing PDF logic
        c = canvas.Canvas(self.pdf_file, pagesize=letter)
        w, h = letter
        
        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(w / 2, h - 50, self.restaurant_info['name'])
        
        # Add your existing PDF generation logic here...
        
        c.save()
        logger.info(f"📄 Saved: {self.pdf_file}")
    
    def _generate_html_menu(self, grouped_items: Dict[str, List[Dict]], group_order: List[str]) -> None:
        """Generate HTML format menu."""
        with open(self.html_file, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{self.restaurant_info['name']} – Takeout Menu</title>
<style>
body {{ font-family: sans-serif; max-width: 800px; margin: auto; padding:2em; background:#fffefb }}
h1 {{ text-align: center; }}
.group {{ margin-top: 2em; }}
.item {{ display: flex; justify-content: space-between; padding: 4px 0; }}
footer {{ margin-top: 3em; font-size: 0.9em; text-align: center; }}
</style></head><body>
<h1>{self.restaurant_info['name']} – Takeout Menu</h1>
<p style="text-align:right">{self.restaurant_info['address']}<br>
{self.restaurant_info['phone']} • <a href="https://{self.restaurant_info['website']}">{self.restaurant_info['website']}</a></p>
""")
            
            # Menu items
            for group in group_order:
                items = grouped_items.get(group, [])
                if not items:
                    continue
                    
                f.write(f'<div class="group"><h2>{group}</h2>\n')
                for item in items:
                    if self.include_prices and item['formatted_price']:
                        f.write(f'<div class="item"><span>{item["name"]}</span><span>{item["formatted_price"]}</span></div>\n')
                    else:
                        f.write(f'<div class="item"><span>{item["name"]}</span></div>\n')
                f.write('</div>\n')
            
            # Footer
            f.write(f"""
<footer>
<p>Hours: {self.restaurant_info['hours'].replace(chr(10), ' • ')}</p>
<p>{self.restaurant_info['disclaimer']}</p>
</footer>
</body></html>""")
        
        logger.info(f"🌐 Saved: {self.html_file}")

def main():
    """Main entry point."""
    try:
        generator = MenuGenerator()
        generator.generate_all_formats()
        return 0
    except Exception as e:
        logger.error(f"Menu generation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

