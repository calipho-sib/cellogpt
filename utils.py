import os
import datetime


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def log_it(*things, duration_since=None):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    t1 = datetime.datetime.now()
    now = t1.isoformat().replace('T',' ')[:23]
    pid = "[" + str(os.getpid()) + "]"
    if duration_since is not None:
        duration = round((t1 - duration_since).total_seconds(),3)
        print(now, pid, *things, "duration", duration, flush=True)
    else:
        print(now, pid, *things, flush=True)


# ------------------------
class Term:
# ------------------------
    def __init__(self, id, prefLabel, altLabelList, parentIdList, scheme):
        self.id = id
        self.prefLabel = prefLabel
        self.altLabelList = altLabelList
        self.parentIdList = parentIdList
        self.scheme = scheme

    def __str__(self):
        return(f"Term({self.id}, {self.prefLabel}, alt: {self.altLabelList}, parents: {self.parentIdList} )")
