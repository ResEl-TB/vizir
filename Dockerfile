FROM docker.resel.fr/resel/docker/alpine-resel
MAINTAINER Benjamin Somers <bsomers@resel.fr>

ARG PRIVATE_TOKEN

RUN apk add --no-cache openssh nodejs npm python3 py3-pip gcc python3-dev libc-dev
RUN npm install -g jsdoc
RUN pip3 install GitPython Jinja2 PyYAML Sphinx sphinx-js recommonmark sphinx_rtd_theme python-gitlab termcolor

RUN mkdir -p /srv/vizir/
COPY app /srv/vizir/

RUN chmod +x /srv/vizir/vizir
RUN mkdir -p ~/.ssh/
ADD git.priv /root/.ssh/git.priv
RUN chmod 0600 /root/.ssh/git.priv

RUN ssh-keyscan -p 43000 git.resel.fr >> ~/.ssh/known_hosts
RUN echo -e '\
host git.resel.fr\n\
    HostName git.resel.fr\n\
    IdentityFile /root/.ssh/git.priv\n\
    User git\n\
' >> ~/.ssh/config

RUN sed -i "s/\$PRIVATE_TOKEN/$PRIVATE_TOKEN/" /srv/vizir/vzr/constants.py

RUN git config --global user.email vizir@resel.fr
RUN git config --global user.name Vizir

ENV PATH="/srv/vizir:${PATH}"

ENTRYPOINT []
