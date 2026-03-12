#!/usr/bin/env python3
"""Generate Excalidraw architecture diagram for data.agent -- v2 with pictograms"""
import json, random

random.seed(42)
_counter = 0

def _id():
    global _counter
    _counter += 1
    return f"el_{_counter:04d}"

def _seed():
    return random.randint(1, 2**31 - 1)

elements = []
arrow_bindings = {}

def _base(eid, etype, x, y, w, h, stroke, bg, fill, sw, rough, opacity, groups, rnd):
    return {
        "id": eid, "type": etype,
        "x": x, "y": y, "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg, "fillStyle": fill,
        "strokeWidth": sw, "roughness": rough, "opacity": opacity,
        "groupIds": groups or [], "frameId": None,
        "roundness": {"type": rnd} if rnd else None,
        "seed": _seed(), "version": 2, "versionNonce": _seed(),
        "isDeleted": False, "boundElements": [],
        "updated": 1700000000000, "link": None, "locked": False
    }

def box(x, y, w, h, stroke="#1e1e1e", bg="transparent", fill="hachure",
        sw=1, rough=1, opacity=100, groups=None, dash=False):
    eid = _id()
    el = _base(eid, "rectangle", x, y, w, h, stroke, bg, fill, sw, rough, opacity, groups, 3)
    if dash:
        el["strokeStyle"] = "dashed"
    elements.append(el)
    arrow_bindings[eid] = []
    return eid

def ellipse(x, y, w, h, stroke="#1e1e1e", bg="transparent", fill="hachure",
            sw=1, rough=1, opacity=100, groups=None):
    eid = _id()
    el = _base(eid, "ellipse", x, y, w, h, stroke, bg, fill, sw, rough, opacity, groups, 2)
    elements.append(el)
    arrow_bindings[eid] = []
    return eid

def txt(x, y, s, size=16, color="#1e1e1e", family=1, align="left", groups=None, w=None):
    eid = _id()
    lines = s.split("\n")
    if w is None:
        factor = 0.55 if family == 1 else (0.48 if family == 2 else 0.52)
        w = max(len(l) for l in lines) * size * factor
    h = len(lines) * size * 1.25
    el = _base(eid, "text", x, y, w, h, color, "transparent", "solid", 1, 1, 100, groups, None)
    el.update({"text": s, "fontSize": size, "fontFamily": family,
               "textAlign": align, "verticalAlign": "top",
               "containerId": None, "originalText": s, "lineHeight": 1.25})
    elements.append(el)
    return eid

def dia(x, y, w, h, stroke="#1e1e1e", bg="transparent", fill="hachure", rough=1, groups=None):
    eid = _id()
    el = _base(eid, "diamond", x, y, w, h, stroke, bg, fill, 1, rough, 100, groups, 2)
    elements.append(el)
    arrow_bindings[eid] = []
    return eid

def line(pts, stroke="#6b7280", sw=1, rough=1, groups=None, opacity=100, dash=False):
    eid = _id()
    x0, y0 = pts[0]
    rel = [[px - x0, py - y0] for px, py in pts]
    w = max(max(p[0] for p in rel) - min(p[0] for p in rel), 1)
    h = max(max(p[1] for p in rel) - min(p[1] for p in rel), 1)
    el = _base(eid, "line", x0, y0, w, h, stroke, "transparent", "solid", sw, rough, opacity, groups, 2)
    el.update({"points": rel, "startBinding": None, "endBinding": None,
               "startArrowhead": None, "endArrowhead": None, "lastCommittedPoint": None})
    if dash:
        el["strokeStyle"] = "dashed"
    elements.append(el)
    return eid

def arr(pts, stroke="#6b7280", sw=1, rough=1, start=None, end=None,
        end_head="arrow", groups=None, opacity=100, dash=False):
    eid = _id()
    x0, y0 = pts[0]
    rel = [[px - x0, py - y0] for px, py in pts]
    w = max(max(p[0] for p in rel) - min(p[0] for p in rel), 1)
    h = max(max(p[1] for p in rel) - min(p[1] for p in rel), 1)
    el = _base(eid, "arrow", x0, y0, w, h, stroke, "transparent", "solid", sw, rough, opacity, groups, 2)
    el.update({
        "points": rel,
        "startBinding": {"elementId": start, "focus": 0, "gap": 8} if start else None,
        "endBinding": {"elementId": end, "focus": 0, "gap": 8} if end else None,
        "startArrowhead": None, "endArrowhead": end_head,
        "lastCommittedPoint": None
    })
    if dash:
        el["strokeStyle"] = "dashed"
    elements.append(el)
    if start and start in arrow_bindings:
        arrow_bindings[start].append({"id": eid, "type": "arrow"})
    if end and end in arrow_bindings:
        arrow_bindings[end].append({"id": eid, "type": "arrow"})
    return eid


