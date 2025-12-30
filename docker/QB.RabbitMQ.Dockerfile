ARG DOCKER_REGISTRY
ARG RABBITMQ_BASE_IMAGE

FROM $DOCKER_REGISTRY/$RABBITMQ_BASE_IMAGE

USER 0
COPY --chown=gpn:0 --chmod=0644 ./docker/certs /etc/pki/ca-trust/source/anchors

RUN groupadd --gid 10000 gpn && useradd --uid 10000 --gid 10000 --shell /bin/bash gpn && \
    mkdir -p /opt/rabbitmq/{certs,conf} && \
    chown -R gpn:0 /opt/rabbitmq/{certs,conf} && \
    chown -R gpn:0 /etc/rabbitmq && \
    mkdir -p /var/lib/rabbitmq/mnesia && \
    chown -R gpn:0 /var/{lib,log}/rabbitmq && \
    update-ca-trust

COPY --chown=gpn:0 --chmod=0755 ./docker/config/QB.RabbitMQ/* /opt/rabbitmq/conf/

COPY --chown=gpn:0 --chmod=0644 ./docker/ssl/certs/certificate.crt /opt/rabbitmq/certs
COPY --chown=gpn:0 --chmod=0600 ./docker/ssl/certs/private.key /opt/rabbitmq/certs

USER gpn

ENTRYPOINT ["/entrypoint.sh"]
CMD ["rabbitmq-server"]