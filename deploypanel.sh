#!/usr/bin/bash
rm -rf /var/www/html/*
cp -avr OPSEC-PANEL/* /var/www/html/
  rm /etc/apache2/sites-enabled/000-default.conf
  cp 000-default.conf /etc/apache2/sites-enabled/000-default.conf
  exit 0;
