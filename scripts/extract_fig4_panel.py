"""提取 Fig 5 的右下角 (f) panel 用于检查 (论文图号顺移后, fig04 → fig05)"""
from PIL import Image
img = Image.open(r"E:\Claude project\SCI5\WUDAPT-FUSE\figures\fig05_subcategory_gini_test.png")
W, H = img.size
print(f"Total size: {W} x {H}")

# 提取右下角 (f) panel：约右 1/3，下 1/2
left = W * 2 // 3 - 30
top = H // 2
right = W
bottom = H

panel = img.crop((left, top, right, bottom))
print(f"Cropped panel: {panel.size}")
panel.save(r"E:\Claude project\SCI5\WUDAPT-FUSE\figures\fig05_panelf_crop.png")
print("Saved fig05_panelf_crop.png")
