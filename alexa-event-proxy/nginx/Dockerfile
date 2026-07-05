FROM nginx:1.25

# htpasswd tool + clean up apt cache
RUN apt-get update && apt-get install -y --no-install-recommends apache2-utils \
    && rm -rf /var/lib/apt/lists/*

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/nginx.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ensure nginx system user owns the relevant paths
RUN chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /etc/nginx/ \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid

# /tmp is always writable – htpasswd file will be written there at startup
USER nginx

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]