# ================================================================
# ICON HELPERS -- simple geometric pictograms
# ================================================================

def icon_person(x, y, color, scale=1.0):
    """Simple person: circle head + trapezoid body"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    # Head
    ellipse(x + 5*s, y, 14*s, 14*s, color, color, "solid", 1, 1, 80, g)
    # Body
    box(x + 1*s, y + 16*s, 22*s, 16*s, color, color, "solid", 1, 1, 80, g)

def icon_window(x, y, color, scale=1.0):
    """Browser window: rectangle with top bar and dots"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    # Frame
    box(x, y, 28*s, 22*s, color, color, "solid", 1, 1, 60, g)
    # Top bar
    line([(x, y + 7*s), (x + 28*s, y + 7*s)], color, sw=1, groups=g)
    # Dots in top bar
    ellipse(x + 3*s, y + 2*s, 3*s, 3*s, "#ffffff", "#ffffff", "solid", 1, 0, 90, g)
    ellipse(x + 8*s, y + 2*s, 3*s, 3*s, "#ffffff", "#ffffff", "solid", 1, 0, 90, g)
    ellipse(x + 13*s, y + 2*s, 3*s, 3*s, "#ffffff", "#ffffff", "solid", 1, 0, 90, g)

def icon_plug(x, y, color, scale=1.0):
    """API plug: two arrows pointing at each other"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    arr([(x, y + 6*s), (x + 12*s, y + 6*s)], color, sw=2, groups=g)
    arr([(x + 26*s, y + 14*s), (x + 14*s, y + 14*s)], color, sw=2, groups=g)

def icon_gear(x, y, color, scale=1.0):
    """Simplified gear: circle with notches"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    ellipse(x + 4*s, y + 4*s, 18*s, 18*s, color, "transparent", "solid", 2, 1, 80, g)
    ellipse(x + 9*s, y + 9*s, 8*s, 8*s, color, color, "solid", 1, 1, 80, g)
    # Notches (small lines radiating out)
    line([(x + 13*s, y), (x + 13*s, y + 4*s)], color, sw=2, groups=g)
    line([(x + 13*s, y + 22*s), (x + 13*s, y + 26*s)], color, sw=2, groups=g)
    line([(x, y + 13*s), (x + 4*s, y + 13*s)], color, sw=2, groups=g)
    line([(x + 22*s, y + 13*s), (x + 26*s, y + 13*s)], color, sw=2, groups=g)

def icon_brain(x, y, color, scale=1.0):
    """Brain: overlapping ellipses"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    ellipse(x, y + 4*s, 20*s, 22*s, color, color, "hachure", 1, 1, 40, g)
    ellipse(x + 10*s, y, 20*s, 22*s, color, color, "hachure", 1, 1, 40, g)
    ellipse(x + 5*s, y + 10*s, 20*s, 18*s, color, color, "hachure", 1, 1, 40, g)

def icon_terminal(x, y, color, scale=1.0):
    """Code terminal: rectangle with > prompt"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    box(x, y, 28*s, 22*s, color, color, "solid", 1, 1, 50, g)
    # > prompt
    line([(x + 5*s, y + 7*s), (x + 12*s, y + 11*s), (x + 5*s, y + 15*s)], color, sw=2, groups=g)
    # Cursor line
    line([(x + 15*s, y + 14*s), (x + 23*s, y + 14*s)], color, sw=2, groups=g)

def icon_container(x, y, color, scale=1.0):
    """Container/sandbox: nested boxes"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    box(x, y, 28*s, 24*s, color, "transparent", "solid", 2, 1, 70, g)
    box(x + 5*s, y + 5*s, 18*s, 14*s, color, color, "hachure", 1, 1, 50, g)

def icon_cylinder(x, y, color, scale=1.0):
    """Database cylinder"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    w, h = 26*s, 28*s
    eh = 8*s
    ellipse(x, y, w, eh, color, color, "solid", 1, 1, 60, g)
    box(x, y + eh/2, w, h - eh, color, color, "solid", 1, 1, 60, g)
    ellipse(x, y + h - eh, w, eh, color, color, "solid", 1, 1, 60, g)

