"""Maintainer-only validation and deterministic packaging for one text skill."""

import argparse
from dataclasses import dataclass
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile

from markdown_it import MarkdownIt
from markdown_it.common.utils import normalizeReference
import yaml


TEXT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json", ".csv", ".tsv", ".toml"}
MAX_FILES = 128
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * MAX_FILE_BYTES
MAX_ARCHIVE_BYTES = 16 * MAX_FILE_BYTES
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LOCAL_PATH = re.compile(
    r"(?i)(?<![\w])(?:[a-z]:[\\/]|\\\\[^\s\\]+\\|file://)"
    r"|(?:^|[\s`\"'(=])/(?!/)[\w.~-]+(?:/|\b)"
)
SECRET = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"|\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"
    r"|sk-(?:proj-)?[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16})\b"
    r"|(?i:\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|password)"
    r"\s*[:=]\s*[\"']?[A-Za-z0-9][A-Za-z0-9_./+=-]{7,})"
)


class SkillError(ValueError):
    """An invalid or unsafe package; messages never include credential values."""


@dataclass(frozen=True)
class SkillPackage:
    root_name: str
    files: tuple[tuple[str, bytes], ...]


class _HTMLReferences(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []

    def handle_starttag(self, tag, attrs):
        self.targets.extend(value for key, value in attrs if key in {"href", "src"} and value is not None)


class _UniqueLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise SkillError("frontmatter: duplicate or non-string YAML key")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _no_links(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    for part in (*reversed(path.parents), path):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise SkillError("link or reparse point refused")
    return path


def _portable_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise SkillError("unsafe package path")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(p in {".", ".."} for p in path.parts):
        raise SkillError("unsafe package path")
    for part in path.parts:
        if (re.search(r'[<>:"|?*\x00-\x1f]', part) or part.endswith((".", " "))
                or part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]}):
            raise SkillError("unsafe package path")
    return value


def _check_paths(names) -> None:
    paths = set()
    for name in names:
        folded = _portable_path(name).casefold()
        if folded in paths:
            raise SkillError("case-insensitive duplicate package path")
        paths.add(folded)
    if any(child.startswith(parent + "/") for parent in paths for child in paths):
        raise SkillError("file/directory package path conflict")


def _text(name: str, data: bytes) -> bytes:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise SkillError(f"{name}: invalid UTF-8") from error
    if "\x00" in text or text.startswith("\ufeff"):
        raise SkillError(f"{name}: binary content or UTF-8 BOM refused")
    if text.startswith("#!"):
        raise SkillError(f"{name}: executable content refused")
    if LOCAL_PATH.search(text):
        raise SkillError(f"{name}: local absolute path refused")
    if SECRET.search(text):
        raise SkillError(f"{name}: possible credential refused")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _frontmatter(root_name: str, data: bytes) -> None:
    lines = data.decode("utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise SkillError("SKILL.md: missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
        header = yaml.load("\n".join(lines[1:end]), Loader=_UniqueLoader)
    except (ValueError, yaml.YAMLError, RecursionError) as error:
        raise SkillError("SKILL.md: invalid YAML frontmatter") from error
    if not isinstance(header, dict):
        raise SkillError("SKILL.md: frontmatter must be a mapping")
    if header.get("name") != root_name or not NAME.fullmatch(root_name):
        raise SkillError("SKILL.md: name must match the skill directory")
    if not isinstance(header.get("description"), str) or not header["description"].strip():
        raise SkillError("SKILL.md: description is required")
    metadata = header.get("metadata")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("version"), str) or not metadata["version"].strip():
        raise SkillError("SKILL.md: metadata.version is required")


