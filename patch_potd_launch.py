#!/usr/bin/env python3
"""Reset POTD for launch. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Change POTD formula to use launch day offset
old_func = '''function getPlayerOfTheDay() {
  const now = new Date();
  const daysSinceEpoch = Math.floor(now.getTime() / 86400000);
  const idx = daysSinceEpoch % POTD_POOL.length;
  return POTD_POOL[idx];
}'''
new_func = '''function getPlayerOfTheDay() {
  const now = new Date();
  const daysSinceEpoch = Math.floor(now.getTime() / 86400000);
  const launchDay = 20518; // March 5, 2026
  const idx = Math.abs(daysSinceEpoch - launchDay) % POTD_POOL.length;
  return POTD_POOL[idx];
}'''
if old_func in src:
    src = src.replace(old_func, new_func)
    changes += 1
    print("1. POTD formula reset to launch day offset")

# 2. Reorder pool - use exact match from file
import re
m = re.search(r'const POTD_POOL = \[.*?\];', src, re.DOTALL)
if m:
    new_pool = '''const POTD_POOL = [
  // Launch week: marquee names
  "Gunnar Henderson","Juan Soto","Bobby Witt Jr.","Shohei Ohtani","Paul Skenes",
  "Aaron Judge","Konnor Griffin","Elly De La Cruz","Corbin Carroll","Julio Rodriguez",
  // Week 2: stars + top prospects
  "Fernando Tatis Jr.","Bryce Harper","Mookie Betts","Samuel Basallo","Tarik Skubal",
  "Ronald Acuña Jr.","Corey Seager","Freddie Freeman","Mike Trout","Roki Sasaki",
  // Week 3: young stars + breakouts
  "Jackson Chourio","Adley Rutschman","Kyle Tucker","Yordan Alvarez","Garrett Crochet",
  "Riley Greene","Jackson Merrill","James Wood","Cal Raleigh","Kevin McGonigle",
  // Week 4+: deep roster
  "Vladimir Guerrero Jr.","Rafael Devers","Jose Ramirez","Francisco Lindor","Kyle Schwarber",
  "Trea Turner","Bo Bichette","Pete Alonso","Willy Adames","Max Clark",
  "Anthony Volpe","CJ Abrams","Jarren Duran","Roman Anthony","JJ Wetherholt",
  "Jackson Holliday","Dylan Crews","Evan Carter","Corbin Burnes","Zack Wheeler",
  "Matt McLain","Dansby Swanson","Marcus Semien","Alex Bregman","Manny Machado",
  "Pete Crow-Armstrong","Steven Kwan","Michael Harris II","Chris Sale","Cole Ragans",
  "Logan Webb","Dylan Cease","Colt Keith","Zach Neto","Matt Olson",
  "Kerry Carpenter","Bryson Stott","Cody Bellinger","Maikel Garcia","Aidan Miller",
  "Grayson Rodriguez","Hunter Brown","Jared Jones","Luis Gil","Tanner Bibee",
];'''
    src = src[:m.start()] + new_pool + src[m.end():]
    changes += 1
    print("2. Reordered POTD pool: Henderson launch day, Soto day 2, Witt day 3")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
