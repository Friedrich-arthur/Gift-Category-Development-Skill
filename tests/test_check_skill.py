import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import warnings
import zipfile

from tools.check_skill import MAX_FILE_BYTES, SkillError, _checked_files, build_package, check_skill, main, verify_package


GOOD_SKILL = """---
name: gift-development-service
description: 帮助用户处理礼品需求。
metadata:
  version: "0.3.0"
---

# 礼品服务

[资料](examples/source.md)
"""


class SkillChecksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".test-skill-", dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "gift-development-service"
        (self.root / "examples").mkdir(parents=True)
        (self.root / "SKILL.md").write_text(GOOD_SKILL, encoding="utf-8")
        (self.root / "examples/source.md").write_text("资料内容。\n", encoding="utf-8")

    def test_missing_reference_is_rejected(self):
        (self.root / "examples/source.md").unlink()
        with self.assertRaisesRegex(SkillError, "missing reference"):
            check_skill(self.root)

    def replace_skill(self, old, new):
        file = self.root / "SKILL.md"
        file.write_text(GOOD_SKILL.replace(old, new), encoding="utf-8")

    def test_minimal_self_contained_package_is_valid(self):
        package = check_skill(self.root)
        self.assertEqual(package.root_name, "gift-development-service")
        self.assertEqual(dict(package.files), {
            "SKILL.md": GOOD_SKILL.encode("utf-8"),
            "examples/source.md": "资料内容。\n".encode("utf-8"),
        })

    def test_empty_markdown_destination_refers_to_current_page(self):
        self.replace_skill("[资料](examples/source.md)", "[返回当前页]( )")
        self.assertEqual(len(check_skill(self.root).files), 2)

    def test_missing_name_or_wrong_name_is_rejected(self):
        for name in ("", "name: another-skill\n"):
            with self.subTest(name=name):
                self.replace_skill("name: gift-development-service\n", name)
                with self.assertRaisesRegex(SkillError, "name must match"):
                    check_skill(self.root)

    def test_missing_or_wrong_frontmatter_fields_are_rejected(self):
        cases = [
            ("description: 帮助用户处理礼品需求。", "description: ''", "description"),
            ('version: "0.3.0"', "version: 0.3", "version"),
            ('version: "0.3.0"', "version: ''", "version"),
            ('metadata:\n  version: "0.3.0"', "metadata: []", "version"),
        ]
        for before, after, error in cases:
            with self.subTest(field=error):
                self.replace_skill(before, after)
                with self.assertRaisesRegex(SkillError, error):
                    check_skill(self.root)

    def test_malformed_and_duplicate_yaml_are_rejected(self):
        for before, after in [
            ("metadata:", "metadata: ["),
            ("description: 帮助用户处理礼品需求。", "description: one\ndescription: two"),
        ]:
            with self.subTest(after=after):
                self.replace_skill(before, after)
                with self.assertRaisesRegex(SkillError, "YAML"):
                    check_skill(self.root)

    def test_relative_reference_cannot_escape_even_when_target_exists(self):
        (self.root.parent / "outside.md").write_text("outside", encoding="utf-8")
        for target in ("../outside.md", "%2e%2e/outside.md", "examples/../../outside.md"):
            with self.subTest(target=target):
                self.replace_skill("examples/source.md", target)
                with self.assertRaisesRegex(SkillError, "escapes skill"):
                    check_skill(self.root)

    def test_relative_parent_within_skill_and_query_fragment_are_valid(self):
        (self.root / "examples/source.md").write_text(
            "[入口](../SKILL.md?view=short#礼品服务)\n", encoding="utf-8")
        self.assertEqual(len(check_skill(self.root).files), 2)

    def test_malformed_external_reference_has_a_validation_error(self):
        self.replace_skill("examples/source.md", "https://[invalid/path")
        with self.assertRaisesRegex(SkillError, "invalid reference"):
            check_skill(self.root)

    def test_nested_link_labels_still_check_the_destination(self):
        (self.root.parent / "outside.md").write_text("outside", encoding="utf-8")
        for target, error in [("absent.md", "missing reference"), ("../outside.md", "escapes skill")]:
            for prefix in ("", "!"):
                with self.subTest(target=target, prefix=prefix):
                    self.replace_skill("[资料](examples/source.md)", f"{prefix}[read [source]]({target})")
                    with self.assertRaisesRegex(SkillError, error):
                        check_skill(self.root)

    def test_parentheses_in_markdown_destinations_are_valid(self):
        (self.root / "guide(a).md").write_text("guide\n", encoding="utf-8")
        for link in ("[guide](guide(a).md)", "[guide][source]\n\n[source]: guide(a).md"):
            with self.subTest(link=link):
                self.replace_skill("[资料](examples/source.md)", link)
                self.assertEqual(len(check_skill(self.root).files), 3)

    def test_paths_with_spaces_survive_build_and_readback(self):
        (self.root / "examples/demo source.md").write_text("guide\n", encoding="utf-8")
        for link in ('<img src="examples/demo source.md">',
                     '[guide](<examples/demo source.md>)',
                     '<a href="examples/demo&#32;source.md">guide</a>'):
            with self.subTest(link=link):
                self.replace_skill("[资料](examples/source.md)", link)
                archive, manifest = build_package(self.root, self.root.parent / "dist")
                self.assertEqual(verify_package(archive, manifest), check_skill(self.root))

    def test_html_path_is_not_truncated_to_an_existing_prefix(self):
        self.replace_skill("[资料](examples/source.md)", '<img src="examples/source.md absent.md">')
        with self.assertRaisesRegex(SkillError, "missing reference"):
            check_skill(self.root)

    def test_parser_does_not_hide_unsupported_reference_schemes(self):
        for target in ("file:guide.md", "javascript:alert(1)", "data:text/plain,hello"):
            for link in (f"[read [source]]({target})", f"![image]({target})", f"[source]: {target}"):
                with self.subTest(link=link):
                    self.replace_skill("[资料](examples/source.md)", link)
                    with self.assertRaisesRegex(SkillError, "unsupported reference scheme"):
                        check_skill(self.root)

    def test_unused_and_duplicate_reference_definitions_are_checked(self):
        for link in ("[unused]: absent.md", "[source]: examples/source.md\n[source]: absent.md"):
            with self.subTest(link=link):
                self.replace_skill("[资料](examples/source.md)", link)
                with self.assertRaisesRegex(SkillError, "missing reference"):
                    check_skill(self.root)

    def test_code_examples_do_not_create_references(self):
        fake_links = '[guide](absent.md) [guide][undefined] <img src="absent.md"> <a href=javascript:alert(1)>run</a>'
        for code in (f"`{fake_links}`", f"```md\n{fake_links}\n[unused]: absent.md\n```", f"    {fake_links}\n"):
            with self.subTest(code=code):
                self.replace_skill("[资料](examples/source.md)", code)
                self.assertEqual(len(check_skill(self.root).files), 2)

    def test_unquoted_html_targets_are_rejected_by_source_check(self):
        for html, message in (
            ("<a href=../outside.md>outside</a>", "escapes skill"),
            ("<img src=absent.md>", "missing reference"),
            ("<a href=javascript:alert(1)>run</a>", "unsupported reference scheme"),
            ("<a HREF=java&#115;cript:alert(1)>run</a>", "unsupported reference scheme"),
        ):
            with self.subTest(html=html):
                self.replace_skill("[资料](examples/source.md)", html)
                with self.assertRaisesRegex(SkillError, message):
                    check_skill(self.root)

    def test_unquoted_html_targets_cannot_be_packaged(self):
        for html, message in (
            ("<a href=../outside.md>outside</a>", "escapes skill"),
            ("<img src=absent.md>", "missing reference"),
            ("<a href=javascript:alert(1)>run</a>", "unsupported reference scheme"),
        ):
            with self.subTest(html=html):
                self.replace_skill("[资料](examples/source.md)", html)
                output = self.root.parent / "dist"
                with self.assertRaisesRegex(SkillError, message):
                    build_package(self.root, output)
                self.assertFalse((output / "gift-development-service.zip").exists())
                self.assertFalse((output / "gift-development-service.manifest.json").exists())

    def test_zip_readback_rechecks_unquoted_html_with_matching_hashes(self):
        for html, message in (
            ("<a href=../outside.md>outside</a>", "escapes skill"),
            ("<img src=absent.md>", "missing reference"),
            ("<a href=javascript:alert(1)>run</a>", "unsupported reference scheme"),
        ):
            with self.subTest(html=html):
                archive, manifest = build_package(self.root, self.root.parent / "dist")
                with zipfile.ZipFile(archive) as handle:
                    members = [(info, handle.read(info)) for info in handle.infolist()]
                data = GOOD_SKILL.replace("[资料](examples/source.md)", html).encode("utf-8")
                with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as handle:
                    for info, original in members:
                        handle.writestr(info, data if info.filename.endswith("/SKILL.md") else original)
                record = json.loads(manifest.read_text(encoding="utf-8"))
                record["archive"]["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
                for entry in record["files"]:
                    if entry["path"].endswith("/SKILL.md"):
                        entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                manifest.write_text(json.dumps(record), encoding="utf-8")
                with self.assertRaisesRegex(SkillError, message):
                    verify_package(archive, manifest)

    def test_valid_unquoted_html_survives_build_and_readback(self):
        for html in (
            "<a href=examples/source.md>source</a>",
            "<img src=examples/source.md />",
            "<a HREF=https://example.invalid/help?x=1&amp;y=2>help</a>",
            "<a href=#section>section</a>",
        ):
            with self.subTest(html=html):
                self.replace_skill("[资料](examples/source.md)", html)
                package = check_skill(self.root)
                archive, manifest = build_package(self.root, self.root.parent / "dist")
                self.assertEqual(verify_package(archive, manifest), package)

    def test_html_comments_do_not_create_references(self):
        self.replace_skill("[资料](examples/source.md)", '<!-- <img src="absent.md"> <a href=../outside.md> -->')
        archive, manifest = build_package(self.root, self.root.parent / "dist")
        self.assertEqual(verify_package(archive, manifest), check_skill(self.root))

    def test_reference_definitions_and_html_targets_are_checked(self):
        for link in ("[资料][source]\n[source]: absent.md", '<img src="absent.md">', "[资料][undefined]", "[*资料*][undefined]"):
            with self.subTest(link=link):
                (self.root / "examples/source.md").write_text(link, encoding="utf-8")
                with self.assertRaisesRegex(SkillError, "reference"):
                    check_skill(self.root)

    def test_absolute_paths_are_rejected_without_echoing_them(self):
        for path in ("C:/Users/private/data.md", r"C:\Users\private\data.md", r"\\server\share\data.md", "/home/private/data.md", "file:///private/data.md"):
            with self.subTest(path=path):
                (self.root / "examples/source.md").write_text(path, encoding="utf-8")
                with self.assertRaisesRegex(SkillError, "absolute path") as result:
                    check_skill(self.root)
                self.assertNotIn(path, str(result.exception))

    def test_external_http_reference_and_portable_install_placeholders_are_valid(self):
        (self.root / "examples/source.md").write_text(
            "[帮助](https://example.invalid/help)\n`<工作区>/.workbuddy/skills/`\n`%USERPROFILE%/.workbuddy/skills/`\n", encoding="utf-8")
        check_skill(self.root)

    def test_executable_file_and_shebang_are_rejected(self):
        file = self.root / "run.ps1"
        file.write_text("Write-Output test\n", encoding="utf-8")
        with self.assertRaisesRegex(SkillError, "executable file"):
            check_skill(self.root)
        file.unlink()
        (self.root / "examples/source.md").write_text("#!/bin/sh\necho test\n", encoding="utf-8")
        with self.assertRaisesRegex(SkillError, "executable content"):
            check_skill(self.root)

    @unittest.skipIf(os.name == "nt", "Windows does not use Unix executable permission bits")
    def test_executable_permission_is_rejected(self):
        (self.root / "examples/source.md").chmod(0o755)
        with self.assertRaisesRegex(SkillError, "executable file"):
            check_skill(self.root)

    def test_invalid_encoding_binary_and_credential_are_rejected(self):
        for content, message in [(b"\xff", "UTF-8"), (b"abc\x00def", "binary"), (b"ghp_" + b"X" * 36, "credential")]:
            with self.subTest(message=message):
                (self.root / "examples/source.md").write_bytes(content)
                with self.assertRaisesRegex(SkillError, message) as result:
                    check_skill(self.root)
                self.assertNotIn("X" * 36, str(result.exception))

    @unittest.skipIf(os.name == "nt", "Windows cannot create these nonportable source names; ZIP path checks still run")
    def test_case_collision_and_nonportable_filename_are_rejected(self):
        file = self.root / "examples/SOURCE.md"
        file.write_text("different", encoding="utf-8")
        with self.assertRaisesRegex(SkillError, "duplicate"):
            check_skill(self.root)
        file.unlink()
        file = self.root / "examples/nonportable..txt."
        file.write_text("text", encoding="utf-8")
        with self.assertRaisesRegex(SkillError, "unsafe package path"):
            check_skill(self.root)

    def test_source_symlink_is_rejected(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("keep", encoding="utf-8")
        link = self.root / "examples/linked.md"
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        with self.assertRaisesRegex(SkillError, "link or reparse"):
            check_skill(self.root)
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep")

    def test_linked_ancestor_is_rejected(self):
        link = self.root.parent / "linked-parent"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"directory symlink unavailable: {error}")
        with self.assertRaisesRegex(SkillError, "link or reparse"):
            check_skill(link / "examples")

    @unittest.skipUnless(os.name == "nt", "Windows junction check")
    def test_windows_junction_is_rejected(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep", encoding="utf-8")
        link = self.root / "examples/junction"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
        if result.returncode:
            self.skipTest("junction creation unavailable")
        try:
            with self.assertRaisesRegex(SkillError, "link or reparse"):
                check_skill(self.root)
        finally:
            os.rmdir(link)
        self.assertEqual((outside / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_oversized_source_is_rejected(self):
        (self.root / "large.txt").write_bytes(b"x" * (MAX_FILE_BYTES + 1))
        with self.assertRaisesRegex(SkillError, "size limit"):
            check_skill(self.root)

    def test_build_uses_stable_paths_bytes_permissions_and_lf(self):
        original = GOOD_SKILL.replace("\n", "\r\n").encode("utf-8")
        (self.root / "SKILL.md").write_bytes(original)
        archive, manifest = build_package(self.root, self.root.parent / "dist")
        with zipfile.ZipFile(archive) as handle:
            self.assertEqual(handle.namelist(), ["gift-development-service/SKILL.md", "gift-development-service/examples/source.md"])
            self.assertEqual(handle.read("gift-development-service/SKILL.md"), GOOD_SKILL.encode("utf-8"))
            for info in handle.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.external_attr >> 16, stat.S_IFREG | 0o644)
        self.assertEqual((self.root / "SKILL.md").read_bytes(), original)
        self.assertEqual(verify_package(archive, manifest), check_skill(self.root))
        record = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(record["archive"]["sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
        self.assertEqual(len(record["files"]), 2)

    def test_build_is_byte_reproducible_after_mtime_changes(self):
        first_zip, first_manifest = build_package(self.root, self.root.parent / "first")
        os.utime(self.root / "SKILL.md", (1234567890, 1234567890))
        second_zip, second_manifest = build_package(self.root, self.root.parent / "second")
        self.assertEqual(first_zip.read_bytes(), second_zip.read_bytes())
        self.assertEqual(first_manifest.read_bytes(), second_manifest.read_bytes())

    def test_invalid_rebuild_preserves_previous_verified_artifacts(self):
        archive, manifest = build_package(self.root, self.root.parent / "dist")
        old_zip, old_manifest = archive.read_bytes(), manifest.read_bytes()
        (self.root / "examples/source.md").unlink()
        with self.assertRaises(SkillError):
            build_package(self.root, self.root.parent / "dist")
        self.assertEqual(archive.read_bytes(), old_zip)
        self.assertEqual(manifest.read_bytes(), old_manifest)

    def test_build_cannot_contaminate_source(self):
        for output in (self.root, self.root / "dist"):
            with self.subTest(output=output), self.assertRaisesRegex(SkillError, "outside the source"):
                build_package(self.root, output)

    def test_dot_parent_source_cannot_hide_output_inside_source(self):
        source = self.root / ".." / self.root.name
        with self.assertRaisesRegex(SkillError, "outside the source"):
            build_package(source, self.root / "dist")
        self.assertFalse((self.root / "dist").exists())

    def unsafe_archive(self, paths, *, data=b"text\n", mode=stat.S_IFREG | 0o644):
        archive = self.root.parent / "untrusted.zip"
        manifest = self.root.parent / "untrusted.manifest.json"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(archive, "w") as handle:
                for path in paths:
                    info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
                    info.external_attr = mode << 16
                    handle.writestr(info, data)
        manifest.write_text(json.dumps({"schema_version": 1, "root": "gift-development-service", "files": []}), encoding="utf-8")
        return archive, manifest

    def test_zip_paths_and_duplicates_are_rejected_before_reading_content(self):
        for paths in (["../escape.md"], ["/absolute.md"], ["C:/absolute.md"], ["gift-development-service/../escape.md"], ["gift-development-service/a.md"] * 2, ["gift-development-service/A.md", "gift-development-service/a.md"], ["gift-development-service/trailing.txt."]):
            with self.subTest(paths=paths):
                archive, manifest = self.unsafe_archive(paths)
                with mock.patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("must not read members")):
                    with self.assertRaisesRegex(SkillError, "path|duplicate"):
                        verify_package(archive, manifest)
        self.assertFalse((self.root.parent / "escape.md").exists())

    def test_file_parent_paths_are_rejected_by_source_and_archive_contracts(self):
        cases = [("a.md", "a.md/child.md"), ("A.md", "a.md/child.md"),
                 ("docs/a.md", "DOCS/A.MD/deep/child.md")]
        for parent, child in cases:
            files = dict(check_skill(self.root).files)
            files.update({parent: b"parent\n", child: b"child\n"})
            with self.subTest(parent=parent, child=child):
                with self.assertRaisesRegex(SkillError, "file/directory.*path conflict"):
                    _checked_files(self.root.name, files)
            for reverse in (False, True):
                with self.subTest(parent=parent, child=child, reverse=reverse):
                    archive, manifest = self.unsafe_archive([])
                    entries = []
                    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as handle:
                        for name, data in sorted(files.items(), reverse=reverse):
                            path = f"{self.root.name}/{name}"
                            info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
                            info.create_system = 3
                            info.external_attr = (stat.S_IFREG | 0o644) << 16
                            handle.writestr(info, data)
                            entries.append({"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
                    manifest.write_text(json.dumps({
                        "schema_version": 1, "root": self.root.name, "files": entries,
                        "archive": {"name": archive.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()},
                    }), encoding="utf-8")
                    with mock.patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("must not read members")):
                        with self.assertRaisesRegex(SkillError, "file/directory.*path conflict"):
                            verify_package(archive, manifest)

    def test_shared_directories_and_filename_prefixes_are_valid(self):
        for name in ("a.md", "a.md2/child.md", "shared/one.md", "shared/two.md"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("text\n", encoding="utf-8")
        archive, manifest = build_package(self.root, self.root.parent / "dist")
        self.assertEqual(verify_package(archive, manifest), check_skill(self.root))

    def test_zip_size_and_links_are_rejected_before_reading_content(self):
        for data, mode, message in [(b"x" * (MAX_FILE_BYTES + 1), stat.S_IFREG | 0o644, "size limit"), (b"../target", stat.S_IFLNK | 0o777, "link")]:
            with self.subTest(message=message):
                archive, manifest = self.unsafe_archive(["gift-development-service/a.md"], data=data, mode=mode)
                with mock.patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("must not read members")):
                    with self.assertRaisesRegex(SkillError, message):
                        verify_package(archive, manifest)

    def test_zip_nul_filename_is_rejected_before_manifest_comparison(self):
        archive, manifest = self.unsafe_archive(["gift-development-service/aX.md"])
        archive.write_bytes(archive.read_bytes().replace(b"aX.md", b"a\x00.md"))
        with self.assertRaisesRegex(SkillError, "unsafe package path"):
            verify_package(archive, manifest)

    def test_manifest_file_list_and_hashes_are_checked(self):
        archive, manifest = build_package(self.root, self.root.parent / "dist")
        original = manifest.read_text(encoding="utf-8")
        for change, message in [(lambda r: r["files"].pop(), "file list"), (lambda r: r["archive"].update(sha256="0" * 64), "archive SHA"), (lambda r: r["files"][0].update(sha256="0" * 64), "file bytes")]:
            with self.subTest(message=message):
                record = json.loads(original)
                change(record)
                manifest.write_text(json.dumps(record), encoding="utf-8")
                with self.assertRaisesRegex(SkillError, message):
                    verify_package(archive, manifest)

    def test_cli_checks_and_builds_only_selected_source(self):
        result = main(["--skill", str(self.root), "--build", "--output", str(self.root.parent / "dist")])
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
