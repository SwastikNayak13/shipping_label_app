import pandas as pd
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

st.title("📦 Shipping Label Generator (8 per A4 sheet)")

uploaded_file = st.file_uploader("Upload Shopify Orders CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = [c.strip() for c in df.columns]

    # Required columns
    required_cols = [
        "Name",
        "Shipping Name",
        "Shipping Street",
        "Shipping City",
        "Shipping Zip",
        "Shipping Province",
        "Shipping Phone",
        "Lineitem quantity",
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        st.stop()

    # Fill missing shipping info forward based on Name
    shipping_cols = [
        "Shipping Name",
        "Shipping Street",
        "Shipping City",
        "Shipping Zip",
        "Shipping Province",
        "Shipping Phone",
    ]
    df[shipping_cols] = df.groupby("Name")[shipping_cols].ffill()

    # Group by Name (order) and sum Lineitem quantity
    df_grouped = df.groupby(
        ["Name"] + shipping_cols, as_index=False
    )["Lineitem quantity"].sum()

    # Generate PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "Helvetica"
    style.fontSize = 10
    style.leading = 12

    LABEL_WIDTH = 90 * mm
    LABEL_HEIGHT = 65 * mm
    LEFT_MARGIN = 20 * mm
    TOP_MARGIN = 270 * mm
    H_SPACING = 10 * mm
    V_SPACING = 5 * mm

    for i, row in df_grouped.iterrows():
        phone = str(row["Shipping Phone"]).split(".")[0]
        text = f"""
        <b>DELIVERY TO:</b><br/>
        {row['Shipping Name']}<br/>
        {row['Shipping Street']}<br/>
        {row['Shipping City']}, {row['Shipping Province']} '{row['Shipping Zip']}'<br/>
        {phone}<br/>
        <b>Total Quantity:</b> {int(row['Lineitem quantity'])}
        """

        col = i % 2
        row_num = (i // 2) % 4
        x = LEFT_MARGIN + col * (LABEL_WIDTH + H_SPACING)
        y = TOP_MARGIN - row_num * (LABEL_HEIGHT + V_SPACING)

        para = Paragraph(text, style)
        w, h = para.wrap(LABEL_WIDTH, LABEL_HEIGHT)
        para.drawOn(c, x, y - h)

        if (i + 1) % 8 == 0:
            c.showPage()

    c.save()
    buffer.seek(0)

    st.success("✅ PDF generated successfully!")
    st.download_button(
        label="⬇️ Download Shipping Labels PDF",
        data=buffer,
        file_name="shipping_labels.pdf",
        mime="application/pdf",
    )
