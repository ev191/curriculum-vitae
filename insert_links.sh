#~/bin/sh

qpdf --qdf $1 - | ./insert_links.py ./links.yml | fix-qdf > $2

