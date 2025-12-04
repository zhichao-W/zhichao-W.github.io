#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""jemdoc version 0.7.3 (Python 3 port). Updated 2025-12-04.
Original copyright (C) 2007-2012 Jacob Mattingley.
This is a minimal, drop-in Python 3 conversion of the classic jemdoc script.
"""

# License notice from the original file:
# This file is part of jemdoc.
# jemdoc is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
# jemdoc is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

# The LaTeX equation portions of this file were initially based on
# latexmath2png, by Kamil Kisiel (kamil@kamikisiel.net).

import sys
import os
import re
import time
import io
import tempfile
import subprocess

PIPE = subprocess.PIPE

def info():
    print(__doc__)
    print('Platform: ' + sys.platform + '.')
    print('Python: %s, located at %s.' % (sys.version[:5], sys.executable))
    print('Equation support:', end=' ')
    (supported, message) = testeqsupport()
    if supported:
        print('yes.')
    else:
        print('no.')
    print(message)

def _first_line_or(msg, default=''):
    if not msg:
        return default
    return msg.splitlines()[0].strip()

def testeqsupport():
    supported = True
    msg = ''
    p = subprocess.run('latex --version', shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        msg += '  latex: not found.\n'
        supported = False
    else:
        msg += '  latex: ' + _first_line_or(p.stdout, 'unknown') + '.\n'
    p = subprocess.run('dvipng --version', shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        msg += '  dvipng: not found.\n'
        supported = False
    else:
        msg += '  dvipng: ' + _first_line_or(p.stdout, 'unknown') + '.\n'
    return (supported, msg[:-1])

class controlstruct(object):
    def __init__(self, infile, outfile=None, conf=None, inname=None, eqs=True,
                 eqdir='eqs', eqdpi=130):
        self.inname = inname
        self.inf = infile
        self.outf = outfile
        self.conf = conf
        self.linenum = 0
        self.otherfiles = []
        self.eqs = eqs
        self.eqdir = eqdir
        self.eqdpi = eqdpi
        # Default to supporting equations until we know otherwise.
        self.eqsupport = True
        self.eqcache = True
        self.eqpackages = []
        self.texlines = []
        self.analytics = None
        self.eqbd = {}  # equation base depth.
        self.baseline = None

    def pushfile(self, newfile):
        self.otherfiles.insert(0, self.inf)
        self.inf = open(newfile, 'r', encoding='utf-8')

    def nextfile(self):
        self.inf.close()
        self.inf = self.otherfiles.pop(0)

def showhelp():
    a = """Usage: jemdoc [OPTIONS] [SOURCEFILE] 
  Produces html markup from a jemdoc SOURCEFILE.

  Most of the time you can use jemdoc without any additional flags.
  For example, typing

    jemdoc index

  will produce an index.html from index.jemdoc, using a default
  configuration.

  Some configuration options can be overridden by specifying a
  configuration file.  You can use

    jemdoc --show-config

  to print a sample configuration file (which includes all of the
  default options). Any or all of the configuration [blocks] can be
  overwritten by including them in a configuration file, and running,
  for example,

    jemdoc -c mywebsite.conf index.jemdoc 

  You can view version and installation details with

    jemdoc --version

  See http://jemdoc.jaboc.net/ for many more details."""
    b = ''
    for l in a.splitlines(True):
        if l.startswith(' ' * 4):
            b += l[4:]
        else:
            b += l
    print(b)

def standardconf():
    a = """[firstbit]
  <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
  <head>
  <meta name="generator" content="jemdoc, see http://jemdoc.jaboc.net/" />
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
  
  [defaultcss]
  <link rel="stylesheet" href="jemdoc.css" type="text/css" />
  <link rel="shortcut icon" type="image/x-icon" href="favicon.ico" />
  
  [windowtitle]
  # used in header for window title.
  <title>|</title>

  [fwtitlestart]
  <div id="fwtitle">

  [fwtitleend]
  </div>
  
  [doctitle]
  # used at top of document.
  <div id="toptitle">
  <h1>|</h1>
  
  [subtitle]
  <div id="subtitle">|</div>
  
  [doctitleend]
  </div>
  
  [bodystart]
  </head>
  <body>
  
  [analytics]
  <script type="text/javascript">
  var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
  document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
  </script>
  <script type="text/javascript">
  try {
      var pageTracker = _gat._getTracker("|");
      pageTracker._trackPageview();
  } catch(err) {}</script>
  
  [menustart]
  <table summary="Table for page layout." id="tlayout">
  <tr valign="top">
  <td id="layout-menu">
  
  [menuend]
  </td>
  <td id="layout-content">
  
  [menucategory]
  <div class="menu-category">|</div>

  [menuitem]
  <div class="menu-item"><a href="|1">|2</a></div>

  [specificcss]
  <link rel="stylesheet" href="|" type="text/css" />

  [specificjs]
  <script src="|.js" type="text/javascript"></script>
  
  [currentmenuitem]
  <div class="menu-item"><a href="|1" class="current">|2</a></div>
  
  [nomenu]
  <div id="layout-content">
  
  [menulastbit]
  </td>
  </tr>
  </table>
  
  [nomenulastbit]
  </div>
  
  [bodyend]
  </body>
  </html>
  
  [infoblock]
  <div class="infoblock">
  
  [codeblock]
  <div class="codeblock">
  
  [blocktitle]
  <div class="blocktitle">|</div>
  
  [infoblockcontent]
  <div class="blockcontent">
  
  [codeblockcontent]
  <div class="blockcontent"><pre>
  
  [codeblockend]
  </pre></div></div>
  
  [codeblockcontenttt]
  <div class="blockcontent"><tt class="tthl">
  
  [codeblockendtt]
  </tt></div></div>
  
  [infoblockend]
  </div></div>
  
  [footerstart]
  <div id="footer">
  <div id="footer-text">
  
  [footerend]
  </div>
  </div>
  
  [lastupdated]
  Page generated |, by <a href="http://jemdoc.jaboc.net/">jemdoc</a>.

  [sourcelink]
  (<a href="|">source</a>)

  """
    b = ''
    for l in a.splitlines(True):
        if l.startswith('  '):
            b += l[2:]
        else:
            b += l
    return b

