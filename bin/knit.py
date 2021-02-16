#!/usr/bin/env python
import re
import sys
import knittingneedles as knit

# read in a tutorial, and check the structure of it.
tuto = open(sys.argv[1], "r+")
tutorial_contents = tuto.read().split("\n")
chunks = []
patches = sys.argv[2:]

# load patches
diffs = []
for patch in patches:
    with open(patch, "r") as handle:
        data = handle.readlines()
        commit = data[2].split(": ")[2]
        data = [x.rstrip("\n") for x in data[5:-3]]
        diffs.append((commit, data))

current = None
diff_idx = 0
prev_line = None
for line, text in enumerate(tutorial_contents):
    m = re.match(knit.BOXES, text)
    if m:
        depth = m.group(1).count(">")
    else:
        depth = 0
    (unprefixed, prefix) = knit.stripN(text, depth)
    m0 = re.match(knit.BOX_PREFIX, unprefixed)
    m1 = re.match(knit.BOX_OPEN, unprefixed)
    m2 = re.match(knit.BOX_CLOSE, unprefixed)
    # print(current is not None, m0 is not None, m1 is not None, m2 is not None, '|', prefix, '|', text[0:100])

    if m0:
        current = []
    if m1 and current is None:
        current = []
        # print('hi', m0, m1, prev_line)
        # if '{% raw %}' in prev_line:
        # current.append(prev_line)

    if current is not None:
        current.append(unprefixed)
    else:
        chunks.append(text)

    # if current:
    # print(current, len(current), not m2)

    if current and len(current) > 2 and (current[-2].strip() == "```") and not m2:
        chunks.extend([prefix + x for x in current])
        # print(current)
        # chunks.append('REJECT)')
        # print('REJECT')
        current = None

    if m2 and current and len(current) > 0:
        # print(m2, current)
        (amount, _) = knit.removeWhitespacePrefix(current)
        prefix_text = prefix + (amount * " ")
        from_patch = diffs[diff_idx]

        # Compare the diff messages
        obs_msg = knit.extractCommitMsg(current).strip()
        exp_msg = from_patch[0].strip()
        if obs_msg != exp_msg:
            print("WARNING: Diff messages do NOT line up: {obs_msg} != {exp_msg}")

        # Knit it anyway
        new_diff = from_patch[1]
        chunks.append(prefix_text + "{% raw %}")
        chunks.append(prefix_text + "```diff")
        chunks.extend([f'{prefix}{amount * " "}{line}' for line in new_diff])
        chunks.append(prefix_text + "{% endraw %}")
        chunks.append(prefix_text + "```")
        chunks.append(prefix_text + '{: data-commit="%s"}' % exp_msg)
        diff_idx += 1
        current = None

    prev_line = text

# Overwrite the original tutorial
tuto.seek(0)
tuto.truncate(0)
# The last chunk is a newline for some reason.
for c in chunks[0:-1]:
    tuto.write(c + "\n")
tuto.close()
