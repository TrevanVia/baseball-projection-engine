#!/usr/bin/env python3
"""Fix Panel component to pass through onClick/mouse events. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old = """const Panel = ({children,title,sub,style={}}) => (
  <div className="via-panel" style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:12,padding:"18px 22px",boxShadow:"0 1px 3px rgba(26,54,104,0.04)",...style}}>"""

new = """const Panel = ({children,title,sub,style={},onClick,onMouseEnter,onMouseLeave}) => (
  <div className="via-panel" onClick={onClick} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:12,padding:"18px 22px",boxShadow:"0 1px 3px rgba(26,54,104,0.04)",...style}}>"""

if old in src:
    src = src.replace(old, new)
    open(APP, "w").write(src)
    print("Fixed: Panel now passes through onClick, onMouseEnter, onMouseLeave")
else:
    print("Target not found - may already be applied")
