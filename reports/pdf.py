import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(
    output_path: str,
    job_id: int,
    carton: dict,
    products_list: list,  # [{"sku": sku, "name": name, "length": l, "width": w, "height": h, "weight": wt}]
    selected_quantities: dict,  # {sku: qty}
    layout_result: dict
) -> str:
    """
    Generates a professional PDF Packing Slip Report at the specified output path.
    Returns the absolute path of the generated PDF file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles for Premium Aesthetics
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1A365D"),  # Slate Blue
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),  # Bright Blue
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748")  # Charcoal
    )

    body_bold_style = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []

    # Title & Metadata Header
    story.append(Paragraph(f"Packing Slip & Optimization Report", title_style))
    story.append(Paragraph(f"<b>Job ID:</b> #{job_id} &nbsp;|&nbsp; <b>Date:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 15))

    # Carton & Summary Metrics Row Table
    carton_dims_str = f"{carton['length']} x {carton['width']} x {carton['height']} mm"
    stats = layout_result["statistics"]
    
    summary_data = [
        [
            Paragraph("<b>CARTON DETAILS</b>", body_bold_style), 
            Paragraph("<b>SHIPPING SUMMARY</b>", body_bold_style)
        ],
        [
            Paragraph(f"Name: {carton['name']}<br/>Dimensions: {carton_dims_str}<br/>Max Load: {carton['max_weight']:.2f} kg<br/>Box Cost: ${carton['cost']:.2f}", body_style),
            Paragraph(f"Volumetric Weight: {layout_result['volumetric_weight']:.2f} kg<br/>Actual Total Weight: {layout_result['actual_weight']:.2f} kg<br/>Chargeable Weight: {layout_result['chargeable_weight']:.2f} kg<br/>Est. Shipping Cost: ${layout_result['shipping_cost']:.2f}", body_style)
        ],
        [
            Paragraph(f"<b>Volume Utilization:</b> {stats['space_utilization']:.1f}%", body_bold_style),
            Paragraph(f"<b>Packing Efficiency:</b> {stats['packing_efficiency_score']:.1f}%", body_bold_style)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[270, 270])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#E2E8F0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Product Quantities Table
    story.append(Paragraph("Packed Product Quantities", section_style))
    
    # Header
    prod_data = [[
        Paragraph("SKU", table_header_style),
        Paragraph("Product Name", table_header_style),
        Paragraph("Unit Dimensions (mm)", table_header_style),
        Paragraph("Unit Weight", table_header_style),
        Paragraph("Qty Packed", table_header_style)
    ]]
    
    # Row compilation
    prod_map = {p["sku"]: p for p in products_list}
    packed_counts = {}
    for layer in layout_result["layers"]:
        for pl in layer["placements"]:
            packed_counts[pl["sku"]] = packed_counts.get(pl["sku"], 0) + 1
            
    for sku, count in packed_counts.items():
        p_def = prod_map.get(sku, {"name": sku, "length": 0, "width": 0, "height": 0, "weight": 0})
        dims = f"{p_def['length']}x{p_def['width']}x{p_def['height']}"
        prod_data.append([
            Paragraph(sku, body_style),
            Paragraph(p_def["name"], body_style),
            Paragraph(dims, body_style),
            Paragraph(f"{p_def['weight']:.2f} kg", body_style),
            Paragraph(str(count), body_style)
        ])
        
    prod_table = Table(prod_data, colWidths=[90, 200, 110, 80, 60])
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(prod_table)
    story.append(Spacer(1, 15))

    # Layer Instructions
    story.append(Paragraph("Layer-by-Layer Packing Instructions (Bottom to Top)", section_style))
    
    for layer in layout_result["layers"]:
        layer_elements = []
        layer_idx = layer["layer_idx"]
        z_start = layer["z_start"]
        z_end = z_start + layer["height"]
        
        layer_title = f"Layer {layer_idx + 1} (Height: {z_start:.1f} - {z_end:.1f} mm)"
        layer_elements.append(Paragraph(layer_title, ParagraphStyle('LTitle', parent=body_bold_style, fontSize=11, textColor=colors.HexColor("#2C5282"))))
        
        # Placements in this layer table
        pl_data = [[
            Paragraph("Item ID", table_header_style),
            Paragraph("SKU", table_header_style),
            Paragraph("Product Name", table_header_style),
            Paragraph("Grid Position (Col, Row)", table_header_style),
            Paragraph("Rotated Size (mm)", table_header_style),
        ]]
        
        for pl in layer["placements"]:
            pos_str = f"Col {pl['gx']}, Row {pl['gy']}"
            size_str = f"{pl['length']} x {pl['width']} x {pl['height']}"
            pl_data.append([
                Paragraph(f"#{pl['id']}", body_style),
                Paragraph(pl['sku'], body_style),
                Paragraph(pl['name'], body_style),
                Paragraph(pos_str, body_style),
                Paragraph(size_str, body_style)
            ])
            
        pl_table = Table(pl_data, colWidths=[60, 90, 190, 100, 100])
        pl_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        layer_elements.append(pl_table)
        layer_elements.append(Spacer(1, 10))
        
        # Keep each layer layout block together to avoid orphans
        story.append(KeepTogether(layer_elements))

    # Build the document
    doc.build(story)
    return os.path.abspath(output_path)
