# 修复 image_service.py 中导致 GBK 编码崩溃的 emoji 字符
import re

with open('image_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有可能导致 GBK 编码问题的 emoji / 特殊 Unicode
replacements = {
    '\u2705': '[OK]',      # ✅
    '\u274c': '[X]',       # ❌
    '\u26a0\ufe0f': '[!]', # ⚠️
    '\u26a0': '[!]',       # ⚠
    '\U0001f3a8': '[*]',   # 🎨
    '\U0001f4ce': '[~]',   # 📎
    '\u2b50': '[*]',       # ⭐
    '\U0001f916': '[AI]',  # 🤖
    '\u2728': '[*]',       # ✨
    '\U0001f4dd': '[>]',   # 📝
    '\U0001f5bc': '[>]',   # 🖼
    '\u2192': '->',        # →
    '\u2190': '<-',        # ←
    '\u2500': '-',         # ─
    '\u2550': '=',         # ═
    '\u2502': '|',         # │
    '\u251c': '|',         # ├
    '\u2514': '|',         # └
    '\u252c': '-',         # ┬
    '\u2534': '-',         # ┴
    '\u253c': '+',         # ┼
}

for old, new in replacements.items():
    content = content.replace(old, new)

# 也替换 print 语句中任何超出 BMP 的字符
def safe_replace(match):
    char = match.group(0)
    if ord(char) > 0x7F:
        try:
            char.encode('gbk')
            return char
        except UnicodeEncodeError:
            return '?'
    return char

# 只对 print(...) 行做安全替换
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'print(' in line:
        lines[i] = re.sub(r'[^\x00-\x7F]', safe_replace, line)

content = '\n'.join(lines)

with open('image_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done: emoji replaced')