def icon_lightning(x, y, color, scale=1.0):
    """Lightning bolt: zig-zag line"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    line([(x + 12*s, y), (x + 4*s, y + 12*s), (x + 14*s, y + 12*s), (x + 6*s, y + 24*s)],
         color, sw=2.5, groups=g)

def icon_question(x, y, color, scale=1.0):
    """Question mark in circle"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    ellipse(x, y, 24*s, 24*s, color, color, "solid", 1, 1, 30, g)
    txt(x + 5*s, y + 1*s, "?", int(18*s), color, family=2, groups=g)

def icon_checklist(x, y, color, scale=1.0):
    """Checklist: lines with checkmarks"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    # Three lines with checkboxes
    for i in range(3):
        ly = y + i * 8*s
        box(x, ly, 6*s, 6*s, color, "transparent" if i > 0 else color,
            "solid", 1, 1, 70, g)
        line([(x + 9*s, ly + 3*s), (x + 22*s, ly + 3*s)], color, sw=1.5, groups=g)

def icon_list(x, y, color, scale=1.0):
    """List/sources: stacked rectangles"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    for i in range(3):
        box(x + i*3*s, y + i*4*s, 20*s, 12*s, color, color, "solid", 1, 1, max(30, 60 - i*15), g)

def icon_loop(x, y, color, scale=1.0):
    """Circular loop arrow"""
    gid = f"icon_{_id()}"
    g = [gid]
    s = scale
    ellipse(x, y, 28*s, 28*s, color, "transparent", "solid", 2, 1, 70, g)
    # Arrowhead at the top-right
    arr([(x + 22*s, y + 2*s), (x + 26*s, y + 8*s)], color, sw=2, groups=g, end_head="arrow")

def step_num(x, y, num, color):
    """Numbered circle as flow step indicator"""
    gid = f"step_{_id()}"
    g = [gid]
    ellipse(x, y, 32, 32, color, color, "solid", 1, 0, 85, g)
    # Center the number
    nx = x + (10 if num < 10 else 5)
    txt(nx, y + 5, str(num), 16, "#ffffff", family=2, groups=g)


# ================================================================
# COLORS
# ================================================================
C = {
    "user":  {"s": "#7c3aed", "b": "#f3e8ff"},
    "front": {"s": "#3b82f6", "b": "#dbeafe"},
    "api":   {"s": "#1d4ed8", "b": "#bfdbfe"},
    "orch":  {"s": "#0e7490", "b": "#cffafe"},
    "loop":  {"s": "#059669", "b": "#d1fae5"},
    "llm":   {"s": "#047857", "b": "#a7f3d0"},
    "tool":  {"s": "#15803d", "b": "#bbf7d0"},
    "sand":  {"s": "#a16207", "b": "#fef3c7"},
    "db":    {"s": "#b91c1c", "b": "#fee2e2"},
    "pipe":  {"s": "#c2410c", "b": "#ffedd5"},
    "evt":   {"s": "#7c3aed", "b": "#ede9fe"},
}
GRAY = "#6b7280"
DARK = "#1f2937"
SUB = "#6b7280"

# ================================================================
# SECTION 1: USER ACTIONS
# ================================================================
icon_person(1340, 0, C["user"]["s"], 1.2)
txt(1380, 5, "USER", 28, C["user"]["s"], align="center")

bw, bh, bgap = 220, 62, 22
total = 5 * bw + 4 * bgap
sx = (3000 - total) / 2

user_labels = [
    ("Upload data files", icon_list),
    ("Ask a question", icon_question),
    ("Answer a choice", None),
    ("Select dashboard cards", None),
    ("Launch auto-analysis", icon_lightning),
]
user_boxes = []
for i, (label, icon_fn) in enumerate(user_labels):
    x = sx + i * (bw + bgap)
    bid = box(x, 50, bw, bh, C["user"]["s"], C["user"]["b"])
    if icon_fn:
        icon_fn(x + 10, 60, C["user"]["s"], 0.9)
        txt(x + 42, 65, label, 14, C["user"]["s"])
    else:
        txt(x + 14, 65, label, 14, C["user"]["s"])
    user_boxes.append(bid)

