"""Analyze CAPTCHA success rate from logs"""
import re

with open('logs/extractor.log', 'r', encoding='utf-8', errors='ignore') as f:
    logs = f.readlines()

# Count CAPTCHA attempts and successes
solved = 0
failed = 0
success_loaded = 0

for line in logs:
    if 'CAPTCHA solved [' in line:
        solved += 1
    elif 'CAPTCHA could not be solved' in line or 'CAPTCHA failed' in line:
        failed += 1
    elif 'CAPTCHA solved successfully - details page loaded' in line:
        success_loaded += 1

total = solved + failed
success_rate = (solved / total * 100) if total > 0 else 0
actual_success_rate = (success_loaded / solved * 100) if solved > 0 else 0

print("\n=== CAPTCHA Performance ===")
print(f"Total attempts: {total}")
print(f"Tesseract read text: {solved}")
print(f"Failed to read: {failed}")
print(f"OCR success rate: {success_rate:.1f}%")
print(f"\nActually accepted by server: {success_loaded}")
print(f"Actual CAPTCHA accuracy: {actual_success_rate:.1f}%")
print(f"\nOverall success: {(success_loaded/total*100) if total > 0 else 0:.1f}%")
