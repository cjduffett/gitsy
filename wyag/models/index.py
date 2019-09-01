"""Git index file."""

import datetime as dt


class IndexEntry:
    """An entry in the index file."""

    # The last time the file's metadata changed.
    meta_changed_at: dt.datetime

    # The last time the file's data changed.
    data_changed_at: dt.datetime

    # The ID of the device containing the file.
    dev: str

    # The file's inode number.
    inode_no: int

    # The object type, either b1000 (regular) or b1010 (symlink) b1110 (gitlink).
    mode_type: bytes

    # The object permissions.
    mode_perms: int

    # User ID of the owner.
    user_id: str

    # Group ID of the owner.
    group_id: str

    # Size of the object, in bytes.
    size: int

    # The object's hash, as a hex string.
    hash_: str

    flag_assume_valid: bool
    flag_extended: bool
    flag_stage: str

    # Length of the name if < 0xFFF, -1 otherwise.
    flag_name_length: int

    # The object's name.
    name: str