def _references(files: dict[str, bytes]) -> None:
    markdown = MarkdownIt("commonmark", {"inline_definitions": True})
    # Keep every parsed target visible to the package scheme whitelist.
    markdown.validateLink = lambda target: True
    for name, data in files.items():
        if PurePosixPath(name).suffix.lower() != ".md":
            continue
        environment = {}
        try:
            pending = markdown.parse(data.decode("utf-8"), environment)
        except ValueError as error:
            raise SkillError(f"{name}: invalid reference") from error
        targets = []
        while pending:
            token = pending.pop()
            if token.children:
                pending.extend(token.children)
                text = "".join(child.content if child.type == "text" else " " for child in token.children)
                for label, ref in re.findall(r"\[([^\]\n]+)\]\[([^\]\n]*)\]", text):
                    if normalizeReference(ref or label) not in environment.get("references", {}):
                        raise SkillError(f"{name}: undefined reference label")
            if token.type == "definition":
                targets.append(token.meta["url"])
            elif token.type in {"link_open", "image"}:
                targets.append(token.attrGet("href" if token.type == "link_open" else "src"))
            elif token.type in {"html_block", "html_inline"}:
                parser = _HTMLReferences()
                parser.feed(token.content)
                parser.close()
                targets.extend(parser.targets)
        for target in targets:
            target = target.strip()
            if not target:
                continue
            target = unquote(target)
            if LOCAL_PATH.search(target) or target.startswith(("/", "\\")):
                raise SkillError(f"{name}: reference escapes skill directory")
            try:
                parsed = urlsplit(target)
            except ValueError as error:
                raise SkillError(f"{name}: invalid reference") from error
            if parsed.scheme in {"https", "http", "mailto"}:
                continue
            if parsed.scheme or parsed.netloc:
                raise SkillError(f"{name}: unsupported reference scheme")
            if not parsed.path:
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), parsed.path.replace("\\", "/")))
            if resolved == ".." or resolved.startswith("../"):
                raise SkillError(f"{name}: reference escapes skill directory")
            if resolved not in files and not any(p.startswith(resolved.rstrip("/") + "/") for p in files):
                raise SkillError(f"{name}: missing reference")


def _checked_files(root_name: str, files: dict[str, bytes]) -> SkillPackage:
    if not NAME.fullmatch(root_name):
        raise SkillError("invalid skill directory name")
    if not files or len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_TOTAL_BYTES:
        raise SkillError("package file count or size limit exceeded")
    _check_paths(files)
    normalized = {}
    for name, data in sorted(files.items()):
        if PurePosixPath(name).suffix.lower() not in TEXT_EXTENSIONS:
            raise SkillError(f"{name}: non-text or executable file refused")
        if len(data) > MAX_FILE_BYTES:
            raise SkillError(f"{name}: file size limit exceeded")
        normalized[name] = _text(name, data)
    if "SKILL.md" not in normalized:
        raise SkillError("missing SKILL.md")
    _frontmatter(root_name, normalized["SKILL.md"])
    _references(normalized)
    return SkillPackage(root_name, tuple(normalized.items()))


def check_skill(skill_dir: Path) -> SkillPackage:
    """Read one link-free directory and return its validated, LF text bytes."""
    root = _no_links(Path(skill_dir))
    if not root.is_dir():
        raise SkillError("skill directory does not exist")
    files = {}
    pending = [root]
    total = 0
    while pending:
        directory = pending.pop()
        for entry in sorted(directory.iterdir()):
            _no_links(entry)
            info = entry.lstat()
            if stat.S_ISDIR(info.st_mode):
                pending.append(entry)
            elif stat.S_ISREG(info.st_mode):
                if os.name != "nt" and info.st_mode & 0o111:
                    raise SkillError("executable file refused")
                total += info.st_size
                if info.st_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or len(files) >= MAX_FILES:
                    raise SkillError("package file count or size limit exceeded")
                files[entry.relative_to(root).as_posix()] = entry.read_bytes()
            else:
                raise SkillError("non-regular file refused")
    return _checked_files(root.name, files)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest(package: SkillPackage, archive_name: str, archive_bytes: bytes) -> dict:
    return {
        "schema_version": 1,
        "root": package.root_name,
        "archive": {"name": archive_name, "sha256": _sha(archive_bytes)},
        "files": [
            {"path": f"{package.root_name}/{name}", "bytes": len(data), "sha256": _sha(data)}
            for name, data in package.files
        ],
    }


