"""
Export utilities for Amazon scraper data
Handles exporting scraped data to various formats including TXT, PDF, and Excel
"""

import os
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import xlsxwriter
import json

class DataExporter:
    """Handles exporting scraped data to various file formats"""
    
    def __init__(self, output_dir="amazon_data"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def export_to_txt(self, products, filename_prefix):
        """Export products to a formatted text file"""
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Amazon Product Search Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, product in enumerate(products, 1):
                f.write(f"Product {i}:\n")
                f.write(f"Title: {product.get('title', 'N/A')}\n")
                f.write(f"Price: {product.get('price', 'N/A')}\n")
                f.write(f"Rating: {product.get('rating', 'N/A')} ⭐\n")
                f.write(f"Reviews: {product.get('reviews_count', 'N/A')}\n")
                f.write(f"URL: {product.get('url', 'N/A')}\n")
                
                if product.get('features'):
                    f.write("\nFeatures:\n")
                    for feature in product['features']:
                        f.write(f"- {feature}\n")
                
                f.write("\n" + "-" * 80 + "\n\n")
        
        return filepath
    
    def export_to_pdf(self, products, filename_prefix):
        """Export products to a PDF file with formatting"""
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Amazon Product Search Results', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'C')
        pdf.ln(10)
        
        # Products
        for i, product in enumerate(products, 1):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"Product {i}", 0, 1)
            
            pdf.set_font('Arial', '', 10)
            
            # Product details
            details = [
                ('Title', product.get('title', 'N/A')),
                ('Price', product.get('price', 'N/A')),
                ('Rating', f"{product.get('rating', 'N/A')} ⭐"),
                ('Reviews', product.get('reviews_count', 'N/A')),
                ('URL', product.get('url', 'N/A'))
            ]
            
            for label, value in details:
                # Handle long text wrapping
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(20, 6, f"{label}:", 0, 0)
                pdf.set_font('Arial', '', 10)
                
                # Split long text into multiple lines if needed
                text = str(value)
                max_width = 160
                if pdf.get_string_width(text) > max_width:
                    words = text.split()
                    line = ""
                    for word in words:
                        if pdf.get_string_width(line + " " + word) <= max_width:
                            line += " " + word
                        else:
                            pdf.cell(0, 6, line.strip(), 0, 1)
                            line = word
                    if line:
                        pdf.cell(0, 6, line.strip(), 0, 1)
                else:
                    pdf.cell(0, 6, text, 0, 1)
            
            # Features
            if product.get('features'):
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 6, "Features:", 0, 1)
                pdf.set_font('Arial', '', 10)
                
                for feature in product['features']:
                    pdf.cell(10, 6, "•", 0, 0)
                    pdf.multi_cell(0, 6, feature)
            
            pdf.ln(10)
            pdf.cell(0, 0, "_" * 80, 0, 1)
            pdf.ln(10)
        
        pdf.output(filepath)
        return filepath
    
    def export_to_excel(self, products, filename_prefix):
        """Export products to a formatted Excel file"""
        filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create Excel writer with formatting
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        workbook = writer.book
        
        # Create formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#007bff',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'top'
        })
        
        url_format = workbook.add_format({
            'border': 1,
            'font_color': 'blue',
            'underline': True
        })
        
        # Convert products to DataFrame
        df = pd.DataFrame(products)
        
        # Basic info sheet
        basic_info = df[['title', 'price', 'rating', 'reviews_count', 'url']].copy()
        basic_info.columns = ['Title', 'Price', 'Rating', 'Reviews', 'URL']
        basic_info.to_excel(writer, sheet_name='Basic Info', index=False)
        
        # Format Basic Info sheet
        worksheet = writer.sheets['Basic Info']
        worksheet.set_column('A:A', 50)  # Title
        worksheet.set_column('B:B', 15)  # Price
        worksheet.set_column('C:C', 10)  # Rating
        worksheet.set_column('D:D', 15)  # Reviews
        worksheet.set_column('E:E', 50)  # URL
        
        # Apply formats
        for col_num, value in enumerate(basic_info.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Features sheet
        if any('features' in p for p in products):
            features_data = []
            for product in products:
                features = product.get('features', [])
                features_data.append({
                    'Title': product.get('title', 'N/A'),
                    'Features': '\n'.join(features)
                })
            
            features_df = pd.DataFrame(features_data)
            features_df.to_excel(writer, sheet_name='Features', index=False)
            
            # Format Features sheet
            worksheet = writer.sheets['Features']
            worksheet.set_column('A:A', 50)  # Title
            worksheet.set_column('B:B', 100)  # Features
            
            # Apply formats
            for col_num, value in enumerate(features_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        # Save and close
        writer.close()
        return filepath

def export_data(products, query, formats=None):
    """
    Export scraped data to multiple formats
    
    Args:
        products (list): List of product dictionaries
        query (str): Search query used (for filename)
        formats (list): List of formats to export to ('txt', 'pdf', 'excel')
    
    Returns:
        dict: Mapping of format to exported filepath
    """
    if formats is None:
        formats = ['txt', 'pdf', 'excel']
    
    exporter = DataExporter()
    filename_prefix = f"amazon_{query.replace(' ', '_').lower()}"
    results = {}
    
    for fmt in formats:
        try:
            if fmt == 'txt':
                filepath = exporter.export_to_txt(products, filename_prefix)
                results['txt'] = filepath
            elif fmt == 'pdf':
                filepath = exporter.export_to_pdf(products, filename_prefix)
                results['pdf'] = filepath
            elif fmt == 'excel':
                filepath = exporter.export_to_excel(products, filename_prefix)
                results['excel'] = filepath
        except Exception as e:
            print(f"Error exporting to {fmt}: {e}")
    
    return results