step_num(sx - 55, 60, 1, C["user"]["s"])

# ================================================================
# SECTION 2: FRONTEND
# ================================================================
front_id = box(700, 180, 1600, 90, C["front"]["s"], C["front"]["b"])
icon_window(715, 190, C["front"]["s"], 1.1)
txt(755, 188, "BROWSER", 22, C["front"]["s"])
txt(720, 222, "Chat interface  |  Real-time event stream (SSE)  |  Interactive Plotly charts  |  File upload", 13, SUB)
txt(720, 242, "Everything updates live as the agent works -- the user sees thinking, tool calls, and response tokens appear", 11, "#9ca3af")

step_num(660, 200, 2, C["front"]["s"])

# ================================================================
# SECTION 3: API
# ================================================================
api_id = box(700, 340, 1600, 75, C["api"]["s"], C["api"]["b"])
icon_plug(715, 352, C["api"]["s"], 1.0)
txt(755, 350, "API GATEWAY", 20, C["api"]["s"])
txt(720, 380, "REST endpoints:  projects  |  sources (upload)  |  chats  |  messages  |  pipelines  |  dashboard cards", 12, SUB)

step_num(660, 355, 3, C["api"]["s"])

# ================================================================
# SECTION 4: ORCHESTRATION
# ================================================================
ow, ogap, oh = 440, 30, 115
ototal = 3 * ow + 2 * ogap
osx = (3000 - ototal) / 2

pm_id = box(osx, 490, ow, oh, C["orch"]["s"], C["orch"]["b"])
icon_gear(osx + 10, 498, C["orch"]["s"], 0.9)
txt(osx + 45, 498, "ProjectManager", 18, C["orch"]["s"])
txt(osx + 15, 528, "Loads projects from DB into memory\nHydrates data source profiles\nManages sandbox containers\nOne instance for the whole server", 11, SUB)

ct_id = box(osx + ow + ogap, 490, ow, oh, C["orch"]["s"], C["orch"]["b"])
icon_gear(osx + ow + ogap + 10, 498, C["orch"]["s"], 0.9)
txt(osx + ow + ogap + 45, 498, "ChatThread", 18, C["orch"]["s"])
txt(osx + ow + ogap + 15, 528, "Owns conversation history\nRebuilds agent graph if sources change\nOne-operation-at-a-time lock\nOne instance per active conversation", 11, SUB)

tc_id = box(osx + 2*(ow+ogap), 490, ow, oh, C["orch"]["s"], C["orch"]["b"])
icon_gear(osx + 2*(ow+ogap) + 10, 498, C["orch"]["s"], 0.9)
txt(osx + 2*(ow+ogap) + 45, 498, "ToolContext", 18, C["orch"]["s"])
txt(osx + 2*(ow+ogap) + 15, 528, "Carried into every tool call:\nproject ID, sandbox access,\ndata source registry,\ncurrent turn state, todo list", 11, SUB)

step_num(osx - 55, 520, 4, C["orch"]["s"])

# ================================================================
# SECTION 5: AGENT LOOP
# ================================================================
loop_y = 680
loop_h = 720
loop_bg = box(180, loop_y, 2640, loop_h, C["loop"]["s"], "#ecfdf5",
              fill="solid", sw=2, rough=1, opacity=20, dash=True)
icon_loop(195, loop_y + 8, C["loop"]["s"], 1.2)
txt(235, loop_y + 10, "AGENT REASONING LOOP", 26, C["loop"]["s"])
txt(235, loop_y + 46, "The core cycle: the agent thinks, acts, observes the result, and repeats until it has a full answer.", 13, SUB)

step_num(135, loop_y + 15, 5, C["loop"]["s"])

# -- LLM --
llm_x, llm_y, llm_w, llm_h = 300, loop_y + 100, 500, 220
llm_id = box(llm_x, llm_y, llm_w, llm_h, C["llm"]["s"], C["llm"]["b"], sw=2)
icon_brain(llm_x + 15, llm_y + 12, C["llm"]["s"], 1.3)
txt(llm_x + 60, llm_y + 14, "LLM (Gemini)", 24, C["llm"]["s"])

txt(llm_x + 20, llm_y + 55, "Receives:", 14, C["llm"]["s"])
txt(llm_x + 20, llm_y + 76, "  data profiles (columns, types, samples)\n  full conversation history\n  results from previous tool calls", 12, SUB)

