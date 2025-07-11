#!/usr/bin/sed -f
# Simple script to fix corrupted CIRED name
s/;C;N;R;S;/CNRS/g
s/;C;I;R;E;D;/CIRED/g
s/CIRED CIRED/CIRED/g
s/' /'/g
s/'CIRED'/CIRED/
s/'UMR CIRED'/CIRED/
s/'CNRS'/CNRS/
s/: CIRED/:CIRED/
s/\[.*CIRED.*\]/CIRED/
s/'École des Ponts ParisTech'/École des Ponts ParisTech/
s/'Ecole des Ponts ParisTech'/École des Ponts ParisTech/
s/'Université Paris-Saclay'/Université Paris-Saclay/
s/CIRED--/CIRED,/
s/CIRED (Centre International de Recherche sur l’Environnement et le Développement)/CIRED/
s/CNRS-- CIRED/CIRED, CNRS/
s/'AgroParisTech'/AgroParisTech/
s/AgroParisTech-- CIRED/CIRED, AgroParisTech/
s/: CIRAD/:CIRAD/
s/Cirad/CIRAD/
s/'CIRAD'/CIRAD/
s/CIRAD-ES-UMR CIRED/CIRED, CIRAD/
s/CIRAD-- CIRED/CIRED, CIRAD/
s/'INRAE'/INRAE/
s/'EHESS'/EHESS/
s/'Sciences Po'/Sciences Po/
s/"//g
s/ORG: /ORG:/g
s/-- /, /g
s/EMAIL: /EMAIL:/

