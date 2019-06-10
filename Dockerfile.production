FROM python:3.7-slim
LABEL maintainer="dev@userland.tech"

RUN pip install pipenv=="2018.11.26"

ARG APP_NAME
ARG SOURCE_COMMIT
ENV APP_HOME /$APP_NAME
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

COPY Pipfile.lock $APP_HOME/Pipfile.lock
COPY Pipfile $APP_HOME/Pipfile
RUN pipenv install --system

ADD . $APP_HOME
RUN echo "$SOURCE_COMMIT" >> /$APP_NAME/SOURCE_COMMIT
EXPOSE 5000

ENV FLASK_APP "app:create_app('production')"

RUN echo '#!/usr/bin/env bash\n\
cd /holepunch\n\
exec gunicorn --ca-certs=/secrets/chain.pem --certfile=/secrets/cert.pem --keyfile=/secrets/key.pem -b :5000 --pythonpath /holepunch --access-logfile - --error-logfile - "app:create_app('\''production'\'')"'\
>> /${APP_HOME}/start.sh

RUN chmod +x ${APP_HOME}/start.sh
ENTRYPOINT "/${APP_HOME}/start.sh"