txt(llm_x + 20, llm_y + 135, "Can:", 14, C["llm"]["s"])
txt(llm_x + 20, llm_y + 156, "  think step by step (visible to user)\n  write and run Python code\n  ask clarifying questions", 12, SUB)

# -- Decision diamond --
dec_x, dec_y, dec_w, dec_h = 1050, loop_y + 160, 180, 130
dec_id = dia(dec_x, dec_y, dec_w, dec_h, C["loop"]["s"], C["loop"]["b"])
txt(dec_x + 42, dec_y + 48, "decide", 20, C["loop"]["s"])

# -- Response box --
resp_x, resp_y, resp_w, resp_h = 1470, loop_y + 90, 460, 180
resp_id = box(resp_x, resp_y, resp_w, resp_h, C["llm"]["s"], "#d1fae5")
txt(resp_x + 20, resp_y + 14, "Generate response", 22, C["llm"]["s"])
txt(resp_x + 20, resp_y + 50, "Text streamed token by token\nUser sees it appear progressively\nCan reference generated figures\nMay suggest follow-up questions", 12, SUB)
txt(resp_x + 20, resp_y + 135, "-- this is the EXIT of the loop --", 13, C["loop"]["s"])

# Arrow: LLM -> Decision
arr([(llm_x + llm_w, llm_y + llm_h / 2),
     (dec_x, dec_y + dec_h / 2)],
    C["loop"]["s"], sw=2, start=llm_id, end=dec_id)

# Arrow: Decision -> Response
arr([(dec_x + dec_w, dec_y + 30),
     (resp_x, resp_y + resp_h / 2)],
    C["loop"]["s"], sw=1.5, start=dec_id, end=resp_id)
txt(dec_x + dec_w + 15, dec_y, "has enough\ninfo to answer", 12, "#059669")

# Arrow: Decision -> Tools (down)
arr([(dec_x + dec_w / 2, dec_y + dec_h),
     (dec_x + dec_w / 2, loop_y + 420)],
    C["loop"]["s"], sw=1.5, start=dec_id)
txt(dec_x + dec_w / 2 + 12, dec_y + dec_h + 20, "needs to\ncompute\nor clarify", 12, "#059669")

# -- Tools row --
tool_y = loop_y + 440
txt(320, tool_y - 26, "TOOLS -- what the agent can do", 16, C["tool"]["s"])

# execute_python
ep_x, ep_w, ep_h = 300, 500, 125
ep_id = box(ep_x, tool_y, ep_w, ep_h, C["tool"]["s"], C["tool"]["b"], sw=2)
icon_terminal(ep_x + 12, tool_y + 10, C["tool"]["s"], 1.1)
txt(ep_x + 50, tool_y + 10, "execute_python", 18, C["tool"]["s"])
txt(ep_x + 18, tool_y + 42, "Runs arbitrary Python code in the sandbox\nReturns: figures, computed values, prints, cards\nVariables persist between calls (stateful)\nThe main analysis workhorse", 11, SUB)

# ask_question
aq_x, aq_w, aq_h = 850, 360, 125
aq_id = box(aq_x, tool_y, aq_w, aq_h, C["tool"]["s"], C["tool"]["b"])
icon_question(aq_x + 12, tool_y + 8, C["tool"]["s"], 1.1)
txt(aq_x + 45, tool_y + 10, "ask_question", 18, C["tool"]["s"])
txt(aq_x + 18, tool_y + 42, "Pauses the agent to ask the user\n2 to 4 clickable choices\nFull state checkpointed\nResumes exactly where it stopped", 11, SUB)

# list_sources
ls_x, ls_w, ls_h = 1260, 260, 105
ls_id = box(ls_x, tool_y, ls_w, ls_h, C["tool"]["s"], C["tool"]["b"])
icon_list(ls_x + 12, tool_y + 10, C["tool"]["s"], 0.8)
txt(ls_x + 42, tool_y + 10, "list_sources", 16, C["tool"]["s"])
txt(ls_x + 18, tool_y + 38, "Discover available\ndatasets: names,\nrow counts, columns", 11, SUB)

