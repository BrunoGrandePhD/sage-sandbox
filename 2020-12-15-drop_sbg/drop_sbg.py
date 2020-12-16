#!/usr/bin/env python3

import re
import sys
import yaml


def drop_sbg(x):
    if isinstance(x, dict):
        for k, v in list(x.items()):
            if isinstance(v, str):
                x[k] = trim_ws(v)
            if k.startswith("sbg:"):
                del x[k]
            else:
                drop_sbg(v)
    elif isinstance(x, list):
        for idx, i in enumerate(x):
            if isinstance(i, str):
                x[idx] = trim_ws(i)
            drop_sbg(i)
    else:
        pass
    return x


def trim_ws(x):
    x = re.sub(r"(\n *| +)", " ", x)
    return x


with open(sys.argv[1]) as infile, open(sys.argv[2], "w") as outfile:
    d = yaml.safe_load(infile)
    d = drop_sbg(d)
    yaml.safe_dump(d, outfile, width=10000)