class JandalError(Exception):
    pass

class NoEqSupport(Exception):
    pass

def raisejandal(msg, line=0):
    if line == 0:
        s = "%s" % msg
    else:
        s = "line %d: %s" % (line, msg)
    raise JandalError(s)

def readnoncomment(f):
    l = f.readline()
    if l == '':
        return l
    elif l[0] == '#':
        return readnoncomment(f)
    else:
        return l.rstrip() + '\n'

def parseconf(cns):
    syntax = {}
    fs = [io.StringIO(standardconf())]
    for sname in cns:
        fs.append(open(sname, 'r', encoding='utf-8'))
    for f in fs:
        while pc(controlstruct(f)) != '':
            l = readnoncomment(f)
            r = re.match(r'\[(.*)\]\n', l)
            if r:
                tag = r.group(1)
                s = ''
                l = readnoncomment(f)
                while l not in ('\n', ''):
                    s += l
                    l = readnoncomment(f)
                syntax[tag] = s
        f.close()
    return syntax

def insertmenuitems(f, mname, current, prefix):
    m = open(mname, 'r', encoding='utf-8')
    while pc(controlstruct(m)) != '':
        l = readnoncomment(m)
        l = l.strip()
        if l == '':
            continue
        r = re.match(r'\s*(.*?)\s*\[(.*)\]', l)
        if r:
            link = r.group(2)
            if '://' not in r.group(2):
                link = prefix + allreplace(link)
            in_quote = False
            menuitem = ""
            for group in re.split(r'({{|}})', r.group(1)):
                if in_quote:
                    if group == '}}':
                        in_quote = False
                        continue
                    else:
                        menuitem += group
                else:
                    if group == '{{':
                        in_quote = True
                        continue
                    else:
                        menuitem += br(re.sub(r'(?<!\\n) +', '~', group), f)
            if link[-len(current):] == current:
                hb(f.outf, f.conf['currentmenuitem'], link, menuitem)
            else:
                hb(f.outf, f.conf['menuitem'], link, menuitem)
        else:
            hb(f.outf, f.conf['menucategory'], br(l, f))
    m.close()

def out(f, s):
    f.write(s)

def hb(f, tag, content1, content2=None):
    if content1 is None:
        content1 = ""
    if content2 is None:
        out(f, re.sub(r'\|', content1, tag))
    else:
        r = re.sub(r'\|1', content1, tag)
        r = re.sub(r'\|2', content2, r)
        out(f, r)

def pc(f, ditchcomments=True):
    """Peeks at next character in the file."""
    pos = f.inf.tell()
    c = f.inf.read(1)
    if c:
        if ditchcomments and c == '#':
            l = nl(f)
            if doincludes(f, l):
                return "#"
        if c in ' \t':
            return pc(f)
        if c == '\\':
            c += pc(f)
        f.inf.seek(pos, os.SEEK_SET)
    elif f.otherfiles:
        f.nextfile()
        return pc(f, ditchcomments)
    return c

def doincludes(f, l):
    ir = 'includeraw{'
    i = 'include{'
    if l.startswith(ir):
        path = l[len(ir):-2]
        if f.outf is not None:
            with open(path, 'r', encoding='utf-8') as nf:
                f.outf.write(nf.read())
    elif l.startswith(i):
        f.pushfile(l[len(i):-2])
    else:
        return False
    return True

def nl(f, withcount=False, codemode=False):
    s = f.inf.readline()
    if not s and f.otherfiles:
        f.nextfile()
        return nl(f, withcount, codemode)
    f.linenum += 1
    if not codemode:
        s = s.lstrip(' \t')
        s = re.sub(r'\s*(?<!\\)#.*', '', s)
    if withcount:
        if s[0] == '.':
            m = r'\.'
        else:
            m = s[0]
        r_ = re.match('(%s+) ' % m, s)
        if not r_:
            raise SyntaxError("couldn't handle the jandal (code 12039) on line %d" % f.linenum)
        if not codemode:
            s = s.lstrip('-.=:')
        return (s, len(r_.group(1)))
    else:
        if not codemode:
            s = s.lstrip('-.=:')
        return s

def np(f, withcount=False, eatblanks=True):
    if withcount:
        (s, c) = nl(f, withcount)
    else:
        s = nl(f)
    while pc(f) not in ('\n', '-', '.', ':', '', '=', '~', '{', '\\(', '\\)'):
        s += nl(f)
    while eatblanks and pc(f) == '\n':
        nl(f)
    if withcount:
        return (s[:-1], c)
    else:
        return s[:-1]

def quote(s):
    return re.sub(r"""[\\*/+"'<>&$%\.~[\]-]""", r'\\\g<0>', s)

