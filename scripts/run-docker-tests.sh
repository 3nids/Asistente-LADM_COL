#!/usr/bin/env bash
#***************************************************************************
#                             -------------------
#       begin                : 2017-08-24
#       git sha              : :%H$
#       copyright            : (C) 2017 by OPENGIS.ch
#       email                : info@opengis.ch
#***************************************************************************
#
#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License as published by  *
#*   the Free Software Foundation; either version 2 of the License, or     *
#*   (at your option) any later version.                                   *
#*                                                                         *
#***************************************************************************

set -e
# rationale: Wait for postgres container to become available
nslookup postgres
ping -c 1 postgres
printf "Wait a moment while loading the database."
while ! PGPASSWORD='clave_ladm_col' psql -h postgres -U usuario_ladm_col -p 5432 -l &> /dev/null
do
  printf "."
  sleep 2
done
printf "\n"

pushd /usr/src
xvfb-run nose2-3
popd