FROM python:3.7
LABEL maintainer="dev@userland.tech"

RUN pip install pipenv=="2018.11.26"
ARG APP_NAME
ENV APP_HOME /$APP_NAME
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

COPY Pipfile.lock $APP_HOME/Pipfile.lock
COPY Pipfile $APP_HOME/Pipfile
RUN pipenv install --system --dev

CMD bash

