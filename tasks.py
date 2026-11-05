"""Task set: small, self-authored Python coding tasks with unit tests.
Self-authored to avoid contamination with public benchmarks. Each task has a reference
solution used only to validate that the tests are correct (python bench.py validate)."""

TASKS = [
 dict(id="palindrome", difficulty=1, entry="is_palindrome",
  prompt="Write a Python function is_palindrome(s: str) -> bool that returns True if s reads the same forwards and backwards, ignoring case and any non-alphanumeric characters.",
  tests='''assert is_palindrome("A man, a plan, a canal: Panama")
assert not is_palindrome("hello")
assert is_palindrome("")
assert is_palindrome("No 'x' in Nixon")''',
  reference='''def is_palindrome(s):
    t=[c.lower() for c in s if c.isalnum()]
    return t==t[::-1]'''),
 dict(id="flatten", difficulty=1, entry="flatten",
  prompt="Write a Python function flatten(x) that takes an arbitrarily nested list of integers and returns a flat list of the integers in order.",
  tests='''assert flatten([1,[2,[3,[4]]],5])==[1,2,3,4,5]
assert flatten([])==[]
assert flatten([[[]]])==[]
assert flatten([1,2])==[1,2]''',
  reference='''def flatten(x):
    out=[]
    for i in x:
        out.extend(flatten(i) if isinstance(i,list) else [i])
    return out'''),
 dict(id="roman", difficulty=2, entry="roman_to_int",
  prompt="Write a Python function roman_to_int(s: str) -> int that converts a Roman numeral (I, V, X, L, C, D, M, with subtractive notation) to an integer.",
  tests='''assert roman_to_int("III")==3
assert roman_to_int("IV")==4
assert roman_to_int("MCMXCIV")==1994
assert roman_to_int("LVIII")==58''',
  reference='''def roman_to_int(s):
    v={'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    t=0
    for i,c in enumerate(s):
        t+= -v[c] if i+1<len(s) and v[c]<v[s[i+1]] else v[c]
    return t'''),
 dict(id="duration", difficulty=2, entry="parse_duration",
  prompt="Write a Python function parse_duration(s: str) -> int that parses strings like '1h30m', '45s', '2d4h', '90m' into a total number of seconds. Units are d, h, m, s. Raise ValueError for an empty string or any string with an unknown unit or stray characters.",
  tests='''assert parse_duration("1h30m")==5400
assert parse_duration("45s")==45
assert parse_duration("2d4h")==2*86400+4*3600
assert parse_duration("90m")==5400
for bad in ["", "5x", "abc", "1h 30m", "h"]:
    try:
        parse_duration(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)''',
  reference='''import re
def parse_duration(s):
    if not re.fullmatch(r'(\\d+[dhms])+', s):
        raise ValueError(s)
    m={'d':86400,'h':3600,'m':60,'s':1}
    return sum(int(n)*m[u] for n,u in re.findall(r'(\\d+)([dhms])',s))'''),
 dict(id="brackets", difficulty=2, entry="balanced",
  prompt="Write a Python function balanced(s: str) -> bool that returns True if every (), [], {} bracket in s is correctly matched and nested. Other characters are ignored.",
  tests='''assert balanced("([]{})")
assert not balanced("([)]")
assert not balanced("(")
assert balanced("a(b)c")
assert not balanced("}{")''',
  reference='''def balanced(s):
    p={')':'(',']':'[','}':'{'}
    st=[]
    for c in s:
        if c in '([{': st.append(c)
        elif c in p:
            if not st or st.pop()!=p[c]: return False
    return not st'''),
 dict(id="intervals", difficulty=3, entry="merge_intervals",
  prompt="Write a Python function merge_intervals(iv) that takes a list of [start, end] pairs (unsorted, may overlap or touch) and returns a sorted list of merged [start, end] lists. Intervals that touch at an endpoint (e.g. [1,3] and [3,5]) must be merged.",
  tests='''assert merge_intervals([[1,3],[2,6],[8,10],[15,18]])==[[1,6],[8,10],[15,18]]
assert merge_intervals([[1,3],[3,5]])==[[1,5]]
assert merge_intervals([])==[]
assert merge_intervals([[5,6],[1,2]])==[[1,2],[5,6]]
assert merge_intervals([[1,10],[2,3]])==[[1,10]]''',
  reference='''def merge_intervals(iv):
    out=[]
    for a,b in sorted(iv):
        if out and a<=out[-1][1]: out[-1][1]=max(out[-1][1],b)
        else: out.append([a,b])
    return out'''),
 dict(id="topk", difficulty=3, entry="top_k_words",
  prompt="Write a Python function top_k_words(text: str, k: int) -> list that returns the k most frequent words as (word, count) tuples. Words are lowercase alphabetic runs (split on any non-letter). Ties are broken alphabetically.",
  tests='''assert top_k_words("the cat and the hat and the bat", 2)==[("the",3),("and",2)]
assert top_k_words("b a b a c", 3)==[("a",2),("b",2),("c",1)]
assert top_k_words("", 3)==[]
assert top_k_words("Hello, hello! HELLO?", 1)==[("hello",3)]''',
  reference='''import re
from collections import Counter
def top_k_words(text,k):
    c=Counter(re.findall(r'[a-z]+',text.lower()))
    return sorted(c.items(), key=lambda x:(-x[1],x[0]))[:k]'''),
 dict(id="lru", difficulty=3, entry="LRUCache",
  prompt="Write a Python class LRUCache with __init__(self, capacity: int), get(self, key) which returns the value or -1 if absent, and put(self, key, value). When capacity is exceeded, evict the least recently used key. Both get and put count as use.",
  tests='''c=LRUCache(2)
c.put(1,1); c.put(2,2)
assert c.get(1)==1
c.put(3,3)
assert c.get(2)==-1
c.put(4,4)
assert c.get(1)==-1
assert c.get(3)==3 and c.get(4)==4
c.put(3,9)
assert c.get(3)==9''',
  reference='''from collections import OrderedDict
class LRUCache:
    def __init__(self,capacity):
        self.c=capacity; self.d=OrderedDict()
    def get(self,k):
        if k not in self.d: return -1
        self.d.move_to_end(k); return self.d[k]
    def put(self,k,v):
        self.d[k]=v; self.d.move_to_end(k)
        if len(self.d)>self.c: self.d.popitem(last=False)'''),
 dict(id="spiral", difficulty=4, entry="spiral",
  prompt="Write a Python function spiral(m) that takes a non-empty rectangular matrix (list of lists) and returns its elements in clockwise spiral order starting at the top-left, as a flat list.",
  tests='''assert spiral([[1,2,3],[4,5,6],[7,8,9]])==[1,2,3,6,9,8,7,4,5]
assert spiral([[1,2,3,4],[5,6,7,8],[9,10,11,12]])==[1,2,3,4,8,12,11,10,9,5,6,7]
assert spiral([[1]])==[1]
assert spiral([[1],[2],[3]])==[1,2,3]
assert spiral([[1,2,3]])==[1,2,3]''',
  reference='''def spiral(m):
    out=[]
    m=[r[:] for r in m]
    while m:
        out+=m.pop(0)
        m=[list(r) for r in zip(*m)][::-1]
    return out'''),
 dict(id="dijkstra", difficulty=4, entry="shortest_path",
  prompt="Write a Python function shortest_path(graph, src, dst) where graph is a dict mapping node -> list of (neighbor, weight) with non-negative weights. Return the minimum total weight from src to dst, or None if dst is unreachable. Nodes with no outgoing edges may be absent as keys.",
  tests='''g={"a":[("b",1),("c",4)],"b":[("c",2),("d",6)],"c":[("d",3)]}
assert shortest_path(g,"a","d")==6
assert shortest_path(g,"a","a")==0
assert shortest_path(g,"d","a") is None
assert shortest_path({},"x","y") is None
assert shortest_path({"a":[("b",0)]},"a","b")==0''',
  reference='''import heapq
def shortest_path(graph,src,dst):
    dist={src:0}; h=[(0,src)]
    while h:
        d,u=heapq.heappop(h)
        if u==dst: return d
        if d>dist.get(u,float('inf')): continue
        for v,w in graph.get(u,[]):
            nd=d+w
            if nd<dist.get(v,float('inf')):
                dist[v]=nd; heapq.heappush(h,(nd,v))
    return None'''),
]