def replacequoted(b):
    r_ = re.compile(r'\{\{(.*?)\}\}', re.M + re.S)
    m = r_.search(b)
    while m:
        qb = quote(m.group(1))
        b = b[:m.start()] + qb + b[m.end():]
        m = r_.search(b, m.start())
    return b

def replacepercents(b):
    r_ = re.compile(r'(?<!\\)%(.*?)(?<!\\)%', re.M + re.S)
    m = r_.search(b)
    while m:
        a = re.sub(r'\[', r'BSNOTLINKLEFT12039XX', m.group(1))
        a = re.sub(r'\]', r'BSNOTLINKRIGHT12039XX', a)
        qb = '+{{' + a + '}}+'
        b = b[:m.start()] + qb + b[m.end():]
        m = r_.search(b, m.start())
    return b

def replaceequations(b, f):
    rs = ((re.compile(r'(?<!\\)\$(.*?)(?<!\\)\$', re.M + re.S), False),
          (re.compile(r'(?<!\\)\\\((.*?)(?<!\\)\\\)', re.M + re.S), True))
    for (r_, wl) in rs:
        m = r_.search(b)
        while m:
            eq = m.group(1)
            if wl:
                fn = str(abs(hash(eq + 'wl120930alsdk')))
            else:
                fn = str(abs(hash(eq)))
            if f.baseline is None:
                if not os.path.isdir(f.eqdir):
                    os.mkdir(f.eqdir)
                (supported, message) = testeqsupport()
                if not supported:
                    print('WARNING: equation support disabled.')
                    print(message)
                    f.eqsupport = False
                    return b
                eqt = "0123456789xxxXXxX"
                (f.baseline, blfn) = geneq(f, eqt, dpi=f.eqdpi, wl=False,
                                           outname='baseline-' + str(f.eqdpi))
                if os.path.exists(blfn):
                    os.remove(blfn)
            fn = fn + '-' + str(f.eqdpi)
            (depth, fullfn) = geneq(f, eq, dpi=f.eqdpi, wl=wl, outname=fn)
            fullfn = fullfn.replace('\\', '/')
            offset = depth - f.baseline + 1
            eqtext = allreplace(eq)
            eqtext = eqtext.replace('\\', '')
            eqtext = eqtext.replace('\n', ' ')
            eqtext = eqtext.replace('{{', 'DOUBLEOPENBRACE')
            eqtext = eqtext.replace('}}', 'DOUBLECLOSEBRACE')
            if wl:
                b = b[:m.start()] + '{{\n<div class="eqwl"><img class="eqwl" src="%s" alt="%s" />\n<br /></div>}}' % (fullfn, eqtext) + b[m.end():]
            else:
                b = b[:m.start()] + '{{<img class="eq" src="%s" alt="%s" style="vertical-align: -%dpx" />}}' % (fullfn, eqtext, offset) + b[m.end():]
            m = r_.search(b, m.start())
    return replacequoted(b)

def replaceimages(b):
    r_ = re.compile(r'(?<!\\)\[img((?:\{.*?\}){,3})\s(.*?)(?:\s(.*?))?(?<!\\)\]',
                    re.M + re.S)
    m = r_.search(b)
    s_ = re.compile(r'\{(.*?)\}', re.M + re.S)
    while m:
        m1 = list(s_.findall(m.group(1)))
        m1 += [''] * (3 - len(m1))
        bits = []
        link = m.group(2).strip()
        bits.append(r'src="%s"' % quote(link))
        if m1[0]:
            s = (m1[0] + 'px') if m1[0].isdigit() else m1[0]
            bits.append(r'width="%s"' % quote(s))
        if m1[1]:
            s = (m1[1] + 'px') if m1[1].isdigit() else m1[1]
            bits.append(r'height="%s"' % quote(s))
        if m1[2]:
            bits.append(r'alt="%s"' % quote(m1[2]))
        else:
            bits.append(r'alt=""')
        b = b[:m.start()] + r'<img %s />' % " ".join(bits) + b[m.end():]
        m = r_.search(b, m.start())
    return b

def replacelinks(b):
    r_ = re.compile(r'(?<!\\)\[(.*?)(?:\s(.*?))?(?<!\\)\]', re.M + re.S)
    m = r_.search(b)
    while m:
        m1 = m.group(1).strip()
        if '@' in m1 and not m1.startswith('mailto:') and not m1.startswith('http://'):
            link = 'mailto:' + m1
        else:
            link = m1
        link = re.sub(r'\\#', '#', link)
        link = re.sub(r'(\+\{\{|\}\}\+)', r'%', link)
        link = quote(link)
        if m.group(2):
            linkname = m.group(2).strip()
        else:
            linkname = re.sub('^mailto:', '', link)
        b = b[:m.start()] + r'<a href=\"%s\">%s<\/a>' % (link, linkname) + b[m.end():]
        m = r_.search(b, m.start())
    return b

