TODO
====

- Documentation.

- Remove lifecycle event notification on ``__setitem__`` in directory. Use
  ``node.behaviors.Lifecycle`` instead

- Suppress lifecycle events in ``_create_child_by_factory``.

- Remove ``Reference`` plumbing behavior from default ``File`` and
  ``Directory`` implementations.

- Rename ``DirectoryStorage.factories`` to ``DirectoryStorage.file_factories``.

- Use regular expressions for child factories if desired.

- Introduce flag on ``DirectoryStorage`` to turn off RAM caching of children.

- Introduce strict mode which prevents fallback ``File`` creation if file
  factory raises ``TypeError``.
