# You could use `gitpod/workspace-full` as well.
FROM gitpod/workspace-python

RUN pyenv install 3.11 \
    && pyenv global 3.11

USER gitpod

## Playwright
RUN pip3 install playwright\
      && playwright install \
      && playwright install-deps

### Foundry
RUN curl -L https://foundry.paradigm.xyz | bash \
  && foundryup