def br(b, f, tableblock=False):
    r_ = re.compile(r"!\$(\w{2,})\$!", re.M + re.S)
    for m in r_.findall(b):
        repl = os.environ.get(m)
        if repl is None:
            b = re.sub("!\$%s\$!" % m, 'FAILED_MATCH_' + m, b)
        else:
            b = re.sub("!\$%s\$!" % m, repl, b)

    if f.eqs and f.eqsupport:
        b = replaceequations(b, f)

    b = re.sub(r'\\\\', 'jemLITerl33talBS', b)
    b = replacequoted(b)
    b = allreplace(b)
    b = b.lstrip('-. \t')
    b = replaceimages(b)
    b = replacepercents(b)
    b = replacelinks(b)
    b = re.sub(r'BSNOTLINKLEFT12039XX', r'[', b)
    b = re.sub(r'BSNOTLINKRIGHT12039XX', r']', b)
    b = replacequoted(b)

    r_ = re.compile(r'(?<!\\)/(.*?)(?<!\\)/', re.M + re.S)
    b = re.sub(r_, r'<i>\1</i>', b)

    r_ = re.compile(r'(?<!\\)\*(.*?)(?<!\\)\*', re.M + re.S)
    b = re.sub(r_, r'<b>\1</b>', b)

    r_ = re.compile(r'(?<!\\)\+(.*?)(?<!\\)\+', re.M + re.S)
    b = re.sub(r_, r'<tt>\1</tt>', b)

    r_ = re.compile(r'(?<!\\)"(.*?)(?<!\\)"', re.M + re.S)
    b = re.sub(r_, r'&ldquo;\1&rdquo;', b)

    r_ = re.compile(r"(?<!\\)`", re.M + re.S)
    b = re.sub(r_, r'&lsquo;', b)

    r_ = re.compile(r"(?<!\\)'(?![a-zA-Z])", re.M + re.S)
    b = re.sub(r_, r'&rsquo;', b)

    r_ = re.compile(r"(?<!\\)---", re.M + re.S)
    b = re.sub(r_, r'&#8201;&mdash;&#8201;', b)

    r_ = re.compile(r"(?<!\\)--", re.M + re.S)
    b = re.sub(r_, r'&ndash;', b)

    r_ = re.compile(r"(?<!\\)\.\.\.", re.M + re.S)
    b = re.sub(r_, r'&hellip;', b)

    r_ = re.compile(r"(?<!\\)~", re.M + re.S)
    b = re.sub(r_, r'&nbsp;', b)

    r_ = re.compile(r"(?<!\\)\\R", re.M + re.S)
    b = re.sub(r_, r'&reg;', b)

    r_ = re.compile(r"(?<!\\)\\C", re.M + re.S)
    b = re.sub(r_, r'&copy;', b)

    r_ = re.compile(r"(?<!\\)\\M", re.M + re.S)
    b = re.sub(r_, r'&middot;', b)

    r_ = re.compile(r"(?<!\\)\\n", re.M + re.S)
    b = re.sub(r_, r'<br />', b)

    r_ = re.compile(r"(?<!\\)\\p", re.M + re.S)
    b = re.sub(r_, r'</p><p>', b)

    if tableblock:
        r_ = re.compile(r"(?<!\\)\|\|", re.M + re.S)
        f.tablecol = 2
        bcopy = b
        b = ""
        r2 = re.compile(r"(?<!\\)\|", re.M + re.S)
        for l in bcopy.splitlines():
            f.tablerow += 1
            l = re.sub(r_, r'</td></tr>\n<tr class="r%d"><td class="c1">' % f.tablerow, l)
            l2 = ''
            col = 2
            r2s = r2.split(l)
            for x in r2s[:-1]:
                l2 += x + ('</td><td class="c%d">' % col)
                col += 1
            l2 += r2s[-1]
            b += l2

    b = re.sub(r'\\(?!\\)', '', b)
    b = re.sub('jemLITerl33talBS', r'\\', b)
    b = re.sub('DOUBLEOPENBRACE', '{{', b)
    b = re.sub('DOUBLECLOSEBRACE', '}}', b)
    return b

def allreplace(b):
    r_ = re.compile(r"(?<!\\)&", re.M + re.S)
    b = re.sub(r_, r'&amp;', b)
    r_ = re.compile(r"(?<!\\)>", re.M + re.S)
    b = re.sub(r_, r'&gt;', b)
    r_ = re.compile(r"(?<!\\)<", re.M + re.S)
    b = re.sub(r_, r'&lt;', b)
    return b

def pyint(f, l):
    l = l.rstrip()
    l = allreplace(l)
    r_ = re.compile(r'(#.*)')
    l = r_.sub(r'<span class = "comment">\1</span>', l)
    if l.startswith('&gt;&gt;&gt;'):
        hb(f, '<span class="pycommand">|</span>\n', l)
    else:
        out(f, l + '\n')

def putbsbs(l):
    for i in range(len(l)):
        l[i] = '\\b' + l[i] + '\\b'
    return l

