"""检查字体使用情况"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path

# 读取代码中定义的优先字体列表
priority_fonts = [
    "simhei.ttf",      # 黑体
    "simkai.ttf",      # 楷体
    "simfang.ttf",     # 仿宋
    "simsun.ttc",      # 宋体
    "msyh.ttc",        # 微软雅黑
    "msyhbd.ttc",      # 微软雅黑粗体
    "msyhl.ttc",       # 微软雅黑细体
    "msjh.ttc",        # 微软正黑体
    "mingliub.ttc",    # 细明体
]

backend_fonts_dir = Path(r"D:\wwwroot\demo\sanxia_demo\backend\fonts")

print("=" * 70)
print("字体文件使用情况分析")
print("=" * 70)
print()

# 获取所有字体文件
all_fonts = []
for ext in [".ttf", ".ttc", ".otf"]:
    all_fonts.extend(backend_fonts_dir.glob(f"*{ext}"))

all_fonts = sorted(all_fonts)

print(f"总共字体文件数: {len(all_fonts)}")
print()

# 分类字体
used_fonts = []
priority_but_not_exists = []
unused_fonts = []

# 检查优先字体
print("【优先字体列表】(按查找顺序)")
print("-" * 70)
for i, font_name in enumerate(priority_fonts, 1):
    font_path = backend_fonts_dir / font_name
    if font_path.exists():
        size = font_path.stat().st_size / 1024 / 1024  # MB
        status = "✓ 存在" if i == 1 else "✓ 备用"
        print(f"{i}. {font_name:20} {status:10} [{size:.2f} MB]")
        used_fonts.append(font_path)
        if i == 1:
            print(f"   → 实际使用: 此字体会被优先使用")
    else:
        print(f"{i}. {font_name:20} ✗ 不存在")
        priority_but_not_exists.append(font_name)

print()
print("【其他字体文件】(不在优先列表中)")
print("-" * 70)

for font_path in all_fonts:
    if font_path.name.lower() not in [f.lower() for f in priority_fonts]:
        size = font_path.stat().st_size / 1024 / 1024  # MB
        print(f"  {font_path.name:40} [{size:.2f} MB] - 不会被使用")
        unused_fonts.append(font_path)

if not unused_fonts:
    print("  (无)")

print()
print("=" * 70)
print("总结")
print("=" * 70)
print(f"✓ 会被使用的字体: {len(used_fonts)} 个")
print(f"  - 实际使用: 1 个 ({priority_fonts[0]})")
print(f"  - 备用字体: {len(used_fonts) - 1} 个")
print(f"✗ 不会被使用的字体: {len(unused_fonts)} 个")

if unused_fonts:
    total_unused_size = sum(f.stat().st_size for f in unused_fonts) / 1024 / 1024
    print(f"  总大小: {total_unused_size:.2f} MB")
    print()
    print("建议删除的文件:")
    for font_path in unused_fonts:
        print(f"  - {font_path.name}")

print()
