#!/usr/bin/env python3
"""
Update index.html with new assignment card
Usage: python update_index.py <hw_number> <hw_title> <category>
"""
import sys
import re

def update_index(hw_num, hw_title, category):
    """Add new assignment card to index.html"""

    # Read index.html
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Create the new card
    new_card = f'''    <a class="hwcard glass" href="hw{hw_num}_improved.html">
      <div class="go"><svg viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></div>
      <div class="hwnum">{hw_num}</div>
      <h3>{hw_title}</h3>
      <p>XX Questions — Multiple Choice</p>
      <div class="meta"><span class="chip open">Available Now</span><span class="chip c2">{category}</span></div>
    </a>'''

    # Find the marker and insert before it
    marker = '<!-- ⬆️ END BLOCK ⬆️ -->'

    if marker in content:
        # Insert the new card before the marker
        content = content.replace(marker, new_card + '\n    ' + marker)

        # Write back
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(content)

        print("SUCCESS: index.html updated")
        return 0
    else:
        print("ERROR: Marker not found in index.html")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python update_index.py <hw_number> <hw_title> <category>")
        sys.exit(1)

    hw_num = sys.argv[1]
    hw_title = sys.argv[2]
    category = sys.argv[3]

    sys.exit(update_index(hw_num, hw_title, category))
