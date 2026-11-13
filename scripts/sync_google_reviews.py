#!/usr/bin/env python3
"""Update the RAM Repair homepage review badge using the official Business Profile API."""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

def request_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

def main():
    keys = ("GBP_CLIENT_ID", "GBP_CLIENT_SECRET", "GBP_REFRESH_TOKEN", "GBP_ACCOUNT_ID", "GBP_LOCATION_ID")
    if not all(os.environ.get(key) for key in keys):
        print("Google Business Profile connection not configured; leaving site unchanged.")
        return
    token_data = urllib.parse.urlencode({
        "client_id": os.environ["GBP_CLIENT_ID"],
        "client_secret": os.environ["GBP_CLIENT_SECRET"],
        "refresh_token": os.environ["GBP_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    token = request_json("https://oauth2.googleapis.com/token", data=token_data,
                         headers={"Content-Type": "application/x-www-form-urlencoded"})["access_token"]
    account = os.environ["GBP_ACCOUNT_ID"].removeprefix("accounts/")
    location = os.environ["GBP_LOCATION_ID"].removeprefix("locations/")
    url = f"https://mybusiness.googleapis.com/v4/accounts/{urllib.parse.quote(account)}/locations/{urllib.parse.quote(location)}/reviews?pageSize=1"
    payload = request_json(url, headers={"Authorization": "Bearer " + token})
    count = payload.get("totalReviewCount")
    rating = payload.get("averageRating")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError("Invalid review count; refusing to change homepage.")
    if not isinstance(rating, (int, float)) or not 1 <= rating <= 5:
        raise ValueError("Invalid rating; refusing to change homepage.")
    # Only claim all reviews are five stars when Google reports a perfect average.
    label = f"{count} Five-Star Google Reviews" if rating == 5 else f"{count} Google Reviews · {rating:.1f}★ Rating"
    path = Path("index.html")
    original = path.read_text(encoding="utf-8")
    pattern = r'(?<=<strong class="trust-stars" aria-hidden="true">★★★★★</strong> )[^<]*(?=</span>)'
    updated, matches = re.subn(pattern, lambda _: label, original)
    if matches != 1:
        raise ValueError(f"Expected exactly one review badge, found {matches}; refusing update.")
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(f"Updated review badge: {label}")
    else:
        print("Review badge already current.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Review sync failed; site left unchanged: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
