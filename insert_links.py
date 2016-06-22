#!/usr/bin/env python3

from itertools import count
from subprocess import call, PIPE, Popen
import os
import re
import sys
import tempfile
import yaml

# Magic to support python both 2 and 3

try:
  range = xrange
except:
  pass

# Command line parsing

if len(sys.argv) < 3:
  print('Usage: %s <config-yaml> <inkscape-gen-pdf>'
    % sys.argv[0], file=sys.stderr)
  exit(1)

config_path = sys.argv[1]
pdf_in_path = sys.argv[2]
#pdf_out_path = sys.argv[3]

# Load configuration file

config = None
with open(config_path, 'r') as stream:
  try:
    config = yaml.load(stream)
  except yaml.YAMLError as exc:
    print(exc)
    exit(1)

# QDFy the input PDF & load the resulting PDF to memory

fd, qdf_tmppath = tempfile.mkstemp()
os.close(fd)
try:
  if call(['qpdf', '--qdf', pdf_in_path, qdf_tmppath]) != 0:
    print('error: qpdf failed', file=sys.stderr)
    exit(1)
  with open(qdf_tmppath, 'rb') as ps_file:
    pdf_data = ps_file.read()
finally:
  try:
    os.unlink(qdf_tmppath)
  except:
    pass

# Load the rects and last object ID from PDF file

last_obj = re.search(br'\bxref\s+(\d+)\s+(\d+)\b', pdf_data)
if not last_obj:
  print('error: could not find last obj id', file=sys.stderr)
  exit(1)
last_obj = tuple(map(int, last_obj.groups()))

# Generate the PDF hyperlink objects

pdf_link_tpl = '''
%%QDF: ignore_newline
%d %d obj
<<
/A << /S /URI /URI (%s) >>
/Border [ 0 0 0 ]
/Rect [ %f %f %f %f ]
/Subtype /Link
/Type /Annot
>>
endobj
'''.strip()

pdf_links = '\n'.join(pdf_link_tpl % (
  c, last_obj[0], l['url'], l['coords'][0], l['coords'][1],
  l['coords'][0] + l['coords'][2], l['coords'][1] + l['coords'][3]
) for c, l in zip(count(last_obj[1]), config['links']))

# Remove the visual rects from PDF, write out the new hyperlink objs

pdf_data = re.sub(
  (r'\bxref\s+%d\s+%d\b' % last_obj).encode('ascii'),
  (pdf_links + '\nxref\n%d %d' % (
    last_obj[0], last_obj[1] + len(pdf_links)
  )).encode('ascii'),
  pdf_data
)
pdf_data = re.sub(
  br'([%][%]\s+Page\s+1\s+[%][%][^\n]+\s+\d+\s+\d+\s+obj\s+<<)',
  (r'\1/Annots [%s] ' % ' '.join(
  '%d %d R' % (i + last_obj[1], last_obj[0])
  for i in range(len(pdf_links))
)).encode('ascii'), pdf_data)

# Write new file to stdandard output

sys.stdout.buffer.write(pdf_data)
exit(0)