# Hidden tests: never shown to any model and never used for feedback or escalation decisions.
# Visible tests (the 'tests' field) are what the harness may run and feed back; hidden tests score the outcome.
HIDDEN = {
 "palindrome": '''assert not is_palindrome("race a car")
assert is_palindrome("Was it a car or a cat I saw?")
assert not is_palindrome("0P")
assert is_palindrome(".,")''',
 "flatten": '''assert flatten([[1],[2,[3]],[[[4]]]])==[1,2,3,4]
assert flatten([0,[0]])==[0,0]
assert flatten([[],[1,[]],[]])==[1]''',
 "roman": '''assert roman_to_int("IX")==9
assert roman_to_int("XL")==40
assert roman_to_int("MMXXIV")==2024
assert roman_to_int("CDXLIV")==444
assert roman_to_int("I")==1''',
 "duration": '''assert parse_duration("0s")==0
assert parse_duration("1d")==86400
assert parse_duration("10h5m3s")==36303
for bad in ["1", "1s2", "-5s", " 5s", "s5"]:
    try:
        parse_duration(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for %r" % bad)''',
 "brackets": '''assert balanced("")
assert balanced("{[()()]}")
assert not balanced("(]")
assert not balanced("((")
assert balanced("x")''',
 "intervals": '''assert merge_intervals([[1,4],[0,4]])==[[0,4]]
assert merge_intervals([[1,4],[2,3]])==[[1,4]]
assert merge_intervals([[2,3],[4,5],[6,7],[8,9],[1,10]])==[[1,10]]
assert merge_intervals([[1,2],[3,4]])==[[1,2],[3,4]]''',
 "topk": '''assert top_k_words("a a b", 5)==[("a",2),("b",1)]
assert top_k_words("x-y x_y", 2)==[("x",2),("y",2)]
assert top_k_words("a1b a", 2)==[("a",2),("b",1)]
assert top_k_words("a b", 0)==[]''',
 "lru": '''c=LRUCache(1)
c.put(1,1); c.put(2,2)
assert c.get(1)==-1 and c.get(2)==2
c=LRUCache(2)
c.put(1,1); c.put(2,2); c.put(1,10); c.put(3,3)
assert c.get(2)==-1 and c.get(1)==10
assert LRUCache(3).get(5)==-1''',
 "spiral": '''assert spiral([[1,2],[3,4]])==[1,2,4,3]
assert spiral([[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]])==[1,2,3,4,8,12,16,15,14,13,9,5,6,7,11,10]
assert spiral([[1,2],[3,4],[5,6]])==[1,2,4,6,5,3]''',
 "dijkstra": '''assert shortest_path({"a":[("b",1)],"b":[("a",1),("c",1)]},"a","c")==2
assert shortest_path({"s":[("t",10),("u",1)],"u":[("t",2)]},"s","t")==3
assert shortest_path({"a":[("b",1)]},"a","z") is None''',
}
for _t in TASKS:
    _t["hidden"] = HIDDEN[_t["id"]]
