#!/bin/bash

# Override JDBC URL to use mysql service instead of localhost
export SPRING_DATASOURCE_URL="jdbc:mysql://mysql:3306/datahub?useSSL=false&serverTimezone=UTC"
export SPRING_DATASOURCE_USERNAME="datahub"
export SPRING_DATASOURCE_PASSWORD="datahub"
export SPRING_DATASOURCE_DRIVER_CLASS_NAME="org.mariadb.jdbc.Driver"

# Run the original start script
exec /datahub/datahub-gms/scripts/start.sh