def build_package(skill_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    """Build and verify a stored ZIP plus an external SHA-256 manifest."""
    package = check_skill(skill_dir)
    output = _no_links(Path(output_dir))
    source = _no_links(Path(skill_dir))
    if output == source or source in output.parents:
        raise SkillError("output directory must be outside the source skill")
    output.mkdir(parents=True, exist_ok=True)
    _no_links(output)
    archive_name = package.root_name + ".zip"
    manifest_name = package.root_name + ".manifest.json"
    for filename in (archive_name, manifest_name):
        _no_links(output / filename)
    with tempfile.TemporaryDirectory(prefix=".skill-build-", dir=output) as temporary:
        archive = Path(temporary) / archive_name
        manifest = Path(temporary) / manifest_name
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as handle:
            for name, data in package.files:
                info = zipfile.ZipInfo(f"{package.root_name}/{name}", ZIP_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                handle.writestr(info, data)
        record = _manifest(package, archive_name, archive.read_bytes())
        manifest.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        if verify_package(archive, manifest) != package:
            raise SkillError("built archive does not match source bytes")
        archive.replace(output / archive_name)
        manifest.replace(output / manifest_name)
    return output / archive_name, output / manifest_name


def verify_package(archive_path: Path, manifest_path: Path) -> SkillPackage:
    """Validate ZIP metadata before reading bounded bytes. Never extract files."""
    archive = _no_links(Path(archive_path))
    manifest = _no_links(Path(manifest_path))
    if archive.stat().st_size > MAX_ARCHIVE_BYTES or manifest.stat().st_size > MAX_FILE_BYTES:
        raise SkillError("archive or manifest size limit exceeded")
    try:
        record = json.loads(manifest.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise SkillError("invalid manifest") from error
    if not isinstance(record, dict) or record.get("schema_version") != 1 or not isinstance(record.get("root"), str) or not NAME.fullmatch(record["root"]):
        raise SkillError("invalid manifest schema")
    root = record["root"]
    try:
        with zipfile.ZipFile(archive) as handle:
            members = handle.infolist()
            if not members or len(members) > MAX_FILES:
                raise SkillError("archive file count limit exceeded")
            _check_paths(info.filename for info in members)
            names = []
            total = 0
            for info in members:
                if info.orig_filename != info.filename:
                    raise SkillError("unsafe package path")
                name = info.filename
                if not name.startswith(root + "/"):
                    raise SkillError("archive path outside root")
                names.append(name)
                mode = info.external_attr >> 16
                if info.is_dir() or stat.S_IFMT(mode) not in {0, stat.S_IFREG} or mode & 0o111:
                    raise SkillError("archive link or non-regular entry refused")
                total += info.file_size
                if info.file_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                    raise SkillError("archive content size limit exceeded")
                if info.date_time != ZIP_TIME or info.compress_type != zipfile.ZIP_STORED or info.extra or info.comment or info.flag_bits & 1:
                    raise SkillError("archive metadata is not canonical")
            if names != sorted(names) or handle.comment:
                raise SkillError("archive order or comment is not canonical")
            entries = record.get("files")
            if not isinstance(entries, list) or len(entries) != len(names) or any(not isinstance(item, dict) for item in entries):
                raise SkillError("archive does not match manifest file list")
            if [item.get("path") for item in entries] != names:
                raise SkillError("archive does not match manifest file list")
            archive_record = record.get("archive")
            if not isinstance(archive_record, dict) or archive_record.get("name") != archive.name or archive_record.get("sha256") != _sha(archive.read_bytes()):
                raise SkillError("archive SHA-256 mismatch")
            files = {}
            for info, item in zip(members, entries):
                with handle.open(info) as member:
                    data = member.read(MAX_FILE_BYTES + 1)
                if len(data) > MAX_FILE_BYTES or len(data) != item.get("bytes") or _sha(data) != item.get("sha256"):
                    raise SkillError("archive file bytes or SHA-256 mismatch")
                files[info.filename[len(root) + 1:]] = data
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError) as error:
        raise SkillError("invalid or unsupported ZIP") from error
    package = _checked_files(root, files)
    if any(dict(package.files)[name] != data for name, data in files.items()):
        raise SkillError("archive text must use LF line endings")
    return package


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, default=Path(__file__).resolve().parents[1] / "gift-development-service")
    parser.add_argument("--build", action="store_true", help="also build and read back the ZIP and SHA-256 manifest")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "dist")
    parser.add_argument("--verify", type=Path, metavar="ZIP", help="verify an existing ZIP without extraction")
    parser.add_argument("--manifest", type=Path, help="external manifest for --verify")
    args = parser.parse_args(argv)
    try:
        if args.verify:
            if not args.manifest or args.build:
                parser.error("--verify requires --manifest and cannot be combined with --build")
            package = verify_package(args.verify, args.manifest)
        else:
            if args.manifest:
                parser.error("--manifest requires --verify")
            package = check_skill(args.skill)
            if args.build:
                archive, manifest = build_package(args.skill, args.output)
                print(f"Built and verified {archive.name} + {manifest.name}")
        print(f"OK: {package.root_name}, {len(package.files)} text files; client recognition and business behavior not tested")
        return 0
    except (SkillError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
