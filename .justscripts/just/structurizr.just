set working-directory := '../../docs'

[private]
@default:
    just -l structurizr

alias browser := lite
alias view := lite
alias start := lite

[doc('Sets up the Structurizr Lite instance locally on port 7267.')]
lite:
    docker run \
      -it \
      --rm \
      -p 7267:8080 \
      -v {{ absolute_path(".") }}:/usr/local/structurizr \
      structurizr/lite

[doc('Exports diagrams in dot format (GraphViz) into a `diagrams/` directory.')]
render-dot:
    docker run \
      -it \
      --rm \
      -v {{ absolute_path(".") }}:/usr/local/structurizr \
      structurizr/cli export \
      -workspace workspace.json \
      -format dot \
      -output diagrams

[doc('Exports diagrams in puml format (C4 PlantUML) into a `diagrams/` directory.')]
render-c4plantuml:
    docker run \
      -it \
      --rm \
      -v {{ absolute_path(".") }}:/usr/local/structurizr \
      structurizr/cli export \
      -workspace workspace.json \
      -format plantuml/c4plantuml \
      -output diagrams

[doc('Exports diagrams in mmd format (Mermaid) into a `diagrams/` directory. Useful for quickly including diagrams into GitHub-rendered Markdown.')]
render-mermaid:
    docker run \
      -it \
      --rm \
      -v {{ absolute_path(".") }}:/usr/local/structurizr \
      structurizr/cli export \
      -workspace workspace.json \
      -format mermaid \
      -output diagrams
