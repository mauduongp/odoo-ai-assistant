# Extends official Odoo with addon Python dependencies (Runbot / CI image).
ARG ODOO_VERSION=18.0
FROM odoo:${ODOO_VERSION}

USER root
COPY requirements.txt /tmp/requirements.txt
# Debian base ships some deps via apt without pip RECORD; avoid uninstall attempts.
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed -r /tmp/requirements.txt

USER odoo
