import os
import pandas as pd

SAMPLE_PRODUCTS = [
    {
        "SKU": "LAP_15",
        "Name": "Gaming Laptop 15-inch",
        "Length (mm)": 360.0,
        "Width (mm)": 250.0,
        "Height (mm)": 25.0,
        "Weight (kg)": 2.20,
        "Barcode": "890123456001",
        "Fragile (TRUE/FALSE)": "TRUE",
        "Stackable (TRUE/FALSE)": "TRUE",
        "Max Stack Weight (kg)": 30.0,
        "Allowed Rotations (XYZ/XY/Z)": "XY",
        "Category": "Computers"
    },
    {
        "SKU": "HDST_BT",
        "Name": "Wireless ANC Headset",
        "Length (mm)": 200.0,
        "Width (mm)": 180.0,
        "Height (mm)": 90.0,
        "Weight (kg)": 0.35,
        "Barcode": "890123456002",
        "Fragile (TRUE/FALSE)": "FALSE",
        "Stackable (TRUE/FALSE)": "TRUE",
        "Max Stack Weight (kg)": 50.0,
        "Allowed Rotations (XYZ/XY/Z)": "XYZ",
        "Category": "Audio"
    },
    {
        "SKU": "TAB_10",
        "Name": "10-inch Tablet Pro",
        "Length (mm)": 245.0,
        "Width (mm)": 175.0,
        "Height (mm)": 15.0,
        "Weight (kg)": 0.48,
        "Barcode": "890123456003",
        "Fragile (TRUE/FALSE)": "TRUE",
        "Stackable (TRUE/FALSE)": "TRUE",
        "Max Stack Weight (kg)": 40.0,
        "Allowed Rotations (XYZ/XY/Z)": "XYZ",
        "Category": "Electronics"
    },
    {
        "SKU": "PRN_LSR",
        "Name": "Desktop Laser Printer",
        "Length (mm)": 410.0,
        "Width (mm)": 370.0,
        "Height (mm)": 280.0,
        "Weight (kg)": 8.50,
        "Barcode": "890123456004",
        "Fragile (TRUE/FALSE)": "TRUE",
        "Stackable (TRUE/FALSE)": "FALSE",
        "Max Stack Weight (kg)": 0.0,
        "Allowed Rotations (XYZ/XY/Z)": "Z",
        "Category": "Office"
    },
    {
        "SKU": "SPK_BT",
        "Name": "Portable Bluetooth Speaker",
        "Length (mm)": 180.0,
        "Width (mm)": 70.0,
        "Height (mm)": 70.0,
        "Weight (kg)": 0.60,
        "Barcode": "890123456005",
        "Fragile (TRUE/FALSE)": "FALSE",
        "Stackable (TRUE/FALSE)": "TRUE",
        "Max Stack Weight (kg)": 60.0,
        "Allowed Rotations (XYZ/XY/Z)": "XYZ",
        "Category": "Audio"
    },
    {
        "SKU": "CAM_4K",
        "Name": "4K Action Camera Kit",
        "Length (mm)": 120.0,
        "Width (mm)": 100.0,
        "Height (mm)": 80.0,
        "Weight (kg)": 0.40,
        "Barcode": "890123456006",
        "Fragile (TRUE/FALSE)": "TRUE",
        "Stackable (TRUE/FALSE)": "TRUE",
        "Max Stack Weight (kg)": 30.0,
        "Allowed Rotations (XYZ/XY/Z)": "XYZ",
        "Category": "Electronics"
    }
]

def generate_sample_excel_template(target_path: str):
    """Generates a formatted Excel sample template at target_path."""
    df = pd.DataFrame(SAMPLE_PRODUCTS)
    
    # Write Excel with openpyxl engine
    with pd.ExcelWriter(target_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Product Catalog", index=False)
        worksheet = writer.sheets["Product Catalog"]
        
        # Auto-adjust column widths
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

def generate_sample_csv_template(target_path: str):
    """Generates a CSV sample template at target_path."""
    df = pd.DataFrame(SAMPLE_PRODUCTS)
    df.to_csv(target_path, index=False, encoding='utf-8')

if __name__ == "__main__":
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data")
    os.makedirs(demo_dir, exist_ok=True)
    excel_path = os.path.join(demo_dir, "sample_product_catalog.xlsx")
    csv_path = os.path.join(demo_dir, "sample_product_catalog.csv")
    
    generate_sample_excel_template(excel_path)
    generate_sample_csv_template(csv_path)
    print(f"Generated sample Excel template: {excel_path}")
    print(f"Generated sample CSV template: {csv_path}")