# todo
td_x, td_w, td_h = 1570, 260, 105
td_id = box(td_x, tool_y, td_w, td_h, C["tool"]["s"], C["tool"]["b"])
icon_checklist(td_x + 12, tool_y + 10, C["tool"]["s"], 1.0)
txt(td_x + 40, tool_y + 10, "todo", 16, C["tool"]["s"])
txt(td_x + 18, tool_y + 38, "Track multi-step\nanalysis progress:\npending / in progress / done", 11, SUB)

# -- Error handling note --
box(1260, tool_y + 115, 570, 65, "#9ca3af", "#f9fafb", "solid", 1, 1, 40)
txt(1275, tool_y + 122, "Error handling: Python errors sent back to the LLM as context", 11, "#9ca3af")
txt(1275, tool_y + 140, "so it can fix its code and retry automatically.", 11, "#9ca3af")
txt(1275, tool_y + 158, "Long conversations auto-summarized to fit context window.", 11, "#9ca3af")

# ================================================================
# LOOP-BACK ARROW
# ================================================================
loop_bot = tool_y + ep_h
arr([(ep_x + 50, loop_bot),
     (ep_x + 50, loop_bot + 40),
     (150, loop_bot + 40),
     (150, llm_y + llm_h * 0.6),
     (llm_x, llm_y + llm_h * 0.6)],
    C["loop"]["s"], sw=3, rough=1, end=llm_id, dash=True)
txt(40, loop_y + 340, "result feeds back\ninto reasoning\n(loop repeats)", 14, C["loop"]["s"])

# ================================================================
# INTERRUPT FLOW (ask_question -> user -> resume)
# ================================================================
arr([(aq_x + aq_w, tool_y + 35),
     (2700, tool_y + 35),
     (2700, 225)],
    C["user"]["s"], sw=1.5, dash=True, end=front_id)
txt(2710, loop_y + 160, "interrupt:\nshows choices\nto user, waits\nfor answer,\nthen resumes\nright here", 12, C["user"]["s"])

# ================================================================
# SECTION 6: SANDBOX
# ================================================================
sand_y = 1510
sand_id = box(150, sand_y, 1180, 360, C["sand"]["s"], C["sand"]["b"], sw=2)
icon_container(170, sand_y + 10, C["sand"]["s"], 1.2)
txt(210, sand_y + 12, "ISOLATED SANDBOX", 24, C["sand"]["s"])
txt(170, sand_y + 48, "One Docker container per project -- completely isolated from the host system", 13, SUB)

step_num(100, sand_y + 18, 6, C["sand"]["s"])

sby = sand_y + 80
box(175, sby, 350, 80, C["sand"]["s"], "#fef9c3", opacity=60)
icon_terminal(185, sby + 8, C["sand"]["s"], 0.8)
txt(218, sby + 8, "Python kernel (IPython)", 14, C["sand"]["s"])
txt(188, sby + 32, "Variables persist between calls\nLike an invisible notebook", 11, SUB)

box(550, sby, 350, 80, C["sand"]["s"], "#fef9c3", opacity=60)
icon_list(560, sby + 10, C["sand"]["s"], 0.7)
txt(590, sby + 8, "Pre-loaded environment", 14, C["sand"]["s"])
txt(563, sby + 32, "pandas, plotly, numpy, regex\n+ uploaded DataFrames by name", 11, SUB)

box(175, sby + 95, 350, 80, C["sand"]["s"], "#fef9c3", opacity=60)
txt(188, sby + 103, "4 output channels", 14, C["sand"]["s"])
txt(188, sby + 125, "figure (Plotly chart)\nresult (value for the LLM)\ncards (dashboard KPIs)\nstdout (print output)", 10, SUB)

box(550, sby + 95, 350, 80, C["sand"]["s"], "#fef9c3", opacity=60)
txt(563, sby + 103, "Security constraints", 14, C["sand"]["s"])
txt(563, sby + 125, "512 MB RAM  |  60s timeout\n100 PIDs  |  no internet\nno privilege escalation", 11, SUB)

box(175, sby + 190, 725, 40, C["sand"]["s"], "#fef9c3", opacity=40)
txt(188, sby + 198, "Lifecycle: created on demand  |  auto-destroyed after 5 min idle  |  max 20 containers  |  oldest evicted first", 11, SUB)

# Arrow: execute_python -> sandbox
arr([(ep_x + ep_w / 2, tool_y + ep_h),
     (ep_x + ep_w / 2, sand_y)],
    C["sand"]["s"], sw=1.5, start=ep_id, end=sand_id)