def gethl(lang):
    d = {'strings': False}
    if lang in ('py', 'python'):
        d['statement'] = ['break', 'continue', 'del', 'except', 'exec',
                          'finally', 'pass', 'print', 'raise', 'return', 'try',
                          'with', 'global', 'assert', 'lambda', 'yield', 'def',
                          'class', 'for', 'while', 'if', 'elif', 'else',
                          'import', 'from', 'as', 'assert']
        d['builtin'] = ['True', 'False', 'set', 'open', 'frozenset',
                        'enumerate', 'object', 'hasattr', 'getattr', 'filter',
                        'eval', 'zip', 'vars', 'unicode', 'type', 'str',
                        'repr', 'round', 'range', 'and', 'in', 'is', 'not',
                        'or']
        d['special'] = ['cols', 'optvar', 'param', 'problem', 'norm2', 'norm1',
                        'value', 'minimize', 'maximize', 'rows', 'rand',
                        'randn', 'printval', 'matrix']
        d['error'] = ['\w*Error', ]
        d['commentuntilend'] = '#'
        d['strings'] = True
    elif lang in ['c', 'c++', 'cpp']:
        d['statement'] = ['if', 'else', 'printf', 'return', 'for']
        d['builtin'] = ['static', 'typedef', 'int', 'float', 'double', 'void',
                        'clock_t', 'struct', 'long', 'extern', 'char']
        d['operator'] = ['#include.*', '#define', '@pyval{', '}@', '@pyif{',
                         '@py{']
        d['error'] = ['\w*Error', ]
        d['commentuntilend'] = ['//', '/*', ' * ', '*/']
    elif lang in ('rb', 'ruby'):
        d['statement'] = putbsbs(['while', 'until', 'unless', 'if', 'elsif',
                                  'when', 'then', 'else', 'end', 'begin',
                                  'rescue', 'class', 'def'])
        d['operator'] = putbsbs(['and', 'not', 'or'])
        d['builtin'] = putbsbs(['true', 'false', 'require', 'warn'])
        d['special'] = putbsbs(['IO'])
        d['error'] = putbsbs(['\w*Error', ])
        d['commentuntilend'] = '#'
        d['strings'] = True
        if lang in ['c++', 'cpp']:
            d['builtin'] += ['bool', 'virtual']
            d['statement'] += ['new', 'delete']
            d['operator'] += ['&lt;&lt;', '&gt;&gt;']
            d['special'] = ['public', 'private', 'protected', 'template',
                            'ASSERT']
    elif lang == 'sh':
        d['statement'] = ['cd', 'ls', 'sudo', 'cat', 'alias', 'for', 'do',
                          'done', 'in', ]
        d['operator'] = ['&gt;', r'\\', r'\|', ';', '2&gt;', 'monolith&gt;',
                         'kiwi&gt;', 'ant&gt;', 'kakapo&gt;', 'client&gt;']
        d['builtin'] = putbsbs(['gem', 'gcc', 'python', 'curl', 'wget', 'ssh',
                                'latex', 'find', 'sed', 'gs', 'grep', 'tee',
                                'gzip', 'killall', 'echo', 'touch',
                                'ifconfig', 'git', '(?<!\.)tar(?!\.)'])
        d['commentuntilend'] = '#'
        d['strings'] = True
    elif lang == 'matlab':
        d['statement'] = putbsbs(['max', 'min', 'find', 'rand', 'cumsum', 'randn', 'help',
                                  'error', 'if', 'end', 'for'])
        d['operator'] = ['&gt;', 'ans =', '>>', '~', '\.\.\.']
        d['builtin'] = putbsbs(['csolve'])
        d['commentuntilend'] = '%'
        d['strings'] = True
    elif lang == 'commented':
        d['commentuntilend'] = '#'
    for x in ['statement', 'builtin', 'special', 'error']:
        if x in d:
            d[x] = putbsbs(d[x])
    return d

def language(f, l, hl):
    l = l.rstrip()
    l = allreplace(l)
    if hl['strings']:
        r_ = re.compile(r'(".*?")')
        l = r_.sub(r'<span CLCLclass="string">\1</span>', l)
        r_ = re.compile(r"('.*?')")
        l = r_.sub(r'<span CLCLclass="string">\1</span>', l)
    if 'statement' in hl:
        r_ = re.compile('(' + '|'.join(hl['statement']) + ')')
        l = r_.sub(r'<span class="statement">\1</span>', l)
    if 'operator' in hl:
        r_ = re.compile('(' + '|'.join(hl['operator']) + ')')
        l = r_.sub(r'<span class="operator">\1</span>', l)
    if 'builtin' in hl:
        r_ = re.compile('(' + '|'.join(hl['builtin']) + ')')
        l = r_.sub(r'<span class="builtin">\1</span>', l)
    if 'special' in hl:
        r_ = re.compile('(' + '|'.join(hl['special']) + ')')
        l = r_.sub(r'<span class="special">\1</span>', l)
    if 'error' in hl:
        r_ = re.compile('(' + '|'.join(hl['error']) + ')')
        l = r_.sub(r'<span class="error">\1</span>', l)
    l = re.sub('CLCLclass', 'class', l)
    if 'commentuntilend' in hl:
        cue = hl['commentuntilend']
        if isinstance(cue, (list, tuple)):
            for x in cue:
                if l.strip().startswith(x):
                    hb(f, '<span class="comment">|</span>\n', allreplace(l))
                    return
            if '//' in cue:
                r_ = re.compile(r'\/\/.*')
                l = r_.sub(r'<span class="comment">\g<0></span>', l)
        elif cue == '#':
            r_ = re.compile(r'#.*')
            l = r_.sub(r'<span class="comment">\g<0></span>', l)
        elif cue == '%':
            r_ = re.compile(r'%.*')
            l = r_.sub(r'<span class="comment">\g<0></span>', l)
        elif l.strip().startswith(cue):
            hb(f, '<span class="comment">|</span>\n', allreplace(l))
            return
    out(f, l + '\n')

