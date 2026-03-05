#!/usr/bin/env python3
"""Apply Option A FV color scale. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old_fv = """const FV_STYLES = {
  70: { label: "70 FV", bg: "linear-gradient(135deg, #ff6b9d, #c084fc, #60a5fa, #4ade80, #facc15, #fb923c)", color: "#fff", border: "none", glow: true },
  65: { label: "65 FV", bg: "linear-gradient(135deg, #dc2626, #991b1b, #7f1d1d)", color: "#fff", border: "none", glow: false },
  60: { label: "60 FV", bg: "linear-gradient(135deg, #93c5fd, #c4b5fd, #e0e7ff)", color: "#1e3a5f", border: "none", glow: false },
  55: { label: "55 FV", bg: "linear-gradient(135deg, #34d399, #10b981, #059669)", color: "#ffffff", border: "none", glow: false },
  50: { label: "50 FV", bg: "linear-gradient(135deg, #fef3c7, #fcd34d, #f59e0b)", color: "#78350f", border: "none", glow: false },
  45: { label: "45 FV", bg: "linear-gradient(135deg, #d4d4d8, #a1a1aa, #d4d4d8)", color: "#3f3f46", border: "none", glow: false },
  40: { label: "40 FV", bg: "linear-gradient(135deg, #d97706, #b45309, #92400e)", color: "#fef3c7", border: "none", glow: false },

};"""

new_fv = """const FV_STYLES = {
  70: { label: "70 FV", bg: "linear-gradient(135deg, #f59e0b, #ef4444, #ec4899, #a855f7, #3b82f6, #10b981)", color: "#fff", border: "none", glow: true },
  65: { label: "65 FV", bg: "linear-gradient(135deg, #7c3aed, #4f46e5, #3730a3)", color: "#e0e7ff", border: "none", glow: false },
  60: { label: "60 FV", bg: "linear-gradient(135deg, #0ea5e9, #0284c7, #0369a1)", color: "#e0f2fe", border: "none", glow: false },
  55: { label: "55 FV", bg: "linear-gradient(135deg, #10b981, #059669, #047857)", color: "#ecfdf5", border: "none", glow: false },
  50: { label: "50 FV", bg: "linear-gradient(135deg, #f59e0b, #d97706, #b45309)", color: "#fff", border: "none", glow: false },
  45: { label: "45 FV", bg: "linear-gradient(135deg, #6b7280, #4b5563, #374151)", color: "#e5e7eb", border: "none", glow: false },
  40: { label: "40 FV", bg: "linear-gradient(135deg, #78716c, #57534e, #44403c)", color: "#d6d3d1", border: "none", glow: false },

};"""

if old_fv in src:
    src = src.replace(old_fv, new_fv)
    open(APP, "w").write(src)
    print("Applied Option A — Deep Jewel Tones")
    print("  70: Spectrum (warm->cool rainbow)")
    print("  65: Deep Violet")
    print("  60: Sapphire")
    print("  55: Emerald")
    print("  50: Amber")
    print("  45: Gunmetal")
    print("  40: Stone")
else:
    print("ERROR: Could not find FV_STYLES block")