txt(ep_x + ep_w / 2 + 12, tool_y + ep_h + 70, "Python code", 12, C["sand"]["s"])

# Arrow: sandbox result back to LLM
arr([(195, sand_y),
     (195, llm_y + llm_h),
     (llm_x + 100, llm_y + llm_h)],
    C["sand"]["s"], sw=1.5, dash=True, end=llm_id)
txt(50, sand_y - 100, "figures +\ncomputed data\nback to LLM", 12, C["sand"]["s"])

# ================================================================
# SECTION 7: DATABASE
# ================================================================
db_y = 1510
db_id = box(1430, db_y, 1150, 360, C["db"]["s"], C["db"]["b"])
icon_cylinder(1450, db_y + 10, C["db"]["s"], 1.3)
txt(1495, db_y + 12, "PERSISTENT MEMORY (PostgreSQL)", 22, C["db"]["s"])
txt(1450, db_y + 48, "Everything that survives server restarts", 13, SUB)

step_num(1385, db_y + 18, 7, C["db"]["s"])

tables = [
    ("projects", "name, description, model, suggested questions"),
    ("sources", "name, profile (types, nulls, cardinality), columns"),
    ("chats", "title (auto-generated by LLM), pending question state"),
    ("messages", "role, text, code, figures, tool steps, thinking, todos"),
    ("dashboard_cards", "type (metric/chart), title, value, figure, position"),
    ("checkpoints", "full agent state -- enables resume after interrupt"),
]
tby = db_y + 78
for i, (name, desc) in enumerate(tables):
    ty = tby + i * 44
    box(1455, ty, 520, 38, C["db"]["s"], "#fef2f2", opacity=60)
    txt(1468, ty + 4, name, 14, C["db"]["s"])
    txt(1468, ty + 22, desc, 10, SUB)

# Arrow: loop -> database (persistence)
arr([(2670, loop_y + loop_h),
     (2670, db_y + 60),
     (2580, db_y + 60)],
    C["db"]["s"], sw=1, dash=True, end=db_id)
txt(2680, 1300, "persist messages,\nfigures, tool steps,\ncheckpoints", 11, C["db"]["s"])

# ================================================================
# SECTION 8: PIPELINES
# ================================================================
pipe_y = 1960

# Insights
box(150, pipe_y, 1180, 190, C["pipe"]["s"], C["pipe"]["b"])
icon_lightning(170, pipe_y + 10, C["pipe"]["s"], 1.1)
txt(200, pipe_y + 10, "PIPELINE: Insights (automatic)", 20, C["pipe"]["s"])
txt(170, pipe_y + 42, "Runs without user interaction after data is uploaded", 12, SUB)

step_num(100, pipe_y + 15, 8, C["pipe"]["s"])

pfy = pipe_y + 72
box(175, pfy, 200, 50, C["pipe"]["s"], "#fed7aa", opacity=70)
txt(188, pfy + 10, "Data source profiles\n(structure, samples)", 11, SUB)
arr([(375, pfy + 25), (415, pfy + 25)], C["pipe"]["s"])
box(415, pfy, 200, 50, C["pipe"]["s"], "#fed7aa", opacity=70)
txt(428, pfy + 10, "LLM analyzes\n(low creativity T=0.3)", 11, SUB)
arr([(615, pfy + 25), (655, pfy + 25)], C["pipe"]["s"])
box(655, pfy, 250, 50, C["pipe"]["s"], "#fed7aa", opacity=70)
txt(668, pfy + 6, "Outputs:", 12, C["pipe"]["s"])
txt(668, pfy + 24, "dataset description\n+ suggested questions", 11, SUB)
txt(175, pipe_y + 155, "Saved to project -- visible in UI as exploration starting points", 11, "#9ca3af")

# Dashboard
box(1430, pipe_y, 1150, 190, C["pipe"]["s"], C["pipe"]["b"])
icon_lightning(1450, pipe_y + 10, C["pipe"]["s"], 1.1)
txt(1485, pipe_y + 10, "PIPELINE: Dashboard (automatic)", 20, C["pipe"]["s"])
txt(1450, pipe_y + 42, "Generates a complete dashboard without any interaction", 12, SUB)