def geneq(f, eq, dpi, wl, outname):
    eqname = os.path.join(f.eqdir, outname + '.png')
    eqdepths = {}
    if f.eqcache:
        try:
            dc = open(os.path.join(f.eqdir, '.eqdepthcache'), 'r', encoding='utf-8')
            for l in dc:
                a = l.split()
                if len(a) >= 2:
                    eqdepths[a[0]] = int(a[1])
            dc.close()
            if os.path.exists(eqname) and eqname in eqdepths:
                return (eqdepths[eqname], eqname)
        except IOError:
            print('eqdepthcache read failed.')

    tempdir = tempfile.gettempdir()
    fd, texfile = tempfile.mkstemp('.tex', '', tempdir, True)
    basefile = texfile[:-4]
    g = os.fdopen(fd, 'w', encoding='utf-8')

    preamble = '\\documentclass{article}\n'
    for p in f.eqpackages:
        preamble += '\\usepackage{%s}\n' % p
    for p in f.texlines:
        preamble += re.sub(r'\\(?=[{}])', '', p + '\n')
    preamble += '\\pagestyle{empty}\n\\begin{document}\n'
    g.write(preamble)

    if wl:
        g.write('\\[%s\\]' % eq)
    else:
        g.write('$%s$' % eq)

    g.write('\n\\newpage\n\\end{document}')
    g.close()

    exts = ['.tex', '.aux', '.dvi', '.log']
    try:
        latexcmd = 'latex -file-line-error-style -interaction=nonstopmode -output-directory %s %s' % (tempdir, texfile)
        p = subprocess.run(latexcmd, shell=True, capture_output=True, text=True)
        if p.returncode != 0:
            for l in p.stdout.splitlines():
                print('  ' + l.rstrip())
            exts.remove('.tex')
            raise Exception('latex error')
        dvifile = basefile + '.dvi'
        dvicmd = 'dvipng --freetype0 -Q 9 -z 3 --depth -q -T tight -D %i -bg Transparent -o %s %s' % (dpi, eqname, dvifile)
        p = subprocess.run(dvicmd, shell=True, capture_output=True, text=True)
        if p.returncode != 0:
            if p.stderr:
                print(p.stderr)
            raise Exception('dvipng error')
        last = p.stdout.splitlines()[-1] if p.stdout.splitlines() else ''
        try:
            depth = int(last.split('=')[-1])
        except Exception:
            depth = 0
    finally:
        for ext in exts:
            g_ = basefile + ext
            if os.path.exists(g_):
                try:
                    os.remove(g_)
                except Exception:
                    pass

    if f.eqcache and eqname not in eqdepths:
        try:
            dc = open(os.path.join(f.eqdir, '.eqdepthcache'), 'a', encoding='utf-8')
            dc.write(eqname + ' ' + str(depth) + '\n')
            dc.close()
        except IOError:
            print('eqdepthcache update failed.')
    return (depth, eqname)

def dashlist(f, ordered=False):
    level = 0
    if ordered:
        char = '.'
        ul = 'ol'
    else:
        char = '-'
        ul = 'ul'
    while pc(f) == char:
        (s, newlevel) = np(f, True, False)
        if newlevel > level:
            for i in range(newlevel - level):
                if newlevel > 1:
                    out(f.outf, '\n')
                out(f.outf, '<%s>\n<li>' % ul)
        elif newlevel < level:
            out(f.outf, '\n</li>')
            for i in range(level - newlevel):
                out(f.outf, '</%s>\n</li>' % ul)
            out(f.outf, '\n<li>')
        else:
            out(f.outf, '\n</li>\n<li>')
        out(f.outf, '<p>' + br(s, f) + '</p>')
        level = newlevel
    for i in range(level):
        out(f.outf, '\n</li>\n</%s>\n' % ul)

def colonlist(f):
    out(f.outf, '<dl>\n')
    while pc(f) == ':':
        s = np(f, eatblanks=False)
        r_ = re.compile(r'\s*{(.*?)(?<!\\)}(.*)', re.M + re.S)
        g = re.match(r_, s)
        if not g or len(g.groups()) != 2:
            raise SyntaxError("couldn't handle the jandal (invalid deflist format) on line %d" % f.linenum)
        defpart = g.group(1)
        rest = g.group(2)
        hb(f.outf, '<dt>|</dt>\n', br(defpart, f))
        hb(f.outf, '<dd><p>|</p></dd>\n', br(rest, f))
    out(f.outf, '</dl>\n')

def codeblock(f, g):
    if g[1] == 'raw':
        raw = True
        ext_prog = None
    elif g[0] == 'filter_through':
        raw = False
        ext_prog = g[1]
        buff = ""
    else:
        ext_prog = None
        raw = False
        out(f.outf, f.conf['codeblock'])
        if g[0]:
            hb(f.outf, f.conf['blocktitle'], g[0])
        if g[1] == 'jemdoc':
            out(f.outf, f.conf['codeblockcontenttt'])
        else:
            out(f.outf, f.conf['codeblockcontent'])
    stringmode = False
    while 1:
        l = nl(f, codemode=True)
        if not l:
            break
        elif l.startswith('~'):
            break
        elif l.startswith('\\~'):
            l = l[1:]
        elif l.startswith('\\{'):
            l = l[1:]
        elif ext_prog:
            buff += l
            continue
        elif stringmode:
            if l.rstrip().endswith('"""'):
                out(f.outf, l + '</span>')
                stringmode = False
            else:
                out(f.outf, l)
            continue
        if g[1] == 'pyint':
            pyint(f.outf, l)
        else:
            if raw:
                out(f.outf, l)
            elif g[1] == 'jemdoc':
                for x in ('#', '~', '>>>', '\\~', '{'):
                    if str(l).lstrip().startswith(x):
                        out(f.outf, '</tt><pre class="tthl">')
                        out(f.outf, l + '</pre><tt class="tthl">')
                        break
                else:
                    for x in (':', '.', '-'):
                        if str(l).lstrip().startswith(x):
                            out(f.outf, '<br />' + prependnbsps(l))
                            break
                    else:
                        if str(l).lstrip().startswith('='):
                            out(f.outf, prependnbsps(l) + '<br />')
                        else:
                            out(f.outf, l)
            else:
                if l.startswith('\\#include{') or l.startswith('\\#includeraw{'):
                    out(f.outf, l[1:])
                elif l.startswith('#') and doincludes(f, l[1:]):
                    continue
                elif g[1] in ('python', 'py') and l.strip().startswith('"""'):
                    out(f.outf, '<span class="string">' + l)
                    stringmode = True
                else:
                    language(f.outf, l, gethl(g[1]))
    if raw:
        return
    elif ext_prog:
        print('filtering through %s...' % ext_prog)
        p = subprocess.run(ext_prog, shell=True, input=buff, capture_output=True, text=True)
        out(f.outf, p.stdout)
    else:
        if g[1] == 'jemdoc':
            out(f.outf, f.conf['codeblockendtt'])
        else:
            out(f.outf, f.conf['codeblockend'])

