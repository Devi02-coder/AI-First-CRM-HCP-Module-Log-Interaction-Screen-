import urllib.request

try:
    with urllib.request.urlopen("http://localhost:5173/", timeout=5) as resp:
        html = resp.read().decode("utf-8")
        print("Vite Frontend Server Response Status:", resp.status)
        print("HTML length:", len(html))
        print("First 200 chars:")
        print(html[:200])
        if "id=\"root\"" in html or "id='root'" in html:
            print("[SUCCESS] Found root element in served HTML!")
        else:
            print("[WARN] Root element not found.")
except Exception as e:
    print("[ERROR] Failed to contact Vite frontend server:", e)
