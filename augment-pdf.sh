#~/bin/sh

qpdf --qdf $1 - | ./format_template.py ./data.yml | ./insert_links.py ./data.yml | fix-qdf > $2

