alias help := default

[private]
@default:
    just --list decisions

# @variable type
# @type string
# @description A string representing the singular name to use when outputting
# messages from the main _new recipe defined at the root `justfile`.

type := "decision record"

# @variable folder
# @type string
# @description A string representing the file path relative to the root of the
# repository which contains the .template.md and where the files are being
# created.

folder := "docs/decisions"

[doc('Create a new decision from the template found in docs/decisions/.template')]
@new title:
    just --justfile {{ justfile() }} _new "{{ title }}" "{{ type }}" "{{ folder }}"
