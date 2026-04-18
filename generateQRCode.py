import os
import qrcode
import psycopg2
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# Load database credentials
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD')
    )

def generate_qr_codes(target_company):
    print(f"\n--- Generating targeted QR Codes for: {target_company} ---")
    os.makedirs("qrcodes", exist_ok=True)
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM projects;")
            projects = cur.fetchall()

            if not projects:
                print("No projects found. Did you run init_db.py?")
                return

            for project_id, name in projects:
                # 1. The URL embedded IN the image is for physical scans
                base_url = "http://127.0.0.1:5001"
                scan_url = f"{base_url}/track/{project_id}?source=scan&target={target_company}"
                
                # 2. Generate the base QR Code
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(scan_url)
                qr.make(fit=True)
                
                # Convert to a format Pillow (PIL) can edit
                qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
                qr_width, qr_height = qr_img.size
                
                # 3. Create a new, taller canvas to hold the text
                text_padding = 80  # Adds 80 pixels of space at the bottom
                final_img = Image.new('RGB', (qr_width, qr_height + text_padding), 'white')
                
                # Paste the QR code at the very top (0, 0)
                final_img.paste(qr_img, (0, 0))
                
                # 4. Draw the text at the bottom
                draw = ImageDraw.Draw(final_img)
                
                # Load default font (Using a basic size that works universally)
                # Note: We use a simple fallback font so it works on any Mac/PC without errors
                try:
                    font = ImageFont.truetype("Arial", 30) # Try to use Arial if available
                except IOError:
                    font = ImageFont.load_default() # Fallback to standard pixel font

                text = "Scan or Click to View"
                
                # Math to perfectly center the text
                # We get the bounding box of the text to calculate its width
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (qr_width - text_width) / 2
                y = qr_height + (text_padding - text_height) / 2 - 5 # Center vertically in the padded area
                
                # Write the text in a subtle dark gray
                draw.text((x, y), text, fill="#333333", font=font)
                
                # 5. Save the final hybrid image
                safe_name = name.lower().replace(" ", "_")
                filename = f"qrcodes/{safe_name}_{target_company.lower()}.png"
                final_img.save(filename)
                
                print(f"Success -> {filename}")
                
                # PRINT THE CLICK URL SO we CAN COPY IT INTO YOUR PDF
                click_url = f"{base_url}/track/{project_id}?source=click&target={target_company}"
                print(f"  Link to attach in PDF: {click_url}\n")

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    company = input("Enter the target company (e.g., Shopify, Google): ")
    if not company.strip():
        company = "General"
    
    generate_qr_codes(company)