pfy2 = pipe_y + 72
box(1455, pfy2, 160, 50, C["pipe"]["s"], "#fed7aa", opacity=70)
txt(1468, pfy2 + 14, "Data profiles", 11, SUB)
arr([(1615, pfy2 + 25), (1645, pfy2 + 25)], C["pipe"]["s"])
box(1645, pfy2, 170, 50, C["pipe"]["s"], "#fed7aa", opacity=70)
txt(1658, pfy2 + 10, "LLM writes\nPython code", 11, SUB)
arr([(1815, pfy2 + 25), (1845, pfy2 + 25)], C["pipe"]["s"])
box(1845, pfy2, 160, 50, C["pipe"]["s"], "#fed7aa", opacity=70)
txt(1858, pfy2 + 10, "Execute in\nsandbox", 11, SUB)
arr([(2005, pfy2 + 25), (2035, pfy2 + 25)], C["pipe"]["s"])
box(2035, pfy2, 210, 50, C["pipe"]["s"], "#fed7aa", opacity=70)
txt(2048, pfy2 + 6, "Outputs:", 12, C["pipe"]["s"])
txt(2048, pfy2 + 24, "KPI metric cards\n+ interactive charts", 11, SUB)
txt(1455, pipe_y + 155, "Cards validated, figures matched, then stored in database", 11, "#9ca3af")

# ================================================================
# SECTION 9: PROMPT SYSTEM
# ================================================================
prompt_y = pipe_y + 210
box(150, prompt_y, 2430, 60, "#6b7280", "#f9fafb", "solid", 1, 1, 50)
txt(175, prompt_y + 8, "SYSTEM PROMPT (injected into LLM):  assembled from modular blocks depending on context", 14, GRAY)
txt(175, prompt_y + 32, "Identity  +  Decision framework  +  Code rules  +  Error recovery  +  Source policy (adapts to 0 / 1 / N data sources)  +  Output format", 12, "#9ca3af")

# ================================================================
# CONNECTING ARROWS (between layers)
# ================================================================

# User -> Frontend
arr([(1500, 112), (1500, 180)], GRAY, sw=1.5, end=front_id)

# Frontend -> API
arr([(1350, 270), (1350, 340)], GRAY, sw=1.5, start=front_id, end=api_id)
txt(1360, 296, "requests", 11, SUB)

# API -> Frontend (events back)
arr([(1700, 340), (1700, 270)], C["evt"]["s"], sw=1.5, dash=True, start=api_id, end=front_id)
txt(1715, 290, "SSE events: thinking | tool calls | text tokens | figures | done", 10, C["evt"]["s"])

# API -> Orchestration
arr([(1500, 415), (1500, 490)], GRAY, sw=1.5, start=api_id, end=ct_id)

# Orchestration -> Agent Loop
arr([(1500, 605), (1500, 680)], GRAY, sw=2, start=ct_id, end=loop_bg)

# ================================================================
# LEGEND (top right)
# ================================================================
leg_x, leg_y = 2450, 5
box(leg_x, leg_y, 330, 115, "#d1d5db", "#f9fafb", "solid", 1, 0, 60)
txt(leg_x + 12, leg_y + 6, "Reading guide", 14, DARK, family=2)
txt(leg_x + 12, leg_y + 28, "Follow the numbered steps (1-8)\nSolid arrows = main flow\nDashed arrows = side effects\nGreen loop = agent repeats until done", 11, SUB)
# small colored boxes as legend
colors_leg = [
    (C["user"]["b"], "User actions"),
    (C["loop"]["b"], "Agent reasoning"),
    (C["sand"]["b"], "Code execution"),
    (C["db"]["b"], "Storage"),
]

# ================================================================
# POST-PROCESS: update boundElements on shapes
# ================================================================
for el in elements:
    eid = el.get("id")
    if eid in arrow_bindings and arrow_bindings[eid]:
        el["boundElements"] = arrow_bindings[eid]

# ================================================================
# OUTPUT
# ================================================================
output = {
    "type": "excalidraw",
    "version": 2,
    "source": "data.agent architecture generator v2",
    "elements": elements,
    "appState": {
        "gridSize": None,
        "viewBackgroundColor": "#ffffff"
    },
    "files": {}
}

outpath = "/home/orso/Repositories/data.agent/docs/architecture.excalidraw"
with open(outpath, "w") as f:
    json.dump(output, f, indent=2)

print(f"Generated {len(elements)} elements -> {outpath}")