def prependnbsps(l):
    g = re.search('(^ *)(.*)', l).groups()
    return g[0].replace(' ', '&nbsp;') + g[1]

def inserttitle(f, t):
    if t is not None:
        hb(f.outf, f.conf['doctitle'], t)
        if pc(f) != '\n':
            hb(f.outf, f.conf['subtitle'], br(np(f), f))
        hb(f.outf, f.conf['doctitleend'], t)

def procfile(f):
    f.linenum = 0
    menu = None
    showfooter = True
    showsourcelink = False
    showlastupdated = True
    showlastupdatedtime = True
    nodefaultcss = False
    fwtitle = False
    css = []
    js = []
    title = None
    while pc(f, False) == '#':
        l = f.inf.readline()
        f.linenum += 1
        if doincludes(f, l[1:]):
            continue
        if l.startswith('# jemdoc:'):
            l = l[len('# jemdoc:'):]
            a = l.split(',')
            for b in a:
                b = b.strip()
                if b.startswith('menu'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    g = re.findall(r_, b)
                    if len(g) > 3 or len(g) < 2:
                        raise SyntaxError('sidemenu error on line %d' % f.linenum)
                    if len(g) == 2:
                        menu = (f, g[0], g[1], '')
                    else:
                        menu = (f, g[0], g[1], g[2])
                elif b.startswith('nofooter'):
                    showfooter = False
                elif b.startswith('nodate'):
                    showlastupdated = False
                elif b.startswith('notime'):
                    showlastupdatedtime = False
                elif b.startswith('fwtitle'):
                    fwtitle = True
                elif b.startswith('showsource'):
                    showsourcelink = True
                elif b.startswith('nodefaultcss'):
                    nodefaultcss = True
                elif b.startswith('addcss'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    css += re.findall(r_, b)
                elif b.startswith('addjs'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    js += re.findall(r_, b)
                elif b.startswith('addpackage'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    f.eqpackages += re.findall(r_, b)
                elif b.startswith('addtex'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    f.texlines += re.findall(r_, b)
                elif b.startswith('analytics'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    f.analytics = re.findall(r_, b)[0]
                elif b.startswith('title'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    g = re.findall(r_, b)
                    if len(g) != 1:
                        raise SyntaxError('addtitle error on line %d' % f.linenum)
                    title = g[0]
                elif b.startswith('noeqs'):
                    f.eqs = False
                elif b.startswith('noeqcache'):
                    f.eqcache = False
                elif b.startswith('eqsize'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    g = re.findall(r_, b)
                    if len(g) != 1:
                        raise SyntaxError('eqsize error on line %d' % f.linenum)
                    f.eqdpi = int(g[0])
                elif b.startswith('eqdir'):
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    g = re.findall(r_, b)
                    if len(g) != 1:
                        raise SyntaxError('eqdir error on line %d' % f.linenum)
                    f.eqdir = g[0]

    out(f.outf, f.conf['firstbit'])
    if not nodefaultcss:
        out(f.outf, f.conf['defaultcss'])
    for i in range(len(css)):
        if '.css' not in css[i]:
            css[i] += '.css'
    for x in css:
        hb(f.outf, f.conf['specificcss'], x)
    for x in js:
        hb(f.outf, f.conf['specificjs'], x)

    if pc(f) == '=':
        t = br(nl(f), f)[:-1]
        if title is None:
            title = re.sub(' *(<br />)|(&nbsp;) *', ' ', t)
    else:
        t = None

    hb(f.outf, f.conf['windowtitle'], title)
    out(f.outf, f.conf['bodystart'])

    if f.analytics:
        hb(f.outf, f.conf['analytics'], f.analytics)

    if fwtitle:
        out(f.outf, f.conf['fwtitlestart'])
        inserttitle(f, t)
        out(f.outf, f.conf['fwtitleend'])

    if menu:
        out(f.outf, f.conf['menustart'])
        insertmenuitems(*menu)
        out(f.outf, f.conf['menuend'])
    else:
        out(f.outf, f.conf['nomenu'])

    if not fwtitle:
        inserttitle(f, t)

    infoblock = False
    imgblock = False
    tableblock = False
    while 1:
        p = pc(f)
        if p == '':
            break
        elif p == '\\(':
            if not (f.eqs and f.eqsupport):
                break
            s = nl(f)
            if not s.strip().endswith('\\)'):
                while True:
                    l = nl(f, codemode=True)
                    if not l:
                        break
                    s += l
                    if l.strip() == '\\)':
                        break
            out(f.outf, br(s.strip(), f))
        elif p == '-':
            dashlist(f, False)
        elif p == '.':
            dashlist(f, True)
        elif p == ':':
            colonlist(f)
        elif p == '=':
            (s, c) = nl(f, True)
            s = s[:-1]
            hb(f.outf, '<h%d>|</h%d>\n' % (c, c), br(s, f))
        elif p == '#':
            _ = nl(f)
        elif p == '\n':
            nl(f)
        elif p == '~':
            nl(f)
            if infoblock:
                out(f.outf, f.conf['infoblockend'])
                infoblock = False
                nl(f)
                continue
            elif imgblock:
                out(f.outf, '</td></tr></table>\n')
                imgblock = False
                nl(f)
                continue
            elif tableblock:
                out(f.outf, '</td></tr></table>\n')
                tableblock = False
                nl(f)
                continue
            else:
                if pc(f) == '{':
                    l = allreplace(nl(f))
                    r_ = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
                    g = re.findall(r_, l)
                else:
                    g = []
                if len(g) >= 1:
                    g[0] = br(g[0], f)
                if len(g) in (0, 1):
                    out(f.outf, f.conf['infoblock'])
                    infoblock = True
                    if len(g) == 1:
                        hb(f.outf, f.conf['blocktitle'], g[0])
                    out(f.outf, f.conf['infoblockcontent'])
                elif len(g) >= 2 and g[1] == 'table':
                    name = ''
                    if len(g) >= 3 and g[2]:
                        name += ' id="%s"' % g[2]
                    out(f.outf, '<table%s>\n<tr class="r1"><td class="c1">' % name)
                    f.tablerow = 1
                    f.tablecol = 1
                    tableblock = True
                elif len(g) == 2:
                    codeblock(f, g)
                elif len(g) >= 4 and g[1] == 'img_left':
                    g += [''] * (7 - len(g))
                    if g[4].isdigit():
                        g[4] += 'px'
                    if g[5].isdigit():
                        g[5] += 'px'
                    out(f.outf, '<table class="imgtable"><tr><td>\n')
                    if g[6]:
                        out(f.outf, '<a href="%s">' % g[6])
                    out(f.outf, '<img src="%s"' % g[2])
                    out(f.outf, ' alt="%s"' % g[3])
                    if g[4]:
                        out(f.outf, ' width="%s"' % g[4])
                    if g[5]:
                        out(f.outf, ' height="%s"' % g[5])
                    out(f.outf, ' />')
                    if g[6]:
                        out(f.outf, '</a>')
                    out(f.outf, '&nbsp;</td>\n<td align="left">')
                    imgblock = True
                else:
                    raise JandalError("couldn't handle block", f.linenum)
        else:
            s = br(np(f), f, tableblock)
            if s:
                if tableblock:
                    hb(f.outf, '|\n', s)
                else:
                    hb(f.outf, '<p>|</p>\n', s)

    if showfooter and (showlastupdated or showsourcelink):
        out(f.outf, f.conf['footerstart'])
        if showlastupdated:
            ts = '%Y-%m-%d %H:%M:%S %Z' if showlastupdatedtime else '%Y-%m-%d'
            s = time.strftime(ts, time.localtime(time.time()))
            hb(f.outf, f.conf['lastupdated'], s)
        if showsourcelink:
            hb(f.outf, f.conf['sourcelink'], f.inname)
        out(f.outf, f.conf['footerend'])

    if menu:
        out(f.outf, f.conf['menulastbit'])
    else:
        out(f.outf, f.conf['nomenulastbit'])
    out(f.outf, f.conf['bodyend'])
    if f.outf is not sys.stdout:
        f.outf.close()

def main():
    if len(sys.argv) == 1 or sys.argv[1] in ('--help', '-h'):
        showhelp()
        raise SystemExit
    if sys.argv[1] == '--show-config':
        print(standardconf())
        raise SystemExit
    if sys.argv[1] == '--version':
        info()
        raise SystemExit

    outoverride = False
    confoverride = False
    outname = None
    confnames = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-o':
            if outoverride:
                raise RuntimeError("only one output file / directory, please")
            outname = sys.argv[i + 1]
            outoverride = True
            i += 2
            continue
        elif sys.argv[i] == '-c':
            confnames.append(sys.argv[i + 1])
            confoverride = True
            i += 2
            continue
        elif sys.argv[i].startswith('-'):
            raise RuntimeError('unrecognised argument %s, try --help' % sys.argv[i])
        else:
            break

    conf = parseconf(confnames)

    innames = []
    for j in range(i, len(sys.argv)):
        inname = sys.argv[j]
        if not os.path.isfile(inname) and '.' not in inname:
            inname += '.jemdoc'
        innames.append(inname)

    if outname is not None and not os.path.isdir(outname) and len(innames) > 1:
        raise RuntimeError('cannot handle one outfile with multiple infiles')

    for inname in innames:
        if outname is None:
            thisout = re.sub(r'.jemdoc$', '', inname) + '.html'
        elif os.path.isdir(outname):
            thisout = os.path.join(outname, re.sub(r'.jemdoc$', '', os.path.basename(inname)) + '.html')
        else:
            thisout = outname

        infile = open(inname, 'r', encoding='utf-8', newline='')
        outfile = open(thisout, 'w', encoding='utf-8', newline='')
        f = controlstruct(infile, outfile, conf, inname)
        procfile(f)

if __name__ == '__main__':
    main()
