#!/usr/bin/env python3
"""Swap POTD pool so today (March 20) shows a hitter. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Move Kyle Tucker into slot 14 (today), push Skubal to week 3, Crochet to end
old1 = '''  "Fernando Tatis Jr.","Bryce Harper","Mookie Betts","Samuel Basallo","Tarik Skubal",
  "Ronald Acuña Jr.","Corey Seager","Freddie Freeman","Mike Trout","Roki Sasaki",'''
new1 = '''  "Fernando Tatis Jr.","Bryce Harper","Mookie Betts","Samuel Basallo","Kyle Tucker",
  "Ronald Acuña Jr.","Corey Seager","Freddie Freeman","Mike Trout","Roki Sasaki",'''
if old1 in src:
    src = src.replace(old1, new1)
    changes += 1
    print("1. Kyle Tucker into slot 14 (today's POTD)")

old2 = '''  "Jackson Chourio","Adley Rutschman","Kyle Tucker","Yordan Alvarez","Garrett Crochet",'''
new2 = '''  "Jackson Chourio","Adley Rutschman","Yordan Alvarez","Tarik Skubal","Garrett Crochet",'''
if old2 in src:
    src = src.replace(old2, new2)
    changes += 1
    print("2. Moved Skubal to week 3")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print("Today's POTD: Kyle Tucker (hitter)")
