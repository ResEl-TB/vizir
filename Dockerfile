FROM docker.resel.fr/resel/docker/alpine-resel
MAINTAINER nicolas.vuillermet@imt-atlantique.net

RUN apk add --no-cache openssh nodejs npm

RUN npm install -g jsdoc

RUN echo "**** install Python ****" && \
    apk add --no-cache python3 && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    \
    echo "**** install pip ****" && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools wheel && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi

RUN pip3 install GitPython Jinja2 PyYAML Sphinx sphinx-js recommonmark sphinx_rtd_theme

RUN mkdir -p /srv/bin/

COPY vizir/bin /srv/bin/

RUN chmod +x /srv/bin/vizir

RUN mkdir -p ~/.ssh/

COPY PRIVATE_KEY /root/.ssh/git.priv

RUN ssh-keyscan -p 43000 git.resel.fr >> ~/.ssh/known_hosts && \
    echo "host git.resel.fr" > ~/.ssh/config && \
    echo "  HostName git.resel.fr" >> ~/.ssh/config && \
    echo "  IdentityFile /root/.ssh/git.priv" >> ~/.ssh/config && \
    echo "  User git" >>  ~/.ssh/config
    
RUN chmod 0600 ~/.ssh/git.priv

RUN git config --global user.email "vizir@resel.fr" && \
    git config --global user.name "Vizir Runner"

	
ENV PATH="/srv/bin:${PATH}"

ENTRYPOINT []
