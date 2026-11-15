# MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
# assemble site/index.html from the template + data + inlined Leaflet CSS
t = open("index.template.html").read()
t = t.replace("<!--LEAFLETCSS-->", "<style>/* Leaflet 1.9.4 (BSD-2) */\n" + open("leaflet.css").read() + "\n</style>")
t = t.replace("/*DATA*/null", open("app_data.json").read())
t = t.replace("const D =", 'const BASENOTE = "Basemap: NASA MGS MOLA terrain (USGS), shaded relief";\nconst D =', 1)
open("site/index.html", "w").write(t)
print("site/index.html", len(t) // 1024, "KB")
