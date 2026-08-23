import qrcode

BASE_URL = "https://abc123.ngrok-free.app"

product_id = 1

url = f"{BASE_URL}/echelon_flow/product/{product_id}/"

qr = qrcode.make(url)

qr.save(f"product_{product_id}_qr.png")

print("QR generated successfully!")
print("URL:", url)