import subprocess

def test_model(model_name):
    print(f"Testing {model_name}...")
    try:
        cmd = f'gemini -m {model_name} "Hello"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SUCCESS: {model_name}")
            print(f"Output: {result.stdout.strip()[:50]}...")
            return True
        else:
            print(f"❌ FAIL: {model_name}")
            print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

print("--- DIAGNOSTIC START ---")
if not test_model("gemini-3-flash"):
    print("-> Trying fallback...")
    test_model("gemini-2.0-flash")
print("--- DIAGNOSTIC END ---")
