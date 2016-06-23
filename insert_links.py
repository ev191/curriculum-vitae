#!/usr/bin/env python3

from itertools import count
import re
import sys
import yaml

# Command line parsing

if len(sys.argv) < 2:
  print('Usage: %s <config-yaml>' % sys.argv[0], file=sys.stderr)
  exit(1)

config_path = sys.argv[1]

# Load configuration file

config = None
with open(config_path, 'r') as stream:
  try:
    config = yaml.load(stream)
  except yaml.YAMLError as exc:
    print(exc)
    exit(1)

# Load PDF from STDIN

pdf_data = sys.stdin.buffer.read()

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

# Insert new hyperlink objs into pdf data

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

# Write new file to STDOUT

sys.stdout.buffer.write(pdf_data)
exit(0